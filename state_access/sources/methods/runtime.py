"""Independent CLIP method runtime. Native attention forward is never replaced.

Projection hooks rotate actual q/k before the installed attention reshapes them.
Consequently the installed backend remains responsible for masks, scaling and v.
"""
import contextlib
import hashlib
import json
import math
import random
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ARMS = ('router-static', 'router-input', 'rope-fixed', 'rope-learned')


def normalize(output):
    x = output if isinstance(output, torch.Tensor) else output.pooler_output
    x = x.float()
    if x.ndim != 2 or not torch.isfinite(x).all() or (x.norm(dim=-1) == 0).any():
        raise ValueError('Invalid projected feature')
    return F.normalize(x, dim=-1)


class Router(nn.Module):
    def __init__(self, conditional):
        super().__init__()
        self.a = nn.Parameter(torch.zeros(12))
        self.U = nn.Parameter(torch.zeros(12,512), requires_grad=conditional)

    def forward(self, features):
        if features.ndim != 2 or features.shape[1] != 512 or not torch.isfinite(features).all():
            raise ValueError('Native references must be finite [batch,512] features')
        if not torch.allclose(features.norm(dim=-1), torch.ones_like(features[:,0]), atol=2e-5, rtol=0):
            raise ValueError('Native references must be normalized')
        return 12 * (self.a + F.linear(features.detach(),self.U)).softmax(-1)


class LoRA(nn.Module):
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.A = nn.Parameter(torch.empty(8,base.in_features))
        self.B = nn.Parameter(torch.zeros(base.out_features,8))
        nn.init.kaiming_uniform_(self.A,a=math.sqrt(5))
        self.register_buffer('scale',torch.tensor(2.))
        self.enabled = True
        self.route = None

    def forward(self,x):
        out = self.base(x)
        if self.enabled:
            delta = F.linear(F.linear(x,self.A),self.B) * self.scale
            if self.route is not None:
                delta = delta * self.route[:,None,None]
            out = out + delta
        return out


class Rotary(nn.Module):
    def __init__(self, layer, learned):
        super().__init__()
        if not 1 <= layer <= 12:
            raise ValueError('Layer numbering must be one through twelve')
        initial = 1 - .5*layer/12
        self.register_buffer('initial_alpha',torch.tensor(initial))
        self.register_buffer('inverse_frequency',10000**(-2*torch.arange(32,dtype=torch.float32)/64))
        self.w = nn.Parameter(torch.logit(torch.tensor((initial-.1)/1.9)), requires_grad=learned)
        self.enabled = True
        self.positions = None

    @property
    def alpha(self):
        return .1+1.9*self.w.sigmoid()

    def forward(self,x,positions=None):
        if not self.enabled:
            return x
        if x.ndim != 3 or x.shape[-1] % 64:
            raise ValueError('Expected flattened heads of dimension64')
        b,t,d=x.shape
        p = positions if positions is not None else self.positions
        if p is None:
            p=torch.arange(t,device=x.device)
        p=p.to(x.device)
        if p.ndim == 1:
            p=p.unsqueeze(0)
        if p.shape[-1] != t or p.shape[0] not in (1,b):
            raise ValueError('Original token position shape mismatch')
        angle=p[...,None,None].to(x.dtype)*self.alpha.to(x.dtype)*self.inverse_frequency.to(x.dtype)
        c,s=angle.cos(),angle.sin()
        heads=x.reshape(b,t,-1,64)
        even,odd=heads[...,0::2],heads[...,1::2]
        return torch.stack((even*c-odd*s,even*s+odd*c),dim=-1).reshape(b,t,d)


