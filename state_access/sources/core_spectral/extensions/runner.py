"""Independent, offline spectral CLIP extension runner; no core source changes.

The four trained arms are an explicit CLIP adaptation, not a DSW reproduction.
Scientific runs require one explicit cell. Technical and smoke outputs are fenced.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import types

os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

import numpy as np
import torch

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from extensions.hooks import HookController
else:
    from .hooks import HookController

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE_PROTOCOL_HASH = '719a783b14bd101eac7c411352598b818aca9dd063f2e78abb7b7558e26636e9'


def _load_core():
    """Resolve legacy absolute imports privately; restore the caller's modules.

    Core module globals keep their resolved dependencies. No sys.path mutation,
    disk rewriting or persistent shadowing of generic model/state names is used.
    Import this serially before worker creation, not concurrently with imports.
    """
    names = ('model', 'records', 'state', 'trainer', 'verify_records')
    saved = {name: sys.modules.get(name) for name in names}
    result = []
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location('_a1_extension_core_' + name, ROOT/'runtime'/f'{name}.py')
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            result.append(module)
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return result


core_model, core_records, core_state, core_trainer, core_verifier = _load_core()
digest_file = core_records.digest_file
read_document = core_records.read_document
_IMPORTED_HASHES = {f'runtime/{name}.py': digest_file(ROOT/'runtime'/f'{name}.py')
                    for name in ('model', 'records', 'state', 'trainer', 'verify_records')}
_IMPORTED_HASHES.update({f'extensions/{name}.py': digest_file(HERE/f'{name}.py')
                         for name in ('runner', 'hooks', 'spectral')})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def producer_hashes():
    current = {name: digest_file(ROOT/name) for name in _IMPORTED_HASHES}
    require(current == _IMPORTED_HASHES, 'Loaded producer source changed; restart and re-review')
    current['extensions/verify_extension.py'] = digest_file(HERE/'verify_extension.py')
    return current


def units():
    return [dict(id=f'{dataset}__{preset}__{mode}__s{seed}', dataset=dataset,
                 preset=preset, gate_mode=mode, seed=seed)
            for dataset in ('dtd', 'cifar100') for seed in (42,43,44)
            for preset in ('early','late') for mode in ('frozen_reference','dynamic')]


def validate_extension(extension, protocol_hash):
    expected = dict(schema_version=1, protocol_id='A1_SPECTRAL_EXTENSION_20261122_V1',
        core_protocol_sha256=CORE_PROTOCOL_HASH, datasets=['dtd','cifar100'], seeds=[42,43,44],
        presets=dict(early=[0,1,2],late=[9,10,11]),gate_modes=['frozen_reference','dynamic'],
        towers=['text','vision'],core_mode='lora_both',epochs=4,batch_size=32,
        learning_rate=.0005,weight_decay=.01,optimizer='AdamW',betas=[.9,.999],epsilon=1e-8,
        schedule='constant',precision='float32',tf32=False,lora_rank=8,
        lora_targets=['q_proj','k_proj','v_proj'],gate_formula='1+alpha+tanh(beta)*(f-0.5)',
        gate_initialization=dict(alpha=0,beta=0),
        calibration=dict(model='native_frozen_ungated',images='all locked source calibration images exactly once',
                         texts='all unique locked source candidate prompts exactly once',
                         labels_accessed=False,freeze_before_optimization=True),
        views=['calibration','test','imagenet','flickr'],
        states=['frozen_baseline']+[f'epoch_{i:03}' for i in range(5)],cells=units(),
        scientific_claim_boundary='Explicit CLIP adaptation; not faithful DSW reproduction, not equal effective capacity or causal identification.')
    require(extension == expected, 'Extension protocol differs from fixed 24-arm recipe')
    require(protocol_hash == CORE_PROTOCOL_HASH, 'Main protocol hash changed')


def make_plan(config, datalock):
    lock, lock_hash = read_document(datalock)
    protocol, protocol_hash = read_document(config['protocol'])
    # Dictionary protocols are accepted for tiny API fixtures only; still bind the
    # exact unchanged source file whose content must match the supplied dictionary.
    if isinstance(config['protocol'], dict):
        source, protocol_hash = read_document(ROOT/'Protocol.json')
        require(protocol == source, 'Core dictionary recipe differs from main protocol')
    extension, extension_hash = read_document(config.get('extension_protocol', HERE/'ExtensionProtocol.json'))
    validate_extension(extension, protocol_hash)
    technical = bool(config.get('technical', False) or config.get('smoke', False))
    _, model_path = core_records.validate_inputs(dict(config, smoke=technical), lock)
    require(lock.get('protocol_sha256', protocol_hash) == protocol_hash, 'DataLock binds a different core protocol')
    output = Path(config['output_dir']).resolve()
    if technical:
        output /= 'smoke' if config.get('smoke') else 'technical'
    return dict(status='VALIDATED_EXTENSION_PLAN_NO_MODEL_LOADED',core_protocol_sha256=protocol_hash,
        extension_protocol_sha256=extension_hash,datalock_sha256=lock_hash,model_path=str(model_path),
        model_files=lock['model']['files'],producer_sha256=producer_hashes(),technical=technical,
        smoke=bool(config.get('smoke',False)),scientific_result=False,
        units=[dict(cell,output=str(output/cell['id'])) for cell in units()])


def make_optimizer(model, protocol):
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
        lr=protocol['learning_rate_by_mode']['lora_both'], weight_decay=protocol['weight_decay'],
        betas=tuple(protocol['betas']),eps=protocol['epsilon'],foreach=False,fused=False)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer,lr_lambda=lambda step: 1.0)
    return optimizer, scheduler


def model_layout(model):
    return {tower:dict(width=getattr(model.clip.config,tower+'_config').hidden_size,
                       heads=getattr(model.clip.config,tower+'_config').num_attention_heads,
                       layers=getattr(model.clip.config,tower+'_config').num_hidden_layers)
            for tower in ('text','vision')}


def _buffers_equal(a, b):
    return (set(a) == set(b) and all(set(a[k]) == set(b[k]) and all(
        torch.is_tensor(a[k][n]) and a[k][n].dtype == b[k][n].dtype
        and a[k][n].shape == b[k][n].shape and torch.equal(a[k][n].cpu(),b[k][n].cpu())
        for n in a[k]) for k in a))


class ExtensionSession:
    """Own hooks and a reversible per-instance text mask wrapper.

    Attach after moving the model and before constructing the optimizer. Restore
    reference JSON and buffers first, then all trainables/optimizer/scheduler/RNG.
    Closing removes gates and the wrapper, so checkpoint before closing.
    """
    def __init__(self, model, preset='early', mode='dynamic', text_eos_token_id=None):
        require(model.mode == 'lora_both', 'Extension requires unchanged both-tower rank-8 LoRA')
        model_eos=model.clip.config.text_config.eos_token_id
        actual_eos=model_eos if text_eos_token_id is None else text_eos_token_id
        vocab_size=model.clip.config.text_config.vocab_size
        require(type(actual_eos) is int and 0<=actual_eos<vocab_size, 'Invalid actual text EOS token id')
        require(actual_eos==model_eos or (model_eos==2 and actual_eos==vocab_size-1),
                'Only explicit legacy config-EOS-2/highest-vocabulary-EOS guard adaptation is supported')
        self.eos_policy=('exact_model_tokenizer_eos' if actual_eos==model_eos
                         else 'legacy_config2_highest_token_eos')
        self.model = model
        self.controller = HookController(model,preset=preset,mode=mode)
        # Legacy HF CLIP config EOS=2 keeps native argmax-token pooling. Bind
        # only our external guard to the tokenizer's highest-ID true EOS; do
        # not edit either model config or change its pretrained pooling path.
        self.controller._eos=actual_eos
        self._had_text = 'text_features' in model.__dict__
        self._old_text_attribute = model.__dict__.get('text_features')
        self._text = model.text_features
        self._closed = False

        def wrapped(instance, text):
            if not isinstance(text, dict) or 'attention_mask' not in text:
                raise ValueError('Extension text_features requires an explicit attention_mask')
            mask = text['attention_mask']
            if not torch.is_tensor(mask) or mask.ndim != 2 or (
                    mask.dtype != torch.bool and (not torch.isfinite(mask).all() or not ((mask==0)|(mask==1)).all())):
                raise ValueError('Text attention_mask must contain only finite boolean/zero-one values')
            actual = dict(text,attention_mask=mask.bool())
            with self.controller.text_context(actual['attention_mask']):
                return self._text(actual)
        model.text_features = types.MethodType(wrapped,model)

    def optimizer_names(self, optimizer):
        expected = {id(p): name for name,p in self.model.named_parameters() if p.requires_grad}
        parameters = [p for group in optimizer.param_groups for p in group['params']]
        require(len(parameters)==len(expected) and len({id(p) for p in parameters})==len(parameters)
                and {id(p) for p in parameters}==set(expected),
                'Optimizer membership must include every LoRA and gate trainable exactly once and no frozen parameters')
        names = [expected[id(p)] for p in parameters]
        require(names == list(core_model.trainable_manifest(self.model)), 'Optimizer order differs from trainable manifest')
        return names

    def reference_buffers(self):
        return {key:{name: value.detach().cpu().clone() for name,value in gate.named_buffers()}
                for key,gate in self.controller.gates.items()}

    def load_references(self, artifact, buffers):
        require(set(artifact)=={'schema_version','payload','provenance'} and artifact['schema_version']==1,
                'Invalid reference artifact schema')
        # Precheck JSON/buffer equality before the one-shot controller mutation.
        expected={}
        for key,gate in self.controller.gates.items():
            expected[key]={'_reference':torch.tensor(artifact['payload']['references'][key],dtype=gate._reference.dtype),
                           '_reference_ready':torch.tensor(True,dtype=torch.bool)}
        require(_buffers_equal(buffers,expected), 'Reference JSON and saved buffers differ')
        self.controller.load_references(artifact['payload'])
        require(_buffers_equal(self.reference_buffers(),buffers), 'Reference restoration is not exact')

    @contextlib.contextmanager
    def native(self):
        with self.controller.disabled(), self.model.frozen_baseline():
            yield

    def checkpoint(self, optimizer, scheduler, epoch, step, identity, device, reference_sha256):
        cp=core_state.checkpoint_state(self.model,optimizer,scheduler,epoch,step,identity,device)
        cp['extension']=dict(schema_version=1,reference_sha256=reference_sha256,
            payload=self.controller.export_references(),buffers=self.reference_buffers(),
            optimizer_parameter_names=self.optimizer_names(optimizer))
        return cp

    def restore(self, checkpoint, optimizer, scheduler, identity, device, reference_sha256):
        extra=checkpoint['extension']
        require(extra['schema_version']==1 and extra['reference_sha256']==reference_sha256,
                'Checkpoint reference identity mismatch')
        require(extra['payload']==self.controller.export_references(), 'Checkpoint reference JSON/config mismatch')
        require(_buffers_equal(extra['buffers'],self.reference_buffers()), 'Checkpoint reference buffer mismatch')
        require(extra['optimizer_parameter_names']==self.optimizer_names(optimizer), 'Checkpoint optimizer membership mismatch')
        # Validate semantic AdamW recipe/moments and scheduler before any state is
        # copied. A self-consistent rehashed receipt is not sufficient to resume.
        if __package__ in (None, ''):
            from extensions.verify_extension import validate_checkpoint
        else:
            from .verify_extension import validate_checkpoint
        validate_checkpoint(checkpoint,identity,checkpoint['epoch'],checkpoint['global_step'],
                            {'payload':self.controller.export_references()},self.reference_buffers(),
                            read_document(ROOT/'Protocol.json')[0])
        core_state.restore_checkpoint(checkpoint,self.model,optimizer,scheduler,identity,device)

    @contextlib.contextmanager
    def capture_diagnostics(self):
        collected = {key:[] for key in self.controller.gates}
        handles=[]
        try:
            for key, layout in self.controller._layout.items():
                target=getattr(self.model.clip,layout['tower']+'_model').encoder.layers[layout['layer']].self_attn.out_proj
                def after(module, args, output, key=key):
                    collected[key].append({n:t.cpu().clone() for n,t in self.controller.last_diagnostics[key].items()})
                handles.append(target.register_forward_hook(after))
            yield collected
        finally:
            for handle in handles: handle.remove()

    def close(self):
        if self._closed: return
        self.controller.close()
        if self._had_text:
            self.model.text_features=self._old_text_attribute
        else:
            delattr(self.model,'text_features')
        self._closed=True

    def __enter__(self): return self
    def __exit__(self,*args): self.close()


def collect_references(session, rows, texts, root, processor, tokenizer, device, batch_size):
    """Present each approved source image and unique candidate prompt once.

    Only four image identity fields are read. No row label is accessed here.
    Calibration input selection/provenance remains caller responsibility.
    """
    clean=[{key:row[key] for key in ('id','path','sha256','pixel_sha256')} for row in rows]
    require(clean and len({row['id'] for row in clean})==len(clean)
            and len({row['pixel_sha256'] for row in clean})==len(clean), 'Calibration images must be unique')
    require(texts and len(set(texts))==len(texts), 'Locked calibration prompts must be nonempty and unique')
    tokens,effective=core_trainer.tokenize(tokenizer,texts,device)
    require(effective==texts,'Calibration prompt mapping changed')
    with session.controller.calibration():
        for start in range(0,len(clean),batch_size):
            session.model.image_features(core_trainer.image_batch(clean[start:start+batch_size],root,processor,device))
        for start in range(0,len(texts),batch_size):
            session.model.text_features({k:v[start:start+batch_size] for k,v in tokens.items()})
    session.controller.freeze_references()
    return dict(schema_version=1,payload=session.controller.export_references(),provenance=dict(
        images=clean,texts=list(texts),input_ids=tokens['input_ids'].cpu().tolist(),
        attention_mask=tokens['attention_mask'].bool().cpu().tolist(),labels_accessed=False,
        source_split='calibration',model_path_kind='native_frozen_ungated',
        image_presentations=len(clean),prompt_presentations=len(texts)))


def commit_state(directory, name, session, optimizer, scheduler, epoch, step, identity,
                 views, config, processor, tokenizer, device, training=None, native=False):
    staging=directory/f'.{name}.partial'
    staging.mkdir()
    diagnostics={}
    model=session.model
    started=time.perf_counter()
    context=session.native() if native else contextlib.nullcontext()
    with context:
        for key,view in views.items():
            capture=contextlib.nullcontext({}) if native else session.capture_diagnostics()
            with capture as observed:
                arrays,metadata=core_trainer.eval_scores(model,view,config['root'],processor,tokenizer,
                                                       device,config['protocol']['batch_size'],native)
            np.savez(staging/f'{key}.npz',**arrays)
            core_state.atomic_json(staging/f'{key}.json',metadata)
            diagnostics[key]=observed
    torch.save(diagnostics,staging/'GateDiagnostics.pt')
    gate_state={key:dict(alpha=gate.alpha.detach().cpu().tolist(),beta=gate.beta.detach().cpu().item(),
                        reference=gate.reference.cpu().tolist(),mode=gate.mode)
                for key,gate in session.controller.gates.items()}
    core_state.atomic_json(staging/'GateState.json',gate_state)
    cp=session.checkpoint(optimizer,scheduler,epoch,step,identity,device,identity['reference_sha256'])
    torch.save(cp,staging/'checkpoint.pt')
    receipt=dict(schema_version=1,epoch=epoch,global_step=step,identity=identity,
        status='TECHNICAL_ONLY' if identity['technical'] else 'EXTENSION_EPOCH_COMPLETE',
        baseline_kind='native_frozen' if native else ('initial_adapted' if epoch==0 else 'trained'),
        views=list(views),training=training,scientific_result=not identity['technical'],
        trainable_manifest=core_model.trainable_manifest(model),
        trainable_count=sum(p.numel() for p in model.parameters() if p.requires_grad),
        train_wall_seconds=training['wall_seconds'] if training else 0.,
        eval_wall_seconds=time.perf_counter()-started,
        cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(device) if device.type=='cuda' else None,
        cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(device) if device.type=='cuda' else None)
    core_state.seal_directory(staging,directory/name,receipt)


def run_unit(config, datalock):
    config=dict(config)
    require(config.get('unit') in {c['id'] for c in units()}, 'Execution requires one explicit extension unit')
    plan=make_plan(config,datalock)
    lock,_=read_document(datalock)
    protocol,_=read_document(config['protocol'])
    extension,_=read_document(config.get('extension_protocol',HERE/'ExtensionProtocol.json'))
    cell=next(c for c in plan['units'] if c['id']==config['unit'])
    directory=Path(cell['output'])
    final_epoch=1 if plan['smoke'] else 4
    stop=config.get('stop_after_epoch',final_epoch)
    require(type(stop) is int and 0<=stop<=final_epoch,'Invalid stop_after_epoch')
    if directory.exists() and any(directory.iterdir()) and not config.get('resume',False):
        raise FileExistsError('Extension output exists; explicit resume required')
    directory.mkdir(parents=True,exist_ok=True)
    device=core_trainer.configure_device(config.get('device','cpu'))
    config['protocol']=protocol
    with core_state.unit_lock(directory,config.get('resume',False)):
        try:
            identity_path=directory/'Identity.json'
            existing=json.loads(identity_path.read_text(encoding='utf-8')) if identity_path.exists() else None
            if not existing:
                # A crash during pre-identity calibration cannot be silently reused.
                require(not any(p.name!='RUNNING.json' for p in directory.iterdir()),
                        'Incomplete pre-identity output needs explicit external recovery')
            model=core_model.build_model(plan['model_path'],'lora_both',cell['seed']).to(device)
            if device.type=='cuda':
                torch.cuda.manual_seed_all(cell['seed']); torch.cuda.reset_peak_memory_stats(device)
            processor=core_trainer.CLIPImageProcessor.from_pretrained(plan['model_path'],local_files_only=True)
            tokenizer=core_trainer.CLIPTokenizer.from_pretrained(plan['model_path'],local_files_only=True)
            if tokenizer.eos_token_id!=model.clip.config.text_config.eos_token_id:
                require(model.clip.config.text_config.eos_token_id==2 and
                        tokenizer.eos_token_id==max(tokenizer.get_vocab().values()),
                        'Tokenizer/model EOS mismatch outside legacy highest-token CLIP convention')
            data=lock['datasets'][cell['dataset']]
            views=core_records.view_specs(lock,cell['dataset'])
            train=data['splits']['train']
            if plan['smoke']:
                train=train[:16]
                views={k:dict(view,rows=view['rows'][:16]) for k,view in views.items()}
            with ExtensionSession(model,cell['preset'],cell['gate_mode'],text_eos_token_id=tokenizer.eos_token_id) as session:
                optimizer,scheduler=make_optimizer(model,protocol)
                names=session.optimizer_names(optimizer)
                refs_path=directory/'References.json'; buffers_path=directory/'ReferenceBuffers.pt'
                if existing:
                    require(refs_path.is_file() and buffers_path.is_file(),'Missing locked reference artifacts; never recalibrate on resume')
                    require(digest_file(refs_path)==existing['reference_sha256'] and
                            digest_file(buffers_path)==existing['reference_buffers_sha256'],'Locked reference artifact hash mismatch')
                    refs=json.loads(refs_path.read_text(encoding='utf-8'))
                    buffers=torch.load(buffers_path,map_location='cpu',weights_only=True)
                    session.load_references(refs,buffers)
                else:
                    refs=collect_references(session,data['splits']['calibration'],views['calibration']['texts'],
                                            config['root'],processor,tokenizer,device,protocol['batch_size'])
                    core_state.atomic_json(refs_path,refs)
                    torch.save(session.reference_buffers(),buffers_path)
                identity=dict(schema_version=1,unit=cell['id'],cell={k:cell[k] for k in ('dataset','preset','gate_mode','seed')},
                    core_protocol_sha256=plan['core_protocol_sha256'],extension_protocol_sha256=plan['extension_protocol_sha256'],
                    datalock_sha256=plan['datalock_sha256'],model_files=plan['model_files'],producer_sha256=plan['producer_sha256'],
                    environment=core_state.environment(device),technical=plan['technical'],smoke=plan['smoke'],
                    model_layout=model_layout(model),text_eos_token_id=session.controller._eos,
                    model_eos_token_id=model.clip.config.text_config.eos_token_id,
                    text_vocab_size=model.clip.config.text_config.vocab_size,eos_policy=session.eos_policy,
                    trainable_manifest=core_model.trainable_manifest(model),optimizer_parameter_names=names,
                    reference_sha256=digest_file(refs_path),reference_buffers_sha256=digest_file(buffers_path))
                if existing:
                    require(existing==identity,'Immutable extension identity changed')
                    snapshot=directory/'Inputs.json'
                    require(snapshot.is_file() and json.loads(snapshot.read_text(encoding='utf-8'))==
                            dict(protocol=protocol,extension_protocol=extension,datalock=lock),
                            'Missing or changed immutable input snapshot')
                else:
                    core_state.atomic_json(identity_path,identity)
                    core_state.atomic_json(directory/'Inputs.json',dict(protocol=protocol,extension_protocol=extension,datalock=lock))
                if config.get('resume'): core_state.discard_uncommitted(directory)
                committed=[]
                for path in sorted(directory.glob('epoch_*')):
                    require(path.is_dir() and len(path.name)==9 and path.name[6:].isdigit(),'Unexpected epoch path')
                    receipt=core_state.verify_directory(path); epoch=int(path.name[6:])
                    require(receipt['identity']==identity and receipt['epoch']==epoch,'Committed epoch identity mismatch')
                    committed.append(epoch)
                require(not committed or committed==list(range(committed[-1]+1)),'Missing committed epoch')
                require(not committed or committed[-1]<=stop<=final_epoch,'Stop precedes saved epoch')
                frozen=directory/'frozen_baseline'
                require(not committed or frozen.is_dir(),'Saved epochs lack native baseline')
                if frozen.exists():
                    require(core_state.verify_directory(frozen)['identity']==identity,'Native identity mismatch')
                else:
                    commit_state(directory,'frozen_baseline',session,optimizer,scheduler,0,0,identity,views,config,processor,tokenizer,device,native=True)
                if committed:
                    cp=core_state.load_checkpoint(directory/f'epoch_{committed[-1]:03}')
                    step_per_epoch=2 if plan['smoke'] else math.ceil(len(train)/protocol['batch_size'])
                    require(cp['epoch']==committed[-1] and cp['global_step']==cp['epoch']*step_per_epoch,'Resume epoch/step mismatch')
                    core_verifier.validate_training_state(cp,identity,cp['global_step'])
                    session.restore(cp,optimizer,scheduler,identity,device,identity['reference_sha256'])
                    epoch,step=cp['epoch'],cp['global_step']
                else:
                    epoch,step=0,0
                    commit_state(directory,'epoch_000',session,optimizer,scheduler,0,0,identity,views,config,processor,tokenizer,device)
                for next_epoch in range(epoch+1,stop+1):
                    training=core_trainer.train_epoch(model,train,views['calibration']['texts'],data['class_names'],config['root'],
                        processor,tokenizer,optimizer,scheduler,cell['seed'],next_epoch,protocol['batch_size'],device,
                        max_steps=2 if plan['smoke'] else None)
                    epoch=next_epoch; step+=training['steps']
                    commit_state(directory,f'epoch_{epoch:03}',session,optimizer,scheduler,epoch,step,identity,views,config,processor,tokenizer,device,training)
                result=dict(status=('TECHNICAL_COMPLETE' if plan['technical'] else 'EXTENSION_COMPLETE') if epoch==final_epoch else 'STOPPED_AT_EPOCH_BOUNDARY',
                    epoch=epoch,global_step=step,unit=cell['id'],directory=str(directory),identity=identity,
                    scientific_result=not plan['technical'],epoch_receipt_sha256=digest_file(directory/f'epoch_{epoch:03}'/'Receipt.json'))
                core_state.atomic_json(directory/'RunReceipt.json',result)
                return result
        except Exception as error:
            core_state.atomic_json(directory/'LastError.json',dict(type=type(error).__name__,message=str(error)))
            raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group(required=True)
    for name in ('plan','self-test','dry-run','smoke','run'):
        actions.add_argument('--'+name,action='store_true')
    parser.add_argument('--protocol',default=str(ROOT/'Protocol.json'))
    parser.add_argument('--extension-protocol',default=str(HERE/'ExtensionProtocol.json'))
    parser.add_argument('--datalock')
    parser.add_argument('--root',default=str(Path.cwd()))
    parser.add_argument('--model-path')
    parser.add_argument('--output',default=str(HERE/'runs'))
    parser.add_argument('--unit',default='all')
    parser.add_argument('--device',default='cpu',choices=('cpu','cuda'))
    parser.add_argument('--technical',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--stop-after-epoch',type=int)
    args=parser.parse_args()
    if args.self_test:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                 OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        raise SystemExit(subprocess.call([sys.executable,'-B','-X','utf8','-m','unittest','discover',
                                         '-s',str(HERE/'tests'),'-v'],env=env))
    if not args.datalock: parser.error('--datalock is required')
    cfg=dict(root=args.root,protocol=args.protocol,extension_protocol=args.extension_protocol,
             model_path=args.model_path,output_dir=args.output,unit=args.unit,device=args.device,
             technical=args.technical,smoke=args.smoke,resume=args.resume)
    if args.stop_after_epoch is not None: cfg['stop_after_epoch']=args.stop_after_epoch
    if args.plan or args.dry_run:
        plan=make_plan(cfg,args.datalock)
        print(json.dumps(plan,indent=2))
        if args.dry_run:
            import shlex
            for cell in plan['units']:
                cmd=[sys.executable,'-B','-X','utf8',str(HERE/'runner.py'),'--run','--unit',cell['id'],
                     '--datalock',args.datalock,'--protocol',args.protocol,'--extension-protocol',args.extension_protocol,
                     '--root',args.root,'--output',args.output,'--device',args.device]
                if args.model_path: cmd+=['--model-path',args.model_path]
                if args.technical: cmd+=['--technical']
                if args.resume: cmd+=['--resume']
                print(subprocess.list2cmdline(cmd) if os.name=='nt' else shlex.join(cmd))
    else:
        if args.unit=='all': parser.error('--run and --smoke require one explicit --unit')
        print(json.dumps(run_unit(cfg,args.datalock),indent=2))


if __name__=='__main__': main()
