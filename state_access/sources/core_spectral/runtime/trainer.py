"""Offline prospective A1 training; no historical reconstruction or selectors."""
import argparse
import contextlib
import hashlib
import json
import math
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.nn import functional as F
from transformers import CLIPImageProcessor, CLIPTokenizer

from model import (MODES, build_model, feature_tensor, get_trainable_state,
                   restore_trainable, trainable_manifest)
from records import (canonical, digest_file, read_document, resolve_inside,
                     validate_inputs, view_specs)
from state import (atomic_json, checkpoint_state, discard_uncommitted, environment,
                   load_checkpoint, restore_checkpoint, seal_directory, unit_lock,
                   verify_directory)


def producer_hashes():
    here = Path(__file__).resolve().parent
    return {name:digest_file(here/name) for name in ('model.py','records.py','state.py','trainer.py')}


def units(protocol, lock):
    result = [dict(id=f'{dataset}__{mode}__s{seed}',dataset=dataset,mode=mode,seed=seed)
              for dataset in lock['datasets'] for mode in protocol['modes'] for seed in protocol['seeds']]
    if 'cells' in protocol:
        declared = {cell['id']:(cell['dataset'],cell['mode'],cell['seed']) for cell in protocol['cells']}
        expected = {cell['id']:(cell['dataset'],cell['mode'],cell['seed']) for cell in result}
        if len(declared) != len(protocol['cells']) or declared != expected:
            raise ValueError('Explicit protocol cells differ from factorial design')
    return result


def execution_units(protocol,lock,selected,smoke=False):
    choices = units(protocol,lock)
    if selected != 'all':
        chosen = [row for row in choices if row['id'] == selected]
        if not chosen:
            raise ValueError('Unknown requested unit')
        return chosen
    if not smoke:
        raise ValueError('Scientific execution requires a single unit')
    return [row for row in choices if row['dataset'] == 'cifar100' and row['seed'] == 42]


def make_plan(config, datalock):
    lock, lock_hash = read_document(datalock)
    protocol, model_path = validate_inputs(config,lock)
    _, protocol_hash = read_document(config['protocol'])
    if lock.get('protocol_sha256',protocol_hash) != protocol_hash:
        raise ValueError('Exact protocol file hash differs from DataLock')
    output = Path(config['output_dir']).resolve()
    if config.get('smoke',False):
        output /= 'smoke'
    planned = (execution_units(protocol,lock,config.get('unit','all'),smoke=True)
               if config.get('smoke',False) else units(protocol,lock))
    return dict(status='INPUTS_VALIDATED_NO_MODEL_LOADED', protocol_sha256=protocol_hash,
        datalock_sha256=lock_hash,model_files=lock['model']['files'],model_path=str(model_path),
        producer_sha256=producer_hashes(),units=[dict(cell,output=str(output/cell['id'])) for cell in planned],
        scientific_result=False)


def configure_device(value):
    device = torch.device(value)
    if device.type not in ('cpu','cuda'):
        raise ValueError('Only CPU and CUDA devices are supported')
    if device.type == 'cuda':
        os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
        if not torch.cuda.is_available():
            raise RuntimeError('Requested CUDA device is unavailable')
        index = torch.cuda.current_device() if device.index is None else device.index
        device = torch.device('cuda',index)
        torch.cuda.set_device(device)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)
    return device


def autocast(device):
    # Fixed float32 in both scientific runs and their technical smoke.
    return contextlib.nullcontext()


def image_batch(rows, root, processor, device):
    images = []
    for row in rows:
        with Image.open(resolve_inside(root,row['path'])) as image:
            images.append(image.convert('RGB'))
    pixels = processor(images=images,return_tensors='pt')['pixel_values'].to(device,dtype=torch.float32)
    if not torch.isfinite(pixels).all():
        raise FloatingPointError('Nonfinite preprocessed pixels')
    return pixels


