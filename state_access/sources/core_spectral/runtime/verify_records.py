"""Fail-closed replacement-state/score validation; no inference or selection."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch

from records import digest_file,read_document,validate_inputs,view_specs
from state import atomic_json,load_checkpoint,verify_directory,rng_state,restore_rng
from trainer import producer_hashes,units


def require(condition,message):
    if not condition: raise ValueError(message)


def expected_trainables(mode):
    towers = ['text_model'] + (['vision_model'] if mode=='lora_both' else [])
    return {f'clip.{tower}.encoder.layers.{layer}.self_attn.{projection}.lora_{factor}'
            for tower in towers for layer in range(12)
            for projection in ('q_proj','k_proj','v_proj') for factor in ('A','B')}


def validate_training_state(checkpoint,identity,expected_step):
    """Check semantic recovery state, not only a self-consistent file digest."""
    group,=checkpoint['optimizer']['param_groups']
    identifiers=group['params']
    moments=checkpoint['optimizer']['state']
    require(identifiers==list(range(len(checkpoint['trainable']))),'Optimizer parameter identity/order mismatch')
    require(set(moments)==(set(identifiers) if expected_step else set()),'Missing/extra AdamW moment states')
    for identifier,value in zip(identifiers,checkpoint['trainable'].values()):
        if not expected_step: continue
        entry=moments[identifier]
        require(set(entry)=={'step','exp_avg','exp_avg_sq'},'Unexpected AdamW moment fields')
        step=entry['step']
        require(torch.is_tensor(step) and step.ndim==0 and torch.isfinite(step).item()
                and step.item()==expected_step,'AdamW step differs from epoch boundary')
        for field in ('exp_avg','exp_avg_sq'):
            moment=entry[field]
            require(torch.is_tensor(moment) and moment.dtype==value.dtype and moment.shape==value.shape
                    and torch.isfinite(moment).all().item(),'Invalid AdamW moment shape/dtype/value')
        require((entry['exp_avg_sq']>=0).all().item(),'Negative AdamW second moment')
    saved=checkpoint['rng']
    require(set(saved)=={'python','numpy','torch_cpu','torch_cuda'},'Incomplete RNG schema')
    np_state=saved['numpy']
    require(set(np_state)=={'algorithm','keys','position','has_gauss','cached'},'Incomplete numpy RNG schema')
    require(np_state['algorithm']=='MT19937' and torch.is_tensor(np_state['keys'])
            and np_state['keys'].dtype==torch.int64 and tuple(np_state['keys'].shape)==(624,),
            'Invalid numpy generator identity/keys')
    require(isinstance(np_state['position'],int) and 0<=np_state['position']<=624
            and np_state['has_gauss'] in (0,1) and math.isfinite(np_state['cached']),
            'Invalid numpy generator position/cache')
    cpu=saved['torch_cpu']
    require(torch.is_tensor(cpu) and cpu.dtype==torch.uint8 and cpu.ndim==1 and cpu.numel()>0,'Invalid Torch CPU RNG state')
    cuda=saved['torch_cuda']
    environment=identity['environment']
    expected_devices=environment.get('device_count',0) if environment['device'].startswith('cuda') else 0
    require(isinstance(cuda,list) and len(cuda)==expected_devices,'CUDA RNG device inventory mismatch')
    require(all(torch.is_tensor(v) and v.dtype==torch.uint8 and v.ndim==1 and v.numel()>0 for v in cuda),'Invalid CUDA RNG byte state')
    # Validate CPU restorability without touching any CUDA context or retaining RNG changes.
    previous=rng_state(torch.device('cpu'))
    try:
        restore_rng(saved,torch.device('cpu'))
    except (KeyError,TypeError,ValueError,RuntimeError) as error:
        raise ValueError('RNG state cannot restore CPU/Python/NumPy generators') from error
    finally:
        restore_rng(previous,torch.device('cpu'))


def verify_unit(directory,lock,protocol,technical=False,lock_hash=None,protocol_hash=None):
    directory = Path(directory)
    identity = json.loads((directory/'Identity.json').read_text(encoding='utf-8'))
    cell = next((row for row in units(protocol,lock) if row['id']==directory.name),None)
    require(cell is not None,'Unknown unit identity')
    require(identity['unit']==directory.name,'Unit path/identity mismatch')
    require(identity['smoke'] is technical,'Scientific/technical firewall mismatch')
    require(identity['protocol_sha256']==(protocol_hash or read_document(protocol)[1]),'Protocol hash mismatch')
    require(identity['datalock_sha256']==(lock_hash or read_document(lock)[1]),'DataLock hash mismatch')
    require(identity['model_files']==lock['model']['files'],'Frozen base identity mismatch')
    require(identity['producer_sha256']==producer_hashes(),'Runtime producer mismatch')
    require(identity['environment']['precision']=='float32','Unexpected precision')
    require(set(identity['trainable_manifest'])==expected_trainables(cell['mode']),'Incomplete trainable topology')
    last = 1 if technical else protocol['epochs']
    names = ['frozen_baseline']+[f'epoch_{epoch:03}' for epoch in range(last+1)]
    actual = {p.name for p in directory.iterdir() if p.is_dir()}
    require(actual==set(names),'Missing, extra or uncommitted epoch directory')
    require(not (directory/'RUNNING.json').exists(),'Unit still running or stale owner not recovered')
    views = view_specs(lock,cell['dataset'])
    if technical: views={name:dict(view,rows=view['rows'][:16]) for name,view in views.items()}
    train_rows = lock['datasets'][cell['dataset']]['splits']['train']
    ntrain = min(16,len(train_rows)) if technical else len(train_rows)
    steps_per_epoch = 2 if technical else math.ceil(ntrain/protocol['batch_size'])
    baseline_arrays = {}
    for name in names:
        path = directory/name
        receipt = verify_directory(path)
        epoch = 0 if name=='frozen_baseline' else int(name[6:])
        require(receipt['identity']==identity,'Epoch identity drift')
        require(receipt['epoch']==epoch and receipt['global_step']==epoch*steps_per_epoch,'Epoch/global-step mismatch')
        require(receipt['scientific_result'] is (not technical),'Epoch scientific flag mismatch')
        require(receipt['views']==list(views),'View inventory/order mismatch')
        expected_files = {'checkpoint.pt'}|{f'{view}.{ext}' for view in views for ext in ('npz','json')}
        require(set(receipt['files'])==expected_files,'Epoch file inventory mismatch')
        checkpoint = load_checkpoint(path)
        require(checkpoint['identity']==identity and checkpoint['epoch']==epoch and checkpoint['global_step']==epoch*steps_per_epoch,'Checkpoint identity/epoch mismatch')
        require(checkpoint['trainable_manifest']==identity['trainable_manifest'],'Checkpoint manifest mismatch')
        require(set(checkpoint['trainable'])==expected_trainables(cell['mode']),'Missing checkpoint trainable')
        count = 0
        for key,value in checkpoint['trainable'].items():
            description = identity['trainable_manifest'][key]
            require(list(value.shape)==description['shape'] and str(value.dtype)==description['dtype'],'Trainable tensor shape/dtype mismatch')
            require(value.dtype==torch.float32 and torch.isfinite(value).all().item(),'Nonfinite or non-float32 trainable')
            require(value.ndim==2 and (value.shape[0] if key.endswith('_A') else value.shape[1])==8,'Wrong LoRA rank')
            count += value.numel()
            if epoch==0 and key.endswith('_B'):
                require(torch.count_nonzero(value).item()==0,'Initial adapter delta is not zero')
        require(receipt['trainable_count']==count,'Trainable count mismatch')
        group, = checkpoint['optimizer']['param_groups']
        require(len(group['params'])==len(checkpoint['trainable']),'Optimizer missing trainables')
        require(group['lr']==protocol['learning_rate_by_mode'][cell['mode']] and group['weight_decay']==.01,'Optimizer recipe mismatch')
        require(tuple(group['betas'])==(.9,.999) and group['eps']==1e-8,'Optimizer defaults drift')
        require(checkpoint['scheduler']['last_epoch']==epoch*steps_per_epoch,'Scheduler step mismatch')
        validate_training_state(checkpoint,identity,epoch*steps_per_epoch)
        if epoch>0:
            training = receipt['training']
            require(training['steps']==steps_per_epoch and len(training['losses'])==steps_per_epoch,'Training loss/step count mismatch')
            require(all(math.isfinite(x) for x in training['losses']),'Nonfinite training loss')
            require(sorted(training['order'])==list(range(ntrain)),'Epoch permutation missing/duplicated samples')
            require(training['learning_rate']==group['lr'],'Recorded learning-rate mismatch')
        else: require(receipt['training'] is None,'Initial/native state claims training')
        for view_name,view in views.items():
            meta = json.loads((path/f'{view_name}.json').read_text(encoding='utf-8'))
            require(meta['row_ids']==[r['id'] for r in view['rows']],'Score row identity/order mismatch')
            require(meta['row_sha256']==[r['sha256'] for r in view['rows']],'Score encoded-image identity mismatch')
            require(meta['row_pixel_sha256']==[r['pixel_sha256'] for r in view['rows']],'Score pixel identity mismatch')
            require(meta['texts']==view['texts'] and meta['effective_texts']==view['texts'],'Candidate prompt mapping drift')
            require(meta['candidate_ids']==list(range(len(view['texts']))),'Candidate ID mapping mismatch')
            require(meta['labels_accessed'] is False and meta['score_kind']=='normalized_cosine_float32_unscaled','Score semantics mismatch')
            with np.load(path/f'{view_name}.npz',allow_pickle=False) as data:
                require(set(data.files)=={'scores','image_features','text_features'},'Score archive inventory mismatch')
                scores,images,texts = (data[k] for k in ('scores','image_features','text_features'))
                require(scores.dtype==images.dtype==texts.dtype==np.float32,'Score dtype mismatch')
                require(scores.shape==(len(view['rows']),len(view['texts'])) and meta['shape']==list(scores.shape),'Score shape mismatch')
                require(images.ndim==2 and texts.ndim==2 and images.shape[1]==texts.shape[1],'Feature shape mismatch')
                require(images.shape[0]==len(view['rows']) and texts.shape[0]==len(view['texts']),'Feature row mismatch')
                require(all(np.isfinite(x).all() for x in (scores,images,texts)),'Nonfinite score/features')
                require(np.allclose(np.linalg.norm(images,axis=1),1,atol=2e-6) and np.allclose(np.linalg.norm(texts,axis=1),1,atol=2e-6),'Unnormalized/zero features')
                require(np.allclose(scores,images@texts.T,rtol=0,atol=2e-6),'Scores do not reconstruct from features')
                if name=='frozen_baseline': baseline_arrays[view_name]=scores.copy()
                if name=='epoch_000': require(np.array_equal(scores,baseline_arrays[view_name]),'Native/initial score null failure')
    run = json.loads((directory/'RunReceipt.json').read_text(encoding='utf-8'))
    require(run['identity']==identity and run['epoch']==last and run['global_step']==last*steps_per_epoch,'Final run receipt mismatch')
    require(run['status']==('TECHNICAL_SMOKE_ONLY' if technical else 'PROSPECTIVE_COMPLETE'),'Run not complete')
    require(run['epoch_receipt_sha256']==digest_file(directory/f'epoch_{last:03}'/'Receipt.json'),'Final epoch receipt not bound')
    return dict(unit=directory.name,states=len(names),trained_epochs=last,scientific_result=not technical,
                final_receipt_sha256=digest_file(directory/'RunReceipt.json'))


def verify_campaign(output,datalock,protocol,root=None):
    lock,lock_hash = read_document(datalock)
    config,protocol_hash = read_document(protocol)
    validate_inputs(dict(root=str(root or Path.cwd()),protocol=protocol,smoke=False),lock)
    output = Path(output)
    cells = units(config,lock)
    require(output.is_dir(),'Missing campaign output')
    require({p.name for p in output.iterdir() if p.is_dir()}=={c['id'] for c in cells},'Missing/extra scientific units')
    records=[verify_unit(output/cell['id'],lock,config,lock_hash=lock_hash,protocol_hash=protocol_hash) for cell in cells]
    return dict(status='PASS_REPLACEMENT_CORE_RECORDS_ONLY',scientific_result=True,
        training_trajectories=len(records),paired_source_seed_groups=len(lock['datasets'])*len(config['seeds']),
        paired_seeds_per_fixed_source=len(config['seeds']),trained_epoch_records=sum(x['trained_epochs'] for x in records),
        saved_states=sum(x['states'] for x in records),protocol_sha256=protocol_hash,datalock_sha256=lock_hash,
        verifier_sha256=digest_file(__file__),units=records,
        limitation='Record validation is not statistical analysis, reviewer acceptance, complete payload retrieval or submission approval.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--datalock',required=True)
    parser.add_argument('--protocol',required=True)
    parser.add_argument('--root',required=True)
    args=parser.parse_args()
    torch.set_num_threads(1)
    report=verify_campaign(args.output,args.datalock,args.protocol,args.root)
    atomic_json(Path(args.output)/'CoreRecordsVerification.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))
