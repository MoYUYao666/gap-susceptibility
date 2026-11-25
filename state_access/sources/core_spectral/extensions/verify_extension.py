"""Fail-closed extension artifact verifier, not scientific or causal acceptance.

Checks complete records, semantic state, references and spectral weight algebra.
Does not recompute pretrained CLIP inference, gradients, optimizer trajectories or
reference spectra from images; a dishonest fully regenerated receipt is not proof.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import torch

if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from extensions import runner as r
else:
    from . import runner as r

require=r.require


def expected_trainables(identity):
    result={}
    for tower,layout in identity['model_layout'].items():
        require(tower in ('text','vision') and layout['layers']==12 and layout['heads']>=1
                and layout['width']%layout['heads']==0,'Invalid CLIP architecture layout')
        for layer in range(12):
            for projection in ('q_proj','k_proj','v_proj'):
                prefix=f'clip.{tower}_model.encoder.layers.{layer}.self_attn.{projection}'
                result[prefix+'.lora_A']={'shape':[8,layout['width']],'dtype':'torch.float32'}
                result[prefix+'.lora_B']={'shape':[layout['width'],8],'dtype':'torch.float32'}
    require(set(identity['model_layout'])=={'text','vision'},'Both tower layouts required')
    for tower,layout in identity['model_layout'].items():
        for layer in r.HookController.PRESETS[identity['cell']['preset']]:
            result[f'spectral_gates.{tower}_{layer}.alpha']={'shape':[layout['heads']],'dtype':'torch.float32'}
            result[f'spectral_gates.{tower}_{layer}.beta']={'shape':[],'dtype':'torch.float32'}
    return result


def validate_references(artifact,buffers,identity,lock):
    require(set(artifact)=={'schema_version','payload','provenance'} and artifact['schema_version']==1,
            'Reference artifact schema mismatch')
    payload=artifact['payload']; provenance=artifact['provenance']
    require(set(payload)=={'schema_version','configuration','references','calibration_counts'}
            and payload['schema_version']==1,'Reference payload schema mismatch')
    cfg=payload['configuration']; cell=identity['cell']
    raw_eos,actual_eos=identity['model_eos_token_id'],identity['text_eos_token_id']
    require((identity['eos_policy']=='exact_model_tokenizer_eos' and raw_eos==actual_eos) or
            (identity['eos_policy']=='legacy_config2_highest_token_eos' and raw_eos==2
             and actual_eos==identity['text_vocab_size']-1), 'Invalid explicit model/tokenizer EOS policy')
    layers=list(r.HookController.PRESETS[cell['preset']])
    gates={f'{tower}_{layer}':dict(tower=tower,layer=layer,width=layout['width'],heads=layout['heads'],
             head_dim=layout['width']//layout['heads'],reference_dtype='torch.float32')
           for tower,layout in identity['model_layout'].items() for layer in layers}
    expected_cfg=dict(controller_version=1,spectral_version=1,preset=cell['preset'],layers=layers,
        mode=cell['gate_mode'],towers=['text','vision'],text_eos_token_id=identity['text_eos_token_id'],
        text_mask='boolean nonempty valid prefix through first EOS',vision_mask='all tokens valid, including CLS',
        gates=gates,spectral=dict(input_layout='B,H,T,D',axis='valid-prefix token axis',
            power_reduction='sum feature dimension',one_sided_multiplicity='DC=1, even Nyquist=1, others=2',
            high_band_cycles_per_token=.25,entropy_normalization='log(floor(valid_length/2)+1)',zero_energy_feature=0.),
        gate=dict(formula='1+alpha+tanh(beta)*(f-0.5)',alpha='per-head',beta='per-layer scalar',
                  dynamic_f='current per-example E*entropy',frozen_reference_f='locked per-head calibration mean'))
    require(cfg==expected_cfg,'Reference mode/layer/head/policy configuration mismatch')
    require(set(payload['references'])==set(gates)==set(payload['calibration_counts'])==set(buffers),'Reference gate coverage mismatch')
    data=lock['datasets'][cell['dataset']]
    rows=[{k:row[k] for k in ('id','path','sha256','pixel_sha256')} for row in data['splits']['calibration']]
    texts=r.core_records.view_specs(lock,cell['dataset'])['calibration']['texts']
    require(provenance['images']==rows and provenance['texts']==texts,'Reference calibration identities/prompts mismatch')
    require(provenance['source_split']=='calibration' and provenance['model_path_kind']=='native_frozen_ungated'
            and provenance['labels_accessed'] is False,'Reference collection policy mismatch')
    require(provenance['image_presentations']==len(rows) and provenance['prompt_presentations']==len(texts),
            'Calibration must present images and prompts once independently')
    ids=torch.tensor(provenance['input_ids']); mask=torch.tensor(provenance['attention_mask'])
    require(ids.ndim==2 and ids.shape==mask.shape and ids.shape[0]==len(texts)
            and mask.dtype==torch.bool and ids.dtype==torch.int64,'Calibration token/mask schema mismatch')
    r.HookController._check_mask(mask)
    lengths=mask.sum(-1)
    require(torch.equal(ids.gather(1,(lengths-1)[:,None]).squeeze(1),torch.full((len(texts),),identity['text_eos_token_id']))
            and (((ids==identity['text_eos_token_id'])&mask).sum(-1)==1).all().item(),'Calibration masks do not end at unique valid EOS')
    for key,layout in gates.items():
        values=payload['references'][key]
        require(isinstance(values,list) and len(values)==layout['heads'] and all(type(x) in (int,float)
                and math.isfinite(x) and 0<=x<=1 for x in values),'Invalid reference means')
        expected={'_reference':torch.tensor(values,dtype=torch.float32),'_reference_ready':torch.tensor(True)}
        require(r._buffers_equal({key:buffers[key]},{key:expected}),'Reference buffers differ from JSON values')
        count=len(texts) if layout['tower']=='text' else len(rows)
        require(type(payload['calibration_counts'][key]) is int and payload['calibration_counts'][key]==count,
                'Calibration counts differ from one presentation per image/prompt')


def validate_checkpoint(cp,identity,epoch,step,artifact,buffers,protocol):
    require(cp['identity']==identity and cp['epoch']==epoch and cp['global_step']==step,'Checkpoint identity/epoch/step mismatch')
    expected=expected_trainables(identity)
    require(cp['trainable_manifest']==identity['trainable_manifest']==expected,'Incomplete trainable shape/dtype manifest')
    require(set(cp['trainable'])==set(expected),'Missing/extra checkpoint trainables')
    require(list(cp['trainable'])==identity['optimizer_parameter_names'],'Checkpoint parameter order mismatch')
    for key,value in cp['trainable'].items():
        require(torch.is_tensor(value) and list(value.shape)==expected[key]['shape'] and value.dtype==torch.float32
                and torch.isfinite(value).all().item(),'Invalid trainable tensor shape/dtype/value')
        if epoch==0 and (key.endswith('lora_B') or key.startswith('spectral_gates.')):
            require(torch.count_nonzero(value).item()==0,'Initial LoRA/gates violate exact identity initialization')
    extra=cp['extension']
    require(set(extra)=={'schema_version','reference_sha256','payload','buffers','optimizer_parameter_names'}
            and extra['schema_version']==1 and extra['reference_sha256']==identity['reference_sha256'], 'Incomplete extension checkpoint identity')
    require(extra['payload']==artifact['payload'] and r._buffers_equal(extra['buffers'],buffers), 'Checkpoint locked references drifted')
    require(extra['optimizer_parameter_names']==identity['optimizer_parameter_names'],'Checkpoint optimizer membership drift')
    group,=cp['optimizer']['param_groups']
    require(group['lr']==.0005 and group['weight_decay']==.01 and tuple(group['betas'])==(.9,.999)
            and group['eps']==1e-8 and group.get('foreach') is False and group.get('fused') is False,'AdamW recipe mismatch')
    require(all(group.get(flag) is False for flag in ('amsgrad','maximize','capturable','differentiable'))
            and group.get('decoupled_weight_decay',True) is True and group['initial_lr']==.0005,
            'AdamW semantic flags or initial rate mismatch')
    require(cp['scheduler']['last_epoch']==step and cp['scheduler']['_last_lr']==[.0005]
            and cp['scheduler']['base_lrs']==[.0005] and cp['scheduler']['lr_lambdas']==[None]
            and cp['scheduler']['_step_count']==step+1,'Constant scheduler position/base-rate mismatch')
    r.core_verifier.validate_training_state(cp,identity,step)


def validate_diagnostics(diagnostics,gate_state,cp,identity,views,native):
    require(set(diagnostics)==set(views),'Diagnostics view inventory mismatch')
    refs=cp['extension']['payload']['references']
    require(set(gate_state)==set(refs),'GateState key inventory mismatch')
    for key,values in gate_state.items():
        prefix='spectral_gates.'+key+'.'
        require(values==dict(alpha=cp['trainable'][prefix+'alpha'].tolist(),beta=cp['trainable'][prefix+'beta'].item(),
                            reference=refs[key],mode=identity['cell']['gate_mode']), 'GateState differs from checkpoint')
    for view,records in diagnostics.items():
        if native:
            require(records=={},'Native bypass must not record active gate diagnostics')
            continue
        require(set(records)==set(refs),'Missing gate diagnostics')
        for key,batches in records.items():
            require(isinstance(batches,list) and len(batches)>0,'Missing gate diagnostic batches')
            count=0; heads=len(refs[key]); reference=torch.tensor(refs[key],dtype=torch.float32)
            prefix='spectral_gates.'+key+'.'
            for batch in batches:
                require(set(batch)=={'energy_ratio','entropy','observed_feature','feature','weights','reference','valid_lengths'},'Diagnostic schema mismatch')
                lengths=batch['valid_lengths']; n=lengths.numel(); count+=n
                require(lengths.ndim==1 and lengths.dtype==torch.int64 and (lengths>=1).all().item(),'Invalid diagnostic valid lengths')
                require(torch.equal(batch['reference'],reference),'Diagnostic reference mismatch')
                for name in ('energy_ratio','entropy','observed_feature','feature','weights'):
                    value=batch[name]
                    require(value.dtype==torch.float32 and tuple(value.shape)==(n,heads)
                            and torch.isfinite(value).all().item(),'Invalid diagnostic shape/dtype/value')
                    if name!='weights': require(((value>=0)&(value<=1)).all().item(),'Diagnostic feature outside [0,1]')
                require(torch.allclose(batch['observed_feature'],batch['energy_ratio']*batch['entropy'],atol=1e-7,rtol=0),'Diagnostic E*entropy mismatch')
                feature=batch['observed_feature'] if identity['cell']['gate_mode']=='dynamic' else reference.expand(n,-1)
                require(torch.equal(batch['feature'],feature),'Static/dynamic feature semantics mismatch')
                expected=1+cp['trainable'][prefix+'alpha']+cp['trainable'][prefix+'beta'].tanh()*(feature-.5)
                require(torch.allclose(batch['weights'],expected,rtol=1e-6,atol=2e-7),'Effective scalar does not match gate formula')
            expected_count=len(views[view]['texts']) if key.startswith('text') else len(views[view]['rows'])
            require(count==expected_count,'Diagnostic coverage differs from full candidate/row inventory')


def verify_unit(directory,lock,protocol,technical=False,lock_hash=None,protocol_hash=None,extension_hash=None):
    directory=Path(directory)
    identity=json.loads((directory/'Identity.json').read_text(encoding='utf-8'))
    cell=next((c for c in r.units() if c['id']==directory.name),None)
    require(cell is not None and identity['unit']==directory.name,'Unknown extension unit')
    require(identity['cell']=={k:cell[k] for k in ('dataset','preset','gate_mode','seed')},'Cell factor identity mismatch')
    require(type(technical) is bool and identity['technical'] is technical,'Scientific/technical firewall mismatch')
    require(identity['core_protocol_sha256']==(protocol_hash or r.CORE_PROTOCOL_HASH),'Core protocol hash mismatch')
    require(identity['datalock_sha256']==(lock_hash or r.read_document(lock)[1]),'DataLock hash mismatch')
    require(identity['extension_protocol_sha256']==(extension_hash or r.read_document(r.HERE/'ExtensionProtocol.json')[1]),'Extension protocol hash mismatch')
    require(identity['producer_sha256']==r.producer_hashes(),'Extension producer code mismatch')
    require(identity['model_files']==lock['model']['files'],'Frozen base file identity mismatch')
    require(identity['environment']['precision']=='float32','Unexpected numerical precision')
    inputs=json.loads((directory/'Inputs.json').read_text(encoding='utf-8'))
    require(inputs['protocol']==protocol and inputs['datalock']==lock,'Saved input snapshot differs')
    r.validate_extension(inputs['extension_protocol'],identity['core_protocol_sha256'])
    require(r.digest_file(directory/'References.json')==identity['reference_sha256']
            and r.digest_file(directory/'ReferenceBuffers.pt')==identity['reference_buffers_sha256'],'Reference artifact hash mismatch')
    artifact=json.loads((directory/'References.json').read_text(encoding='utf-8'))
    buffers=torch.load(directory/'ReferenceBuffers.pt',weights_only=True,map_location='cpu')
    validate_references(artifact,buffers,identity,lock)
    last=1 if identity['smoke'] else 4
    require(not identity['smoke'] or technical,'Smoke cannot be a scientific run')
    names=['frozen_baseline']+[f'epoch_{i:03}' for i in range(last+1)]
    require({p.name for p in directory.iterdir() if p.is_dir()}==set(names),'Missing/extra/uncommitted saved states')
    require(not (directory/'RUNNING.json').exists(),'Unit still running or unrecovered owner lock')
    views=r.core_records.view_specs(lock,cell['dataset'])
    train=lock['datasets'][cell['dataset']]['splits']['train']
    if identity['smoke']:
        train=train[:16]; views={k:dict(v,rows=v['rows'][:16]) for k,v in views.items()}
    per_epoch=2 if identity['smoke'] else math.ceil(len(train)/protocol['batch_size'])
    baseline={}
    for name in names:
        path=directory/name; epoch=0 if name=='frozen_baseline' else int(name[6:]); step=epoch*per_epoch
        receipt=r.core_state.verify_directory(path)
        require(receipt['identity']==identity and receipt['epoch']==epoch and receipt['global_step']==step,'Saved state identity/position mismatch')
        require(receipt['scientific_result'] is (not technical),'Scientific flag drift')
        require(receipt['views']==list(views),'Score view order mismatch')
        expected_files={'checkpoint.pt','GateState.json','GateDiagnostics.pt'}|{f'{v}.{ext}' for v in views for ext in ('json','npz')}
        require(set(receipt['files'])==expected_files,'Saved state file inventory mismatch')
        cp=r.core_state.load_checkpoint(path)
        validate_checkpoint(cp,identity,epoch,step,artifact,buffers,protocol)
        require(receipt['trainable_manifest']==identity['trainable_manifest'] and
                receipt['trainable_count']==sum(x.numel() for x in cp['trainable'].values()),'Receipt trainable count/manifest mismatch')
        diagnostics=torch.load(path/'GateDiagnostics.pt',weights_only=True,map_location='cpu')
        gate_state=json.loads((path/'GateState.json').read_text(encoding='utf-8'))
        validate_diagnostics(diagnostics,gate_state,cp,identity,views,name=='frozen_baseline')
        if epoch:
            training=receipt['training']
            require(training['steps']==per_epoch and len(training['losses'])==per_epoch
                    and all(math.isfinite(v) for v in training['losses']),'Training step/loss record mismatch')
            require(sorted(training['order'])==list(range(len(train))),'Training order does not cover exact source rows')
            require(training['learning_rate']==.0005,'Recorded training rate mismatch')
        else:
            require(receipt['training'] is None,'Native/initial state claims optimization')
        for view_name,view in views.items():
            meta=json.loads((path/f'{view_name}.json').read_text(encoding='utf-8'))
            require(meta['row_ids']==[row['id'] for row in view['rows']] and
                    meta['row_sha256']==[row['sha256'] for row in view['rows']] and
                    meta['row_pixel_sha256']==[row['pixel_sha256'] for row in view['rows']], 'Score row identity/order mismatch')
            require(meta['texts']==meta['effective_texts']==view['texts'] and meta['candidate_ids']==list(range(len(view['texts']))),'Full candidate mapping mismatch')
            require(meta['labels_accessed'] is False and meta['score_kind']=='normalized_cosine_float32_unscaled','Score semantics mismatch')
            with np.load(path/f'{view_name}.npz',allow_pickle=False) as arrays:
                require(set(arrays.files)=={'scores','image_features','text_features'},'Score archive inventory mismatch')
                scores,images,texts=(arrays[k] for k in ('scores','image_features','text_features'))
                require(all(a.dtype==np.float32 and np.isfinite(a).all() for a in (scores,images,texts)),'Invalid score/features dtype/value')
                require(scores.shape==(len(view['rows']),len(view['texts'])) and meta['shape']==list(scores.shape),'Full score matrix shape mismatch')
                require(images.ndim==texts.ndim==2 and images.shape[0]==scores.shape[0] and texts.shape[0]==scores.shape[1]
                        and images.shape[1]==texts.shape[1],'Feature shape mismatch')
                require(np.allclose(np.linalg.norm(images,axis=1),1,atol=2e-6) and np.allclose(np.linalg.norm(texts,axis=1),1,atol=2e-6),'Features not unit normalized')
                require(np.allclose(scores,images@texts.T,rtol=0,atol=2e-6),'Scores do not reconstruct from full features')
                if name=='frozen_baseline': baseline[view_name]=scores.copy()
                if name=='epoch_000': require(np.array_equal(scores,baseline[view_name]),'Native versus epoch-zero identity null failed')
    run=json.loads((directory/'RunReceipt.json').read_text(encoding='utf-8'))
    require(run['identity']==identity and run['epoch']==last and run['global_step']==last*per_epoch,'Final run identity/step mismatch')
    require(run['status']==('TECHNICAL_COMPLETE' if technical else 'EXTENSION_COMPLETE') and run['scientific_result'] is (not technical),'Incomplete or misclassified run')
    require(run['epoch_receipt_sha256']==r.digest_file(directory/f'epoch_{last:03}'/'Receipt.json'),'Final receipt binding mismatch')
    return dict(unit=cell['id'],states=len(names),trained_epochs=last,scientific_result=not technical,
                reference_sha256=identity['reference_sha256'],run_receipt_sha256=r.digest_file(directory/'RunReceipt.json'))


def verify_campaign(output,datalock,protocol,extension_protocol,root,technical=False):
    cfg=dict(root=str(root),protocol=protocol,extension_protocol=extension_protocol,output_dir=str(output),technical=technical)
    plan=r.make_plan(cfg,datalock)
    lock,lock_hash=r.read_document(datalock); recipe,protocol_hash=r.read_document(protocol)
    output=Path(output)
    require({p.name for p in output.iterdir() if p.is_dir()}=={c['id'] for c in r.units()},'Campaign requires exactly the fixed 24 complete units')
    records=[verify_unit(output/c['id'],lock,recipe,technical,lock_hash,protocol_hash,plan['extension_protocol_sha256']) for c in r.units()]
    return dict(status='PASS_EXTENSION_RECORDS_ONLY',scientific_result=not technical,units=records,
                trajectories=24,saved_states=sum(row['states'] for row in records),
                limitation='Artifact/state validation is not inference replay, statistical analysis, causal identification, retrieval completion or launch approval.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--datalock',required=True)
    parser.add_argument('--protocol',default=str(r.ROOT/'Protocol.json'))
    parser.add_argument('--extension-protocol',default=str(r.HERE/'ExtensionProtocol.json'))
    parser.add_argument('--root',required=True)
    parser.add_argument('--technical',action='store_true')
    parser.add_argument('--unit',help='Verify one completed unit instead of all 24')
    args=parser.parse_args(); torch.set_num_threads(1)
    if args.unit:
        cfg=dict(root=args.root,protocol=args.protocol,extension_protocol=args.extension_protocol,
                 output_dir=args.output,technical=args.technical)
        plan=r.make_plan(cfg,args.datalock)
        lock,lh=r.read_document(args.datalock); protocol,ph=r.read_document(args.protocol)
        report=verify_unit(Path(args.output)/args.unit,lock,protocol,args.technical,lh,ph,plan['extension_protocol_sha256'])
    else:
        report=verify_campaign(args.output,args.datalock,args.protocol,args.extension_protocol,args.root,args.technical)
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