def tokenize(tokenizer, texts, device, context_texts=None):
    effective = list(texts) if context_texts is None else ['X X X X '+text for text in context_texts]
    limit = tokenizer.model_max_length
    batch = tokenizer(effective,padding=True,truncation=False,return_tensors='pt')
    if batch['input_ids'].shape[1] > limit:
        raise ValueError('Prompt exceeds fixed CLIP context; no silent truncation')
    ids, mask = batch['input_ids'],batch['attention_mask']
    positions = torch.arange(ids.shape[1]).expand_as(ids)
    eos = torch.where((ids == tokenizer.eos_token_id) & mask.bool(), positions,
                      torch.full_like(positions,ids.shape[1])).min(dim=1).values
    if (eos >= ids.shape[1]).any() or (eos != mask.sum(1)-1).any():
        raise ValueError('EOS token must match the last nonpadding position')
    if context_texts is not None:
        prefix = tokenizer('X X X X',add_special_tokens=False)['input_ids']
        if len(prefix) != 4 or not torch.equal(ids[:,1:5],torch.tensor(prefix).expand(len(effective),-1)):
            raise ValueError('Context prefix must tokenize into exactly four tokens')
        if (eos < 6).any():
            raise ValueError('A context prompt has no remaining text before EOS')
    return {key:value.to(device) for key,value in batch.items() if key in ('input_ids','attention_mask')}, effective


@torch.no_grad()
def training_image_cache(model,rows,root,processor,device,batch_size):
    # Only text-only adaptation leaves the entire vision function unchanged.
    if model.mode != 'lora_text':
        return None
    key = tuple((row['id'],row['sha256'],row['pixel_sha256']) for row in rows)
    if not hasattr(model,'_training_image_cache') or model._training_image_cache[0] != key:
        features = []
        for start in range(0,len(rows),batch_size):
            pixels = image_batch(rows[start:start+batch_size],root,processor,device)
            features.append(model.image_features(pixels).cpu())
        model._training_image_cache = (key,torch.cat(features))
    return model._training_image_cache[1]


def train_epoch(model, rows, texts, context_texts, root, processor, tokenizer,
                optimizer, scheduler, seed, epoch, batch_size, device, max_steps=None):
    if device.type == 'cuda': torch.cuda.synchronize(device)
    started = time.perf_counter()
    model.train()
    # Separate generator isolates the exact epoch order from model/evaluation RNG.
    generator = torch.Generator(device='cpu').manual_seed(seed + epoch * 1000003)
    order = torch.randperm(len(rows),generator=generator).tolist()
    batches = [order[start:start+batch_size] for start in range(0,len(order),batch_size)]
    if max_steps is not None:
        batches = [batches[index % len(batches)] for index in range(max_steps)]
    prompt = context_texts if model.mode in ('text_context','dual_context') else None
    tokens, _ = tokenize(tokenizer,texts,device,prompt)
    cached_images = training_image_cache(model,rows,root,processor,device,batch_size)
    losses = []
    for indices in batches:
        batch = [rows[index] for index in indices]
        pixels = image_batch(batch,root,processor,device) if cached_images is None else None
        labels = torch.tensor([row['label'] for row in batch],dtype=torch.long,device=device)
        optimizer.zero_grad(set_to_none=True)
        with autocast(device):
            scores = (model(pixels,tokens) if cached_images is None else
                      cached_images[indices].to(device) @ model.text_features(tokens).T)
            loss = F.cross_entropy(scores.float(),labels)
        if not torch.isfinite(loss):
            raise FloatingPointError('Nonfinite loss')
        loss.backward()
        for key,parameter in model.named_parameters():
            if parameter.requires_grad:
                if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                    raise FloatingPointError(f'Missing/nonfinite gradient: {key}')
        optimizer.step()
        scheduler.step()
        if any(not torch.isfinite(parameter).all() for parameter in model.parameters() if parameter.requires_grad):
            raise FloatingPointError('Nonfinite adapter after optimizer step')
        losses.append(float(loss.detach().cpu()))
    if device.type == 'cuda': torch.cuda.synchronize(device)
    return dict(steps=len(batches),losses=losses,order=order,learning_rate=optimizer.param_groups[0]['lr'],
                wall_seconds=time.perf_counter()-started)


