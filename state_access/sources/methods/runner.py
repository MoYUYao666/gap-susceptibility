"""Offline, explicit-input training CLI. Importing this module does not load weights.

No data discovery, implicit historical recipes, network fallback or GPU scheduling.
The parent supplies a locked tensor bundle and every optimizer/config identity.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import platform
import numpy as np
import torch

_spec=importlib.util.spec_from_file_location('a1_independent_method_runtime',Path(__file__).with_name('runtime.py'))
rt=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)


def matrix():
    return [{'dataset':d,'arm':a,'seed':s} for d in ('dtd','cifar100') for a in rt.ARMS for s in (42,43,44)]


def epoch_order(n,seed,epoch):
    # Match the replacement runtime: epoch is one-based, isolated from model RNG.
    return torch.randperm(n,generator=torch.Generator(device='cpu').manual_seed(seed+epoch*1000003)).tolist()


def digest_json(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def validate_config(c):
    required={'schema','dataset','arm','seed','epochs','batch_size','rank','scale','learning_rate',
              'router_learning_rate','alpha_learning_rate','alpha_schedule','schedule','precision',
              'tf32','score','optimizer','model_path','model_assets','data_path','data_sha256',
              'reference_cache_keys','source_protocol_sha256','deterministic_algorithms','cpu_threads'}
    if set(c)!=required:raise ValueError('Explicit configuration inventory mismatch')
    if c['schema']!='A1_NEW_METHOD_RUN_V1' or c['dataset'] not in ('dtd','cifar100') or c['arm'] not in rt.ARMS or c['seed'] not in (42,43,44):
        raise ValueError('Unapproved matrix cell')
    locked={'epochs':4,'batch_size':32,'rank':8,'scale':2.,'learning_rate':5e-4,
            'router_learning_rate':5e-4,'alpha_learning_rate':1e-5,'alpha_schedule':'cosine',
            'schedule':'constant','precision':'float32','tf32':False,'score':'unscaled_normalized_cosine'}
    if any(c[k]!=v for k,v in locked.items()):raise ValueError('Locked method recipe changed')
    o=c['optimizer']
    if set(o)!={'name','weight_decay','betas','eps'} or o['name']!='AdamW':raise ValueError('Explicit AdamW recipe required')
    if o['weight_decay']!=.01 or o['betas']!=[.9,.999] or o['eps']!=1e-8:
        raise ValueError('Invalid optimizer settings')
    if c['deterministic_algorithms'] is not True or type(c['cpu_threads']) is not int or c['cpu_threads']!=2:
        raise ValueError('Explicit determinism and CPU thread settings required')
    refs=c['reference_cache_keys']
    if set(refs)!={'native_model','preprocessing','image_sample_order','text_candidate_order'}:
        raise ValueError('Reference identity inventory mismatch')
    hashes=[c['data_sha256'],c['source_protocol_sha256'],*refs.values(),*c['model_assets'].values()]
    if not c['model_assets'] or any(not isinstance(v,str) or len(v)!=64 or any(ch not in '0123456789abcdef' for ch in v) for v in hashes):
        raise ValueError('All identities must be lowercase SHA256')


def reference_keys(bundle,keys):
    """Bind cached reference rows to sample order and original token/candidate IDs."""
    result=dict(keys)
    result['image_sample_order']=digest_json({'train':bundle['train']['sample_ids'],
                        'evaluations':{k:v['sample_ids'] for k,v in sorted(bundle['evaluations'].items())}})
    result['text_candidate_order']=digest_json({'class_ids':bundle['class_ids'],
                                             'text':{k:v.tolist() for k,v in sorted(bundle['text'].items())}})
    return result


def _features(x,n):
    if not isinstance(x,torch.Tensor) or x.device.type!='cpu' or x.dtype!=torch.float32 or x.shape!=(n,512):
        raise ValueError('Reference features must be CPU float32 [rows,512]')
    if not torch.isfinite(x).all() or not torch.allclose(x.norm(dim=-1),torch.ones(n),atol=2e-5,rtol=0):
        raise ValueError('Reference feature normalization invalid')


def validate_bundle(b,c):
    if set(b)!={'schema','dataset','reference_cache_keys','class_ids','text','native_text','train','evaluations'}:
        raise ValueError('Input bundle schema mismatch')
    if b['schema']!='A1_NEW_METHOD_INPUT_V1' or b['dataset']!=c['dataset'] or b['reference_cache_keys']!=c['reference_cache_keys']:
        raise ValueError('Input or reference identity mismatch')
    if reference_keys(b,c['reference_cache_keys'])!=c['reference_cache_keys']:
        raise ValueError('Reference row/token mapping changed')
    classes=b['class_ids'];nclasses=len(classes)
    if nclasses<2 or len(set(classes))!=nclasses:raise ValueError('Duplicate or missing candidate IDs')
    if set(b['text']) not in ({'input_ids','attention_mask'},{'input_ids','attention_mask','position_ids'}):
        raise ValueError('Explicit original text IDs/mask required')
    shape=b['text']['input_ids'].shape
    if len(shape)!=2 or shape[0]!=nclasses:raise ValueError('Candidate token mapping mismatch')
    for k,v in b['text'].items():
        if v.dtype!=torch.long or v.device.type!='cpu' or v.shape!=shape:raise ValueError('Invalid text input '+k)
    _features(b['native_text'],nclasses)
    if set(b['evaluations'])!={'calibration','test'}:raise ValueError('Separate calibration and test splits required')
    seen=set()
    for split in [b['train'],*b['evaluations'].values()]:
        if set(split)!={'pixels','labels','sample_ids','native_image'}:raise ValueError('Split schema mismatch')
        ids=split['sample_ids'];n=len(ids);x=split['pixels'];y=split['labels']
        if n==0 or any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=n or seen.intersection(ids):
            raise ValueError('Empty, duplicate or cross-split sample IDs')
        seen.update(ids)
        if x.device.type!='cpu' or x.dtype!=torch.float32 or x.ndim!=4 or x.shape[:2]!=(n,3) or not torch.isfinite(x).all():
            raise ValueError('Invalid image tensor')
        if y.device.type!='cpu' or y.dtype!=torch.long or y.shape!=(n,) or (y<0).any() or (y>=nclasses).any():
            raise ValueError('Invalid label/candidate mapping')
        _features(split['native_image'],n)


def validate_production_base(base):
    text=base.config.text_config;vision=base.config.vision_config
    actual=(base.config.projection_dim,text.hidden_size,text.num_hidden_layers,text.num_attention_heads,
            text.max_position_embeddings,vision.hidden_size,vision.num_hidden_layers,
            vision.num_attention_heads,vision.image_size,vision.patch_size)
    if actual!=(512,512,12,8,77,768,12,12,224,32):
        raise ValueError('Scientific runner requires the approved CLIP B32 architecture')


LOADER_ASSETS=frozenset({'config.json','merges.txt','preprocessor_config.json','pytorch_model.bin',
                         'special_tokens_map.json','tokenizer.json','tokenizer_config.json','vocab.json'})


def checked_assets(c,root):
    model=(root/c['model_path']).resolve()
    if not model.is_dir():raise ValueError('Local model directory missing')
    if set(c['model_assets'])!=LOADER_ASSETS:
        raise ValueError('Model manifest must contain exactly the eight DataLock loader assets')
    # Bind only loader inputs. A verified file symlink is allowed: no 600MB copy.
    for name,expected in c['model_assets'].items():
        path=model/name
        if not path.is_file() or sha256(path)!=expected:
            raise ValueError('Model asset absent or changed: '+name)
    # Explicit metadata allowlist; unknown files fail closed, including alternate
    # weights, adapter/processor configs, added tokens and executable overrides.
    ignored_files={'.gitattributes','.gitignore','.gitmodules','README','README.md','README.txt',
                   'LICENSE','LICENSE.md','LICENSE.txt','NOTICE','NOTICE.md','NOTICE.txt'}
    for directory,dirs,files in os.walk(model,followlinks=False):
        dirs[:]=[name for name in dirs if name not in ('.cache','.git')]
        for name in dirs:
            if (Path(directory)/name).is_symlink():
                raise ValueError('Unexpected model directory link: '+name)
        for name in files:
            relative=(Path(directory)/name).relative_to(model).as_posix()
            if relative not in LOADER_ASSETS and relative not in ignored_files:
                raise ValueError('Unexpected computation-affecting or unknown model asset: '+relative)
    if c['reference_cache_keys']['native_model']!=digest_json(c['model_assets']):
        raise ValueError('Native reference model key is not the locked loader asset manifest')
    return model


def should_commit(completed_batches,total_batches):
    return completed_batches%8==0 or completed_batches==total_batches


def atomic_save(value,path):
    path=Path(path);tmp=path.with_name(path.name+'.partial')
    torch.save(value,tmp);os.replace(tmp,path)


def evaluate(model,bundle,device):
    previous=model.training;model.eval();out={}
    try:
        with torch.no_grad():
            text_features=[]
            for start in range(0,len(bundle['class_ids']),32):
                text={k:v[start:start+32].to(device) for k,v in bundle['text'].items()}
                reference=bundle['native_text'][start:start+32].to(device)
                text_features.append(model.text_features(text,reference).cpu())
            tf=torch.cat(text_features)
            for name,split in bundle['evaluations'].items():
                image_features=[]
                for start in range(0,len(split['sample_ids']),32):
                    im=model.image_features(split['pixels'][start:start+32].to(device),split['native_image'][start:start+32].to(device))
                    image_features.append(im.cpu())
                images=torch.cat(image_features)
                matrix=images@tf.T
                if not torch.isfinite(matrix).all():raise FloatingPointError('Nonfinite evaluation scores')
                out[name]={'scores':matrix,'predictions':matrix.argmax(-1),'labels':split['labels'],
                           'sample_ids':split['sample_ids'],'class_ids':bundle['class_ids'],
                           'image_features':images,'text_features':tf}
    finally:model.train(previous)
    return out


def native_admission(model,bundle,device):
    """Match complete locked cached features/scores before any training step."""
    with model.native():result=evaluate(model,bundle,device)
    checks={}
    for name,actual in result.items():
        split=bundle['evaluations'][name]
        expected={'image_features':split['native_image'],'text_features':bundle['native_text'],
                  'scores':split['native_image']@bundle['native_text'].T}
        checks[name]={}
        for key,reference in expected.items():
            value=actual[key]
            if value.shape!=reference.shape or value.dtype!=reference.dtype or not torch.isfinite(value).all() or not torch.isfinite(reference).all():
                raise ValueError('Native admission shape/dtype/finiteness mismatch: '+name+'.'+key)
            if not torch.allclose(value,reference,atol=2e-6,rtol=0):
                raise ValueError('Native admission exceeds atol2e-6/rtol0: '+name+'.'+key)
            checks[name][key]={'max_abs':float((value-reference).abs().max()),'shape':list(value.shape)}
    return result,{'status':'NATIVE_SOURCE_ROUTE_PARITY_PASS','atol':2e-6,'rtol':0,
                   'evaluation_batch_size':32,'score_product_device':'cpu','checks':checks,
                   'meaning':'Technical source arithmetic admission only, not scientific result acceptance.'}


def train(config_path,output,device,resume=False):
    """Run only when invoked explicitly by the parent. Never invoked by CPU tests."""
    import transformers
    from transformers import CLIPModel
    path=Path(config_path).resolve();c=json.loads(path.read_text(encoding='utf-8-sig'));validate_config(c)
    root=path.parent;output=Path(output).resolve()
    if output.exists() and not resume:raise ValueError('Output already exists; refuse to overwrite')
    if resume and not (output/'latest.pt').is_file():raise ValueError('Resume checkpoint missing')
    model_path=checked_assets(c,root)
    bundle_path=(root/c['data_path']).resolve()
    if sha256(bundle_path)!=c['data_sha256']:raise ValueError('Input bundle SHA mismatch')
    bundle=torch.load(bundle_path,map_location='cpu',weights_only=True);validate_bundle(bundle,c)
    expected_classes={'dtd':47,'cifar100':100}[c['dataset']]
    if len(bundle['class_ids'])!=expected_classes or len(bundle['train']['sample_ids'])!=2000:
        raise ValueError('Production inputs must match the replacement 2000-image source protocol')
    if output.is_relative_to(model_path):
        raise ValueError('Output cannot be inside the immutable foundation model directory')
    # No silent external data acquisition or pretrained fallback.
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    torch.set_num_threads(c['cpu_threads']);torch.use_deterministic_algorithms(c['deterministic_algorithms'])
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    random.seed(c['seed']);np.random.seed(c['seed']);torch.manual_seed(c['seed'])
    if str(device).startswith('cuda'):torch.cuda.manual_seed_all(c['seed'])
    base=CLIPModel.from_pretrained(model_path,local_files_only=True,weights_only=True,
                                  attn_implementation='eager',dtype=torch.float32,use_safetensors=False)
    validate_production_base(base)
    model=rt.MethodCLIP(base,c['arm']).to(device)
    rt.bind_frozen(model,digest_json(c['model_assets']))
    n=len(bundle['train']['sample_ids']);steps_per_epoch=math.ceil(n/32)
    o=c['optimizer'];opt,sch=rt.optimizers(model,steps_per_epoch*4,weight_decay=o['weight_decay'],betas=tuple(o['betas']),eps=o['eps'])
    identity=dict(rt.producer_signature(),config=c,config_sha256=digest_json(c),
                  reference_cache_keys=c['reference_cache_keys'],device=str(device))
    native_scores,native_receipt=native_admission(model,bundle,device)
    epoch=step=cursor=0;order=[]
    if resume:
        state=torch.load(output/'latest.pt',map_location='cpu',weights_only=False)
        progress=rt.restore(state,model,opt,sch,identity)
        epoch,step,cursor,order=(progress[k] for k in ('epoch','step','cursor','order'))
        if not 0<=epoch<=4 or not 0<=cursor<=n or (order and sorted(order)!=list(range(n))):
            raise ValueError('Invalid sampler progress')
        if step!=epoch*steps_per_epoch+(math.ceil(cursor/32) if cursor else 0):
            raise ValueError('Sampler/optimizer progress mismatch')
    else:
        output.mkdir(parents=True)
        (output/'Identity.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
        (output/'NativeAdmission.json').write_text(json.dumps(native_receipt,indent=2),encoding='utf-8')
        atomic_save(native_scores,output/'native_scores.pt')
        atomic_save(evaluate(model,bundle,device),output/'epoch000_scores.pt')
        initial=rt.capture(model,opt,sch,identity,epoch=0,step=0,cursor=0,order=[])
        atomic_save(initial,output/'epoch000.pt');atomic_save(initial,output/'latest.pt')
    text={k:v.to(device) for k,v in bundle['text'].items()}
    native_text=bundle['native_text'].to(device);train_split=bundle['train']
    model.train()
    while epoch<4:
        if not order:order=epoch_order(n,c['seed'],epoch+1)
        while cursor<n:
            idx=order[cursor:cursor+32]
            pixels=train_split['pixels'][idx].to(device);labels=train_split['labels'][idx].to(device)
            refs={'image':train_split['native_image'][idx].to(device),'text':native_text}
            opt.zero_grad(set_to_none=True)
            scores=model(pixels,text,refs)
            loss=torch.nn.functional.cross_entropy(scores.float(),labels)
            if not torch.isfinite(loss):raise FloatingPointError('Nonfinite loss')
            loss.backward()
            for name,p in model.named_parameters():
                if p.requires_grad and (p.grad is None or not torch.isfinite(p.grad).all()):
                    raise FloatingPointError('Missing or nonfinite gradient: '+name)
            opt.step();sch.step();step+=1;cursor+=len(idx)
            if should_commit(math.ceil(cursor/32),steps_per_epoch):
                atomic_save(rt.capture(model,opt,sch,identity,epoch=epoch,step=step,cursor=cursor,order=order),output/'latest.pt')
        epoch+=1;cursor=0;order=[]
        atomic_save(evaluate(model,bundle,device),output/f'epoch{epoch:03}_scores.pt')
        saved=rt.capture(model,opt,sch,identity,epoch=epoch,step=step,cursor=cursor,order=order)
        atomic_save(saved,output/f'epoch{epoch:03}.pt');atomic_save(saved,output/'latest.pt')
    frozen_final=rt.verify_frozen_final(model)
    manifest={p.name:sha256(p) for p in output.iterdir() if p.is_file() and p.name!='Completion.json'}
    (output/'Completion.json').write_text(json.dumps({'status':'TRAINING_COMPLETE_PENDING_INDEPENDENT_SCIENTIFIC_REVIEW',
                                                    'identity_sha256':digest_json(identity),'frozen_final_verification':frozen_final,'files':manifest},indent=2),encoding='utf-8')


def validate_transfer(bundle,config):
    required={'schema','task','source','reference_cache_keys','class_ids','text','native_text','samples'}
    if set(bundle)!=required or bundle['schema']!='A1_NEW_METHOD_TRANSFER_V1':
        raise ValueError('Explicit transfer bundle schema required')
    if bundle['source'] not in ('imagenet','flickr') or bundle['task'] not in ('classification','paired_retrieval'):
        raise ValueError('Unsupported transfer task/source')
    if (bundle['source']=='imagenet')!=(bundle['task']=='classification'):
        raise ValueError('Transfer task/source mismatch')
    expected=(5000,1000) if bundle['source']=='imagenet' else (512,512)
    if (len(bundle['samples']['sample_ids']),len(bundle['class_ids']))!=expected:
        raise ValueError('Transfer cohort size mismatch')
    keys=bundle['reference_cache_keys']
    if set(keys)!={'native_model','preprocessing','image_sample_order','text_candidate_order'}:
        raise ValueError('Transfer reference inventory mismatch')
    if keys['native_model']!=config['reference_cache_keys']['native_model'] or keys['preprocessing']!=config['reference_cache_keys']['preprocessing']:
        raise ValueError('Transfer native model/preprocessing changed')
    if keys['image_sample_order']!=digest_json(bundle['samples']['sample_ids']):
        raise ValueError('Transfer reference image mapping changed')
    if keys['text_candidate_order']!=digest_json({'class_ids':bundle['class_ids'],
                                                'text':{k:v.tolist() for k,v in sorted(bundle['text'].items())}}):
        raise ValueError('Transfer reference candidate mapping changed')
    if set(bundle['samples'])!={'pixels','labels','sample_ids','native_image'}:
        raise ValueError('Transfer sample inventory mismatch')
    ids=bundle['samples']['sample_ids'];classes=bundle['class_ids'];text=bundle['text']
    if len(set(ids))!=len(ids) or len(set(classes))!=len(classes):raise ValueError('Duplicate transfer identities')
    if set(text) not in ({'input_ids','attention_mask'},{'input_ids','attention_mask','position_ids'}):
        raise ValueError('Missing transfer tokens/mask')
    shape=text['input_ids'].shape
    if len(shape)!=2 or shape[0]!=len(classes):raise ValueError('Transfer token mapping mismatch')
    for k,value in text.items():
        if value.device.type!='cpu' or value.dtype!=torch.long or value.shape!=shape:raise ValueError('Invalid transfer text '+k)
    x=bundle['samples']['pixels'];y=bundle['samples']['labels']
    if x.device.type!='cpu' or x.dtype!=torch.float32 or x.ndim!=4 or x.shape[:2]!=(len(ids),3) or not torch.isfinite(x).all():
        raise ValueError('Invalid transfer pixels')
    if y.device.type!='cpu' or y.dtype!=torch.long or y.shape!=(len(ids),) or (y<0).any() or (y>=len(classes)).any():
        raise ValueError('Transfer target mapping mismatch')
    if bundle['task']=='paired_retrieval' and not torch.equal(y,torch.arange(512)):
        raise ValueError('Flickr one-caption pairing must follow explicit row order')
    _features(bundle['native_text'],len(classes));_features(bundle['samples']['native_image'],len(ids))


def evaluate_checkpoint(config_path,checkpoint_path,checkpoint_sha256,bundle_path,bundle_sha256,output,device):
    """Independent transfer inference, not optimizer or historical-runtime replay."""
    from transformers import CLIPModel
    config_path=Path(config_path).resolve()
    c=json.loads(config_path.read_text(encoding='utf-8-sig'));validate_config(c)
    if sha256(checkpoint_path)!=checkpoint_sha256 or sha256(bundle_path)!=bundle_sha256:
        raise ValueError('Checkpoint/transfer bundle SHA mismatch')
    output=Path(output).resolve()
    if output.exists():raise ValueError('Transfer output already exists')
    model_path=checked_assets(c,config_path.parent)
    bundle=torch.load(bundle_path,map_location='cpu',weights_only=True);validate_transfer(bundle,c)
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    base=CLIPModel.from_pretrained(model_path,local_files_only=True,weights_only=True,
                                  attn_implementation='eager',dtype=torch.float32,use_safetensors=False)
    validate_production_base(base)
    model=rt.MethodCLIP(base,c['arm']).to(device)
    rt.bind_frozen(model,digest_json(c['model_assets']))
    state=torch.load(checkpoint_path,map_location='cpu',weights_only=False)
    rt.restore_for_inference(state,model,digest_json(c),expected_producer=rt.producer_signature(),expected_config=c)
    adapted={'text':bundle['text'],'native_text':bundle['native_text'],
             'class_ids':bundle['class_ids'],'evaluations':{bundle['source']:bundle['samples']}}
    scores=evaluate(model,adapted,device)
    frozen_final=rt.verify_frozen_final(model)
    output.mkdir(parents=True)
    atomic_save(scores,output/'scores.pt')
    receipt={'status':'TRANSFER_INFERENCE_COMPLETE_PENDING_SCIENTIFIC_REVIEW',
             'checkpoint_sha256':checkpoint_sha256,'bundle_sha256':bundle_sha256,
             'frozen_final_verification':frozen_final,
             'reference_cache_keys':bundle['reference_cache_keys'],'task':bundle['task'],
             'device':str(device),'source_training_device':state['identity'].get('device'),
             'runtime_sha256':sha256(Path(__file__).with_name('runtime.py')),
             'scores_sha256':sha256(output/'scores.pt'),
             'restoration':'Inference parameters/buffers only; not optimizer/RNG or historical backend replay.'}
    (output/'Receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--device',choices=['cpu','cuda'],required=True)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--evaluate-only',action='store_true')
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--checkpoint-sha256')
    parser.add_argument('--evaluation-bundle',type=Path)
    parser.add_argument('--evaluation-sha256')
    parser.add_argument('--validate-only',action='store_true',help='Check explicit config only; no weights or input arrays loaded')
    a=parser.parse_args()
    if a.validate_only:
        validate_config(json.loads(a.config.read_text(encoding='utf-8-sig')));print('CONFIG_VALID_ONLY_NOT_SCIENCE_READY');return
    if a.output is None:parser.error('--output required')
    if a.evaluate_only:
        if a.resume or not all((a.checkpoint,a.checkpoint_sha256,a.evaluation_bundle,a.evaluation_sha256)):
            parser.error('Transfer requires checkpoint/bundle and their SHA256, without --resume')
        evaluate_checkpoint(a.config,a.checkpoint,a.checkpoint_sha256,a.evaluation_bundle,a.evaluation_sha256,a.output,a.device)
    else:
        if any((a.checkpoint,a.checkpoint_sha256,a.evaluation_bundle,a.evaluation_sha256)):
            parser.error('Transfer arguments require --evaluate-only')
        train(a.config,a.output,a.device,a.resume)

if __name__=='__main__':main()
