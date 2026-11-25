"""Download or verify the exact versioned project state shards, then safely extract."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import urllib.request
import zipfile

HERE=Path(__file__).resolve().parent
RELEASE='https://github.com/MoYUYao666/gap-susceptibility/releases/download/v3.5.1/'


def require(ok, message):
    if not ok: raise ValueError(message)


def identity(path):
    with Path(path).open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(bytes=Path(path).stat().st_size,sha256=digest)


def safe(name):
    p=PurePosixPath(name)
    require(name and not p.is_absolute() and ':' not in name and '\\' not in name and
            all(x not in ('','.','..') for x in name.split('/')), 'Unsafe archive path')
    return name


def verify_asset(path, shard):
    require(identity(path)=={k:shard[k] for k in ('bytes','sha256')},'Asset size/SHA mismatch: '+shard['name'])
    expected=shard['members']
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist(); names=[i.filename for i in infos]
        require(len(names)<=2000 and len(names)==len(set(n.casefold() for n in names)), 'Duplicate or excessive member count')
        require(set(names)==set(expected),'Unexpected/missing archive members')
        require(sum(i.file_size for i in infos)<=256*1024**2,'Shard expansion bound exceeded')
        for item in infos:
            safe(item.filename)
            require(not item.is_dir() and (item.external_attr>>16)&0o170000 != 0o120000,'Archive symlink/directory rejected')
            require(item.file_size==expected[item.filename]['bytes'],'Expanded size differs from index')
            with archive.open(item) as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
            require(digest==expected[item.filename]['sha256'],'Member SHA mismatch')
    return len(expected)


def fetch(shard, directory):
    target=directory/shard['name']
    if target.exists():
        verify_asset(target,shard);return target
    partial=target.with_suffix(target.suffix+'.partial')
    current=partial.stat().st_size if partial.exists() else 0
    require(current<=shard['bytes'],'Partial larger than expected')
    if current<shard['bytes']:
        headers={'User-Agent':'project-state-verification/3.5'}
        if current:headers['Range']='bytes='+str(current)+'-'
        request=urllib.request.Request(RELEASE+shard['name'],headers=headers)
        with urllib.request.urlopen(request,timeout=90) as response:
            require(response.status==(206 if current else 200),'Resume requires a verified range response')
            if current:require(response.headers.get('Content-Range','').startswith('bytes '+str(current)+'-'),'Wrong resume offset')
            require(int(response.headers.get('Content-Length','0'))==shard['bytes']-current,'Download length mismatch')
            with partial.open('ab' if current else 'xb') as stream:
                remaining=shard['bytes']-current
                while remaining:
                    block=response.read(min(4*1024**2,remaining))
                    require(block,'Truncated state asset');stream.write(block);remaining-=len(block)
                require(not response.read(1),'Download exceeded declared size')
    verify_asset(partial,shard);partial.rename(target)
    return target


def extract(paths,index,target):
    require(not target.exists(),'Extraction target must be new')
    all_names=[]
    for shard in index['shards']:
        verify_asset(paths/shard['name'],shard);all_names.extend(shard['members'])
    require(len(all_names)==len(set(x.casefold() for x in all_names)),'Cross-shard duplicate')
    require(sum(x['bytes'] for s in index['shards'] for x in s['members'].values())<=3*1024**3,'Total expansion bound')
    for name in all_names:
        require(not any(str(p).casefold() in {n.casefold() for n in all_names} for p in PurePosixPath(name).parents if str(p)!='.'),'Member prefix collision')
    target.mkdir(parents=True)
    for shard in index['shards']:
        with zipfile.ZipFile(paths/shard['name']) as archive:
            for name,expected in shard['members'].items():
                destination=target/safe(name)
                require(destination.resolve().is_relative_to(target.resolve()),'Extraction escaped target')
                destination.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(name) as source,destination.open('xb') as output:shutil.copyfileobj(source,output,4*1024**2)
                require(identity(destination)==expected,'Extracted file SHA changed')
    return len(all_names)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['download','verify','extract'])
    p.add_argument('--index',type=Path,default=HERE/'StateIndex.json')
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--jobs',type=int,default=4)
    args=p.parse_args();index=json.loads(args.index.read_text(encoding='utf-8'))
    require(index['version']=='3.5','Wrong index version')
    if args.action=='download':
        require(1<=args.jobs<=8,'Choose 1 to 8 parallel downloads')
        args.assets.mkdir(parents=True,exist_ok=True)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:list(pool.map(lambda s:fetch(s,args.assets),index['shards']))
    count=sum(verify_asset(args.assets/s['name'],s) for s in index['shards'])
    if args.action=='extract':
        require(args.output is not None,'--output required')
        count=extract(args.assets,index,args.output)
    print(json.dumps(dict(status='PASS_VERSION_BOUND_STATE_ASSETS',version='3.5',shards=len(index['shards']),members=count,models_restored=False)))


if __name__=='__main__':main()