@torch.no_grad()
def eval_scores(model, view, root, processor, tokenizer, device, batch_size=16, native=False):
    """Return full normalized features and cosine scores, without any label reads."""
    model.eval()
    context_texts = view['context_texts'] if not native and model.mode in ('text_context','dual_context') else None
    tokens,effective = tokenize(tokenizer,view['texts'],device,context_texts)
    text_features = []
    for start in range(0,len(effective),batch_size):
        text = {key:value[start:start+batch_size] for key,value in tokens.items()}
        with autocast(device):
            text_features.append(model.text_features(text).cpu())
    cache_key = tuple((row['id'],row['sha256'],row['pixel_sha256']) for row in view['rows'])
    cache = getattr(model,'_evaluation_image_cache',{}) if model.mode == 'lora_text' else {}
    if cache_key in cache:
        image_features = [cache[cache_key]]
    else:
        image_features = []
        for start in range(0,len(view['rows']),batch_size):
            pixels = image_batch(view['rows'][start:start+batch_size],root,processor,device)
            with autocast(device):
                image_features.append(model.image_features(pixels).cpu())
        if model.mode == 'lora_text':
            cache[cache_key] = torch.cat(image_features)
            model._evaluation_image_cache = cache
    images, texts = torch.cat(image_features),torch.cat(text_features)
    scores = images @ texts.T
    if not torch.isfinite(scores).all():
        raise FloatingPointError('Nonfinite evaluation scores')
    metadata = dict(schema_version=1,row_ids=[row['id'] for row in view['rows']],
        row_sha256=[row['sha256'] for row in view['rows']],
        row_pixel_sha256=[row['pixel_sha256'] for row in view['rows']],
        candidate_ids=list(range(len(view['texts']))),texts=view['texts'],effective_texts=effective,
        score_kind='normalized_cosine_float32_unscaled',
        frozen_logit_scale_exp=float(model.clip.logit_scale.detach().float().exp().cpu()),
        labels_accessed=False,shape=list(scores.shape))
    return dict(scores=scores.numpy().astype(np.float32,copy=False),
        image_features=images.numpy().astype(np.float32,copy=False),
        text_features=texts.numpy().astype(np.float32,copy=False)),metadata


def commit_epoch(directory, name, model, optimizer, scheduler, epoch, step, identity,
                 views, config, processor, tokenizer, device, training=None, native=False):
    staging = directory/f'.{name}.partial'
    staging.mkdir()
    context = model.frozen_baseline() if native else contextlib.nullcontext()
    view_wall_seconds = {}
    if device.type == 'cuda': torch.cuda.synchronize(device)
    eval_started = time.perf_counter()
    with context:
        for key, view in views.items():
            started = time.perf_counter()
            arrays,metadata = eval_scores(model,view,config['root'],processor,tokenizer,device,
                                          config['protocol']['batch_size'],native)
            np.savez(staging/f'{key}.npz',**arrays)
            atomic_json(staging/f'{key}.json',metadata)
            if device.type == 'cuda': torch.cuda.synchronize(device)
            view_wall_seconds[key] = time.perf_counter()-started
    eval_wall_seconds = time.perf_counter()-eval_started
    checkpoint = checkpoint_state(model,optimizer,scheduler,epoch,step,identity,device)
    torch.save(checkpoint,staging/'checkpoint.pt')
    receipt = dict(schema_version=1,epoch=epoch,global_step=step,identity=identity,
        status='TECHNICAL_SMOKE_ONLY' if config.get('smoke') else 'PROSPECTIVE_EPOCH_COMPLETE',
        baseline_kind='native_frozen' if native else ('initial_adapted' if epoch == 0 else 'trained'),
        trainable_manifest=trainable_manifest(model),training=training,
        trainable_count=sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
        train_wall_seconds=training['wall_seconds'] if training else 0.,
        eval_wall_seconds=eval_wall_seconds,view_wall_seconds=view_wall_seconds,
        cuda_peak_allocated_bytes=None,cuda_peak_reserved_bytes=None,
        views=list(views),scientific_result=not config.get('smoke',False))
    if device.type == 'cuda':
        receipt['cuda_peak_allocated_bytes'] = torch.cuda.max_memory_allocated(device)
        receipt['cuda_peak_reserved_bytes'] = torch.cuda.max_memory_reserved(device)
    seal_directory(staging,directory/name,receipt)
    return receipt