class MethodCLIP(nn.Module):
    def __init__(self,clip,arm):
        super().__init__()
        if arm not in ARMS:
            raise ValueError('Unknown arm')
        if clip.config.projection_dim != 512:
            raise ValueError('Projected native feature dimension must be512')
        self.clip,self.arm=clip,arm
        self.routers=nn.ModuleDict()
        self.rotaries=nn.ModuleDict()
        self.handles=[]
        self.routing_override=None
        for p in clip.parameters(): p.requires_grad_(False)
        for name,tower in (('text',clip.text_model),('vision',clip.vision_model)):
            if len(tower.encoder.layers)!=12:
                raise ValueError('Both towers must contain twelve layers')
            if arm.startswith('router'):
                self.routers[name]=Router(arm=='router-input')
            for i,layer in enumerate(tower.encoder.layers):
                attn=layer.self_attn
                if attn.head_dim!=64:
                    raise ValueError('Attention head dimension must be64')
                for key in ('q_proj','k_proj','v_proj'):
                    setattr(attn,key,LoRA(getattr(attn,key)))
                if arm.startswith('rope'):
                    key=f'{name}_{i}'
                    self.rotaries[key]=Rotary(i+1,arm=='rope-learned')
                    # Bind the module, not the loop variable. Both hooks share it.
                    rotary=self.rotaries[key]
                    def hook(module, args, output, rotary=rotary):
                        return rotary(output)
                    self.handles.extend([attn.q_proj.register_forward_hook(hook),
                                         attn.k_proj.register_forward_hook(hook)])

    @contextlib.contextmanager
    def native(self):
        modules=[m for m in self.modules() if isinstance(m,(LoRA,Rotary))]
        old=[m.enabled for m in modules]
        try:
            for m in modules: m.enabled=False
            yield
        finally:
            for m,v in zip(modules,old): m.enabled=v

    @contextlib.contextmanager
    def routing_intervention(self,mode,means=None):
        if not self.routers or mode not in ('uniform','calibration-mean'):
            raise ValueError('Invalid routing intervention')
        if mode=='calibration-mean':
            if means is None or set(means)!={'vision','text'}:
                raise ValueError('Both calibration means required')
            for value in means.values():
                if value.shape!=(12,) or not torch.isfinite(value).all() or (value<0).any() or abs(value.sum().item()-12)>2e-5:
                    raise ValueError('Invalid calibration mean weights')
        old=self.routing_override
        self.routing_override=(mode,means)
        try: yield
        finally: self.routing_override=old

    @contextlib.contextmanager
    def _context(self,tower,reference,positions=None):
        route=None
        layers=getattr(self.clip,tower+'_model').encoder.layers
        adaptation_enabled=any(getattr(layer.self_attn,key).enabled
                               for layer in layers for key in ('q_proj','k_proj','v_proj'))
        if tower in self.routers and adaptation_enabled:
            if reference is None:
                raise ValueError('Frozen native references required for routing')
            route=self.routers[tower](reference)
            if self.routing_override is not None:
                mode,means=self.routing_override
                route=(torch.ones_like(route) if mode=='uniform' else
                       means[tower].detach().to(route).unsqueeze(0).expand_as(route))
        try:
            for i,layer in enumerate(layers):
                for key in ('q_proj','k_proj','v_proj'):
                    getattr(layer.self_attn,key).route=route[:,i] if route is not None else None
                key=f'{tower}_{i}'
                if key in self.rotaries: self.rotaries[key].positions=positions
            yield
        finally:
            for i,layer in enumerate(layers):
                for key in ('q_proj','k_proj','v_proj'):
                    getattr(layer.self_attn,key).route=None
                key=f'{tower}_{i}'
                if key in self.rotaries: self.rotaries[key].positions=None

    def image_features(self,pixels,reference=None):
        patch=self.clip.config.vision_config.patch_size
        if self.arm.startswith('rope') and (pixels.shape[-2]//patch,pixels.shape[-1]//patch)!=(7,7):
            raise ValueError('Vision RoPE requires CLS plus49 patches')
        with self._context('vision',reference):
            return normalize(self.clip.get_image_features(pixel_values=pixels,return_dict=True))

    def text_features(self,text,reference=None):
        with self._context('text',reference,text.get('position_ids')):
            return normalize(self.clip.get_text_features(**text,return_dict=True))

    def forward(self,pixels,text,references=None):
        refs=references or {}
        return self.image_features(pixels,refs.get('image')) @ self.text_features(text,refs.get('text')).T


class Schedules:
    """Only frequency multipliers use cosine; LoRA and routing stay constant."""
    def __init__(self,optimizer,total_steps):
        if total_steps<=0: raise ValueError('Positive total_steps required')
        self.optimizer,self.total_steps,self.steps=optimizer,total_steps,0
    def step(self):
        self.steps+=1
        if self.steps>self.total_steps: raise ValueError('Scheduler exhausted')
        for group in self.optimizer.param_groups:
            group['lr']=group['initial_lr']*(.5*(1+math.cos(math.pi*self.steps/self.total_steps))
                                           if group['role']=='frequency' else 1.)
    def state_dict(self): return {'steps':self.steps,'total_steps':self.total_steps}
    def load_state_dict(self,state):
        if set(state)!={'steps','total_steps'} or state['total_steps']!=self.total_steps or not 0<=state['steps']<=self.total_steps:
            raise ValueError('Scheduler identity mismatch')
        self.steps=state['steps']
        for group in self.optimizer.param_groups:
            expected=group['initial_lr']*(.5*(1+math.cos(math.pi*self.steps/self.total_steps)) if group['role']=='frequency' else 1.)
            if group['lr']!=expected: raise ValueError('Optimizer/scheduler LR mismatch')


def optimizers(model,total_steps,*,weight_decay,betas,eps):
    if weight_decay!=.01 or tuple(betas)!=(.9,.999) or eps!=1e-8:
        raise ValueError('Locked AdamW recipe cannot be overridden')
    ordinary=[]; frequency=[]
    for key,p in model.named_parameters():
        if p.requires_grad:
            (frequency if key.startswith('rotaries.') and key.endswith('.w') else ordinary).append(p)
    groups=[{'params':ordinary,'lr':5e-4,'initial_lr':5e-4,'weight_decay':weight_decay,'role':'adapter_router'}]
    if frequency: groups.append({'params':frequency,'lr':1e-5,'initial_lr':1e-5,'weight_decay':0.,'role':'frequency'})
    optimizer=torch.optim.AdamW(groups,betas=betas,eps=eps,foreach=False,fused=False)
    return optimizer,Schedules(optimizer,total_steps)


def tensor_digest(values):
    digest=hashlib.sha256()
    for key,value in sorted(values.items()):
        t=value.detach().cpu().contiguous()
        digest.update(key.encode());digest.update(str((tuple(t.shape),t.dtype)).encode())
        digest.update(t.numpy().tobytes())
    return digest.hexdigest()


def _frozen(model):
    return {k:p for k,p in model.named_parameters() if not p.requires_grad}


def _parameter_guard(values):
    # Metadata only: no device synchronization, tensor clone, or D2H transfer.
    return {key:(id(p),p._version,p.data_ptr(),p.storage_offset(),tuple(p.shape),
                 tuple(p.stride()),str(p.dtype),str(p.device),p.requires_grad)
            for key,p in values.items()}


def bind_frozen(model,foundation_assets_sha256=None):
    """Bind once AFTER device/dtype setup. Cached guards never enter state_dict.

    PyTorch in-place mutations, replacement, requires_grad and storage changes
    fail at capture. Raw .data writes can bypass version counters; a mandatory
    final full-content recheck catches them before a completion receipt.
    """
    values=_frozen(model)
    guard=_parameter_guard(values)
    buffers=dict(model.named_buffers())
    buffer_guard=_parameter_guard(buffers)
    old=getattr(model,'_frozen_binding',None)
    if old is not None:
        if guard!=old['guard'] or buffer_guard!=old['buffer_guard']:
            raise ValueError('Frozen parameter version/storage/inventory changed')
        if foundation_assets_sha256 is not None and old['foundation_assets_sha256']!=foundation_assets_sha256:
            raise ValueError('Foundation asset binding changed')
        return old
    digest=tensor_digest(values)
    if _parameter_guard(_frozen(model))!=guard:
        raise ValueError('Frozen parameters changed during initial hashing')
    if _parameter_guard(dict(model.named_buffers()))!=buffer_guard:
        raise ValueError('Fixed buffers changed during initial hashing')
    result={'guard':guard,'buffer_guard':buffer_guard,
            'buffer_values':{k:v.detach().cpu().clone() for k,v in buffers.items()},
            'sha256':digest,'foundation_assets_sha256':foundation_assets_sha256,
            'manifest':{k:{'shape':list(p.shape),'dtype':str(p.dtype)} for k,p in values.items()}}
    model._frozen_binding=result
    return result


def verify_frozen_final(model):
    """Full D2H-content recheck at closeout, never at every eight-step snapshot."""
    bound=bind_frozen(model)
    digest=tensor_digest(_frozen(model))
    bind_frozen(model)  # Check versions again after the full copy/hash.
    if digest!=bound['sha256']:
        raise ValueError('Final frozen-content hash mismatch')
    for key,value in model.named_buffers():
        if not torch.equal(value.detach().cpu(),bound['buffer_values'][key]):
            raise ValueError('Final fixed-buffer content mismatch: '+key)
    return {'frozen_sha256':digest,'foundation_assets_sha256':bound['foundation_assets_sha256'],
            'status':'FULL_CONTENT_RECHECK_PASS'}


def capture(model,optimizer,scheduler,identity,*,epoch,step,cursor,order):
    # Only local trusted checkpoints may be loaded with weights_only=False.
    if model.routing_override is not None or any(not m.enabled for m in model.modules() if isinstance(m,(LoRA,Rotary))):
        raise ValueError('Cannot checkpoint an intervention context')
    if any(m.route is not None for m in model.modules() if isinstance(m,LoRA)):
        raise ValueError('Cannot checkpoint an active forward context')
    bound=bind_frozen(model)
    return {'schema':'A1_NEW_METHOD_STATE_V1','arm':model.arm,'identity':json.loads(json.dumps(identity)),
            'trainable':{k:p.detach().cpu().clone() for k,p in model.named_parameters() if p.requires_grad},
            'buffers':{k:p.detach().cpu().clone() for k,p in model.named_buffers()},
            'fixed_method_parameters':{k:p.detach().cpu().clone() for k,p in _frozen(model).items() if k.startswith(('routers.','rotaries.'))},
            'frozen_manifest':__import__('copy').deepcopy(bound['manifest']),
            'frozen_sha256':bound['sha256'],
            'optimizer':__import__('copy').deepcopy(optimizer.state_dict()),'scheduler':scheduler.state_dict(),
            'rng':{'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),
                   'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None},
            'progress':{'epoch':epoch,'step':step,'cursor':cursor,'order':list(order)},
            'training':model.training}


def _validate_state(state,model,identity):
    required={'schema','arm','identity','trainable','buffers','frozen_manifest','frozen_sha256',
              'optimizer','scheduler','rng','progress','training','fixed_method_parameters'}
    if set(state)!=required or state['schema']!='A1_NEW_METHOD_STATE_V1' or state['arm']!=model.arm or state['identity']!=identity:
        raise ValueError('State schema or identity mismatch')
    fixed={k:p for k,p in _frozen(model).items() if k.startswith(('routers.','rotaries.'))}
    if set(fixed)!=set(state['fixed_method_parameters']):
        raise ValueError('Fixed method inventory mismatch')
    for k,p in fixed.items():
        if not torch.equal(p.detach().cpu(),state['fixed_method_parameters'][k]):
            raise ValueError('Fixed method value mismatch: '+k)
    params={k:p for k,p in model.named_parameters() if p.requires_grad}
    buffers=dict(model.named_buffers())
    manifest={k:{'shape':list(p.shape),'dtype':str(p.dtype)} for k,p in _frozen(model).items()}
    bound=bind_frozen(model)
    if manifest!=state['frozen_manifest'] or bound['sha256']!=state['frozen_sha256']:
        raise ValueError('Frozen state identity mismatch')
    for actual,saved in ((params,state['trainable']),(buffers,state['buffers'])):
        if set(actual)!=set(saved): raise ValueError('Tensor inventory mismatch')
        for k,p in actual.items():
            v=saved[k]
            if p.shape!=v.shape or p.dtype!=v.dtype or not torch.isfinite(v).all():
                raise ValueError('Tensor shape/dtype/value mismatch: '+k)
            if actual is buffers and not torch.equal(p.detach().cpu(),v):
                raise ValueError('Fixed buffer value mismatch: '+k)
    return params,buffers


def restore(state,model,optimizer,scheduler,identity):
    params,buffers=_validate_state(state,model,identity)
    progress=state['progress'];schedule=state['scheduler']
    if set(progress)!={'epoch','step','cursor','order'} or any(type(progress[k]) is not int or progress[k]<0 for k in ('epoch','step','cursor')):
        raise ValueError('Progress schema mismatch')
    if set(schedule)!={'steps','total_steps'} or progress['step']!=schedule['steps'] or schedule['total_steps']!=scheduler.total_steps or not 0<=schedule['steps']<=schedule['total_steps']:
        raise ValueError('Progress/scheduler mismatch')
    saved_opt=state['optimizer'];current_opt=optimizer.state_dict()
    if set(saved_opt)!={'state','param_groups'} or len(saved_opt['param_groups'])!=len(current_opt['param_groups']):
        raise ValueError('Optimizer schema mismatch')
    ids=[];ordered_params=[]
    for saved,current,actual in zip(saved_opt['param_groups'],current_opt['param_groups'],optimizer.param_groups):
        if set(saved)!=set(current):raise ValueError('Optimizer group inventory mismatch')
        for key in current:
            expected=current[key]
            if key=='lr':
                expected=current['initial_lr']*(.5*(1+math.cos(math.pi*schedule['steps']/schedule['total_steps'])) if current['role']=='frequency' else 1.)
            if saved[key]!=expected:raise ValueError('Optimizer setting mismatch: '+key)
        ids.extend(saved['params']);ordered_params.extend(actual['params'])
    if set(saved_opt['state'])!=(set(ids) if progress['step'] else set()):
        raise ValueError('Incomplete optimizer moments')
    for key,parameter in zip(ids,ordered_params):
        if not progress['step']:break
        item=saved_opt['state'][key]
        if set(item)!={'step','exp_avg','exp_avg_sq'} or item['step'].numel()!=1 or item['step'].item()!=progress['step']:
            raise ValueError('Optimizer step inventory mismatch')
        for name in ('exp_avg','exp_avg_sq'):
            if item[name].shape!=parameter.shape or item[name].dtype!=parameter.dtype or not torch.isfinite(item[name]).all():
                raise ValueError('Invalid optimizer moment: '+name)
        if (item['exp_avg_sq']<0).any():raise ValueError('Negative second moment')
    rng=state['rng']
    if set(rng)!={'python','numpy','torch','cuda'}:raise ValueError('RNG inventory mismatch')
    random.Random().setstate(rng['python']);np.random.RandomState().set_state(rng['numpy'])
    torch.Generator(device='cpu').set_state(rng['torch'])
    if rng['cuda'] is not None and not torch.cuda.is_available():raise ValueError('CUDA RNG cannot be restored on CPU')
    with torch.no_grad():
        for k,p in params.items(): p.copy_(state['trainable'][k].to(p.device))
    optimizer.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler'])
    random.setstate(state['rng']['python']);np.random.set_state(state['rng']['numpy'])
    torch.set_rng_state(state['rng']['torch'])
    if state['rng']['cuda'] is not None:
        if not torch.cuda.is_available(): raise ValueError('CUDA RNG cannot be restored on CPU')
        torch.cuda.set_rng_state_all(state['rng']['cuda'])
    model.train(state['training'])
    return state['progress']


def producer_signature():
    """Independently measured local forward/optimizer semantics, never state claims."""
    import inspect
    import platform
    from pathlib import Path
    import transformers
    from transformers.models.clip.modeling_clip import CLIPAttention
    def file_sha(path):
        with Path(path).open('rb') as stream:
            return hashlib.file_digest(stream,'sha256').hexdigest()
    return {'runtime_sha256':file_sha(__file__),
            'runner_sha256':file_sha(Path(__file__).with_name('runner.py')),
            'attention_source_sha256':file_sha(inspect.getfile(CLIPAttention)),
            'software':{'torch':torch.__version__,'transformers':transformers.__version__,
                        'numpy':np.__version__,'python':platform.python_version()},
            'implementation_contract':{'adamw_foreach':False,'adamw_fused':False,
                                       'evaluation_batch_size':32,'score_product_device':'cpu',
                                       'score_product':'concatenated_float32_features_unscaled_cosine'}}


def restore_for_inference(state,model,expected_config_sha256,*,expected_producer=None,expected_config=None):
    """Validate full tensor inventories; do not pretend to resume optimizer/RNG."""
    identity=state.get('identity',{})
    current=producer_signature()
    if expected_producer!=current:
        raise ValueError('Explicit current producer signature required; no self-declared migration')
    if any(identity.get(key)!=value for key,value in current.items()):
        raise ValueError('Inference producer/attention/software/implementation mismatch')
    if not isinstance(expected_config,dict):
        raise ValueError('Explicit inference training recipe required')
    calculated=hashlib.sha256(json.dumps(expected_config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if identity.get('config_sha256')!=expected_config_sha256 or calculated!=expected_config_sha256 or identity.get('config')!=expected_config:
        raise ValueError('Inference checkpoint configuration mismatch')
    if identity.get('reference_cache_keys')!=expected_config.get('reference_cache_keys',{}):
        raise ValueError('Inference source reference cache mismatch')
    if identity.get('device') not in ('cpu','cuda'):
        raise ValueError('Unknown source execution device')
    params,buffers=_validate_state(state,model,identity)
    with torch.no_grad():
        for key,p in params.items():p.copy_(state['trainable'][key].to(p.device))
    model.eval()