def run_unit(config, datalock):
    config = dict(config)
    lock,lock_hash = read_document(datalock)
    protocol,protocol_hash = read_document(config['protocol'])
    final_epoch = 1 if config.get('smoke',False) else protocol['epochs']
    stop = config.get('stop_after_epoch',final_epoch)
    if type(stop) is not int or not 0 <= stop <= final_epoch:
        raise ValueError('Invalid technical stop_after_epoch')
    plan = make_plan(config,datalock)
    config['protocol'] = protocol
    choices = {cell['id']:cell for cell in plan['units']}
    if config['unit'] not in choices:
        raise ValueError(f'Unknown unit: {config["unit"]}')
    cell = choices[config['unit']]
    directory = Path(cell['output'])
    if directory.exists():
        previous_epochs = [int(path.name[6:]) for path in directory.glob('epoch_*')
                           if path.is_dir() and len(path.name)==9 and path.name[6:].isdigit()]
        if previous_epochs and (max(previous_epochs)>final_epoch or stop<max(previous_epochs)):
            raise ValueError('Stop precedes committed epoch or epoch exceeds protocol budget')
    if directory.exists() and any(directory.iterdir()) and not config.get('resume',False):
        raise FileExistsError(f'Unit already exists; explicit --resume required: {directory}')
    device = configure_device(config.get('device','cpu'))
    model = build_model(plan['model_path'],cell['mode'],cell['seed']).to(device)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(cell['seed'])
        torch.cuda.reset_peak_memory_stats(device)
    identity = dict(schema_version=1,unit=cell['id'],protocol_sha256=protocol_hash,
        datalock_sha256=lock_hash,model_files=lock['model']['files'],
        producer_sha256=producer_hashes(),environment=environment(device),
        smoke=bool(config.get('smoke',False)),trainable_manifest=trainable_manifest(model))
    processor = CLIPImageProcessor.from_pretrained(plan['model_path'],local_files_only=True)
    tokenizer = CLIPTokenizer.from_pretrained(plan['model_path'],local_files_only=True)
    eos = model.clip.config.text_config.eos_token_id
    if eos != 2 and tokenizer.eos_token_id != eos:
        raise ValueError('Tokenizer/model EOS identity mismatch')
    data = lock['datasets'][cell['dataset']]
    train = data['splits']['train']
    views = view_specs(lock,cell['dataset'])
    smoke = config.get('smoke',False)
    if smoke:
        train = train[:16]
        views = {name:dict(view,rows=view['rows'][:16]) for name,view in views.items()}
    steps_per_epoch = math.ceil(len(train)/protocol['batch_size'])
    total_steps = 2 if smoke else steps_per_epoch*protocol['epochs']
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
        lr=protocol['learning_rate_by_mode'][cell['mode']],weight_decay=protocol['weight_decay'],
        betas=(.9,.999),eps=1e-8,foreach=False,fused=False)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer,lr_lambda=lambda step:1.0)
    directory.mkdir(parents=True,exist_ok=True)
    with unit_lock(directory,config.get('resume',False)):
        try:
            identity_path = directory/'Identity.json'
            if identity_path.exists():
                if json.loads(identity_path.read_text(encoding='utf-8')) != identity:
                    raise ValueError('Immutable run identity changed')
            else:
                if any(path.name != 'RUNNING.json' for path in directory.iterdir()):
                    raise ValueError('Existing unit lacks immutable identity; cannot resume')
                atomic_json(identity_path,identity)
                atomic_json(directory/'Inputs.json',dict(protocol=protocol,datalock=lock,
                    effective_configuration=dict(device=str(device),smoke=bool(smoke),
                    score_kind='normalized_cosine_float32_unscaled')))
            if config.get('resume',False):
                discard_uncommitted(directory)
            committed = sorted(directory.glob('epoch_*'))
            epochs = []
            for path in committed:
                if not path.is_dir() or len(path.name) != 9 or not path.name[6:].isdigit():
                    raise ValueError('Unexpected epoch path')
                receipt = verify_directory(path)
                epoch = int(path.name[6:])
                if receipt['identity'] != identity or receipt['epoch'] != epoch:
                    raise ValueError('Committed epoch identity mismatch')
                epochs.append(epoch)
            if epochs and epochs != list(range(epochs[-1]+1)):
                raise ValueError('Missing committed epochs')
            if epochs and not (directory/'frozen_baseline').is_dir():
                raise ValueError('Missing native frozen baseline')
            if (directory/'frozen_baseline').exists():
                frozen = verify_directory(directory/'frozen_baseline')
                if frozen['identity'] != identity:
                    raise ValueError('Frozen baseline identity mismatch')
            else:
                commit_epoch(directory,'frozen_baseline',model,optimizer,scheduler,0,0,identity,
                             views,config,processor,tokenizer,device,native=True)
            if epochs:
                checkpoint = load_checkpoint(directory/f'epoch_{epochs[-1]:03}')
                if checkpoint['epoch'] != epochs[-1] or checkpoint['global_step'] != epochs[-1]*(2 if smoke else steps_per_epoch):
                    raise ValueError('Resume checkpoint epoch/step differs from committed path')
                restore_checkpoint(checkpoint,model,optimizer,scheduler,identity,device)
                epoch,step = checkpoint['epoch'],checkpoint['global_step']
                expected_steps = (2*epoch) if smoke else steps_per_epoch*epoch
                if step != expected_steps:
                    raise ValueError('Checkpoint global step differs from epoch boundary')
            else:
                epoch,step = 0,0
                commit_epoch(directory,'epoch_000',model,optimizer,scheduler,epoch,step,identity,
                             views,config,processor,tokenizer,device)
        
            for next_epoch in range(epoch+1,min(stop,final_epoch)+1):
                texts = data.get('texts',[data['template'].format(name.replace('_',' ')) for name in data['class_names']])
                training = train_epoch(model,train,texts,data['class_names'],config['root'],
                    processor,tokenizer,optimizer,scheduler,cell['seed'],next_epoch,
                    protocol['batch_size'],device,max_steps=2 if smoke else None)
                step += training['steps']
                epoch = next_epoch
                commit_epoch(directory,f'epoch_{epoch:03}',model,optimizer,scheduler,epoch,step,
                    identity,views,config,processor,tokenizer,device,training=training)
            result = dict(status='TECHNICAL_SMOKE_ONLY' if smoke else
                          ('PROSPECTIVE_COMPLETE' if epoch == final_epoch else 'STOPPED_AT_EPOCH_BOUNDARY'),
                          epoch=epoch,global_step=step,unit=cell['id'],identity=identity)
            last_folder = directory/f'epoch_{epoch:03}'
            last_receipt = verify_directory(last_folder)
            for field in ('trainable_count','train_wall_seconds','eval_wall_seconds',
                          'cuda_peak_allocated_bytes','cuda_peak_reserved_bytes'):
                result[field] = last_receipt[field]
            result['epoch_receipt_sha256'] = digest_file(last_folder/'Receipt.json')
            atomic_json(directory/'RunReceipt.json',result)
            return result
        except Exception as error:
            atomic_json(directory/'LastError.json',dict(type=type(error).__name__,message=str(error)))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for action in ('self-test','plan','dry-run','run'):
        actions.add_argument('--'+action,action='store_true')
    parser.add_argument('--datalock')
    parser.add_argument('--protocol')
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[5]))
    parser.add_argument('--model-path')
    parser.add_argument('--output',default=str(Path(__file__).resolve().parent/'runs'))
    parser.add_argument('--unit',default='all')
    parser.add_argument('--device',choices=('cpu','cuda'),default='cpu')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--smoke',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        raise SystemExit(subprocess.call([sys.executable,'-B','-X','utf8','-m','unittest','discover',
            '-s',str(Path(__file__).resolve().parent/'tests'),'-v']))
    if not args.datalock or not args.protocol:
        parser.error('--datalock and --protocol are required')
    config = dict(root=args.root,model_path=args.model_path,protocol=args.protocol,output_dir=args.output,
                  unit=args.unit,device=args.device,resume=args.resume,smoke=args.smoke)
    if args.plan or args.dry_run:
        plan = make_plan(config,args.datalock)
        print(json.dumps(plan,indent=2))
        if args.dry_run:
            for cell in plan['units']:
                command = [sys.executable,'-B',str(Path(__file__).resolve()),'--run',
                    '--unit',cell['id'],'--datalock',args.datalock,'--protocol',args.protocol,
                    '--root',args.root,'--output',args.output,'--device',args.device]
                if args.model_path: command += ['--model-path',args.model_path]
                if args.smoke: command += ['--smoke']
                if args.resume: command += ['--resume']
                print(subprocess.list2cmdline(command) if os.name == 'nt' else shlex.join(command))
    else:
        if args.unit == 'all':
            if not args.smoke:
                parser.error('Scientific execution requires a single --unit for disjoint scheduling')
            lock,_ = read_document(args.datalock)
            protocol,_ = read_document(args.protocol)
            for cell in execution_units(protocol,lock,'all',smoke=True):
                print(json.dumps(run_unit(dict(config,unit=cell['id']),args.datalock),indent=2))
        else:
            print(json.dumps(run_unit(config,args.datalock),indent=2))


if __name__ == '__main__':
    main()
