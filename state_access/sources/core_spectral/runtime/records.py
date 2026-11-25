"""Read-only locked inputs, path identities, finite protocol validation."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from model import MODES


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_document(value):
    if isinstance(value, dict):
        return value, hashlib.sha256(canonical(value)).hexdigest()
    path = Path(value)
    return json.loads(path.read_text(encoding='utf-8')), digest_file(path)


def resolve_inside(root, relative):
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError(f'Locked input path must be relative: {relative}')
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError(f'Input escapes root: {relative}')
    if not path.is_file():
        raise FileNotFoundError(f'Missing locked input: {path}')
    return path


def rgb_hash(image):
    image = image.convert('RGB')
    return hashlib.sha256(f'RGB:{image.width}:{image.height}:'.encode() + image.tobytes()).hexdigest()


def validate_source_quotas(dataset,classes):
    if len(dataset['class_names']) != classes:
        raise ValueError('Incorrect source candidate count')
    base,remainder = divmod(2000,classes)
    ranking = lambda k:hashlib.sha256(json.dumps([20261122,'remainder_class',k],separators=(',',':')).encode('utf-8')).hexdigest()
    extras = set(sorted(range(classes),key=ranking)[:remainder])
    expected_train = [base+int(k in extras) for k in range(classes)]
    for split,expected in [('train',expected_train),('calibration',[16]*classes),('test',[16]*classes)]:
        labels = [row['label'] for row in dataset['splits'][split]]
        if any(type(label) is not int or not 0<=label<classes for label in labels):
            raise ValueError('Source label outside exact candidate mapping')
        actual = [0]*classes
        for label in labels: actual[label]+=1
        if actual != expected:
            raise ValueError('Source stratified per-class quota mismatch: '+split)


def validate_protocol(protocol, lock):
    if protocol.get('schema_version') != 1 or lock.get('schema_version') != 1:
        raise ValueError('Only schema_version=1 is supported')
    if protocol.get('protocol_id') != 'A1_R1_REPLACEMENT_20261122_V1' or protocol['protocol_id'] != lock['protocol_id']:
        raise ValueError('Replacement protocol identity mismatch')
    exact = dict(seeds=[42,43,44],epochs=4,batch_size=32,
        learning_rate_by_mode=dict(lora_text=.001,lora_both=.0005),
        weight_decay=.01,lora_rank=8,lora_alpha_over_rank=2,
        lora_targets=['q_proj','k_proj','v_proj'],precision='float32',tf32=False,
        lora_A_initialization='kaiming_uniform_sqrt5',lora_B_initialization='zero',
        schedule='constant',training_score='unscaled_normalized_cosine',
        optimizer='AdamW',betas=[.9,.999],epsilon=1e-8,
        datasets=['dtd','cifar100','food101'],train_images_per_source=2000,
        calibration_per_class=16,test_per_class=16,sampling_seed=20261122,
        source_class_counts=dict(dtd=47,cifar100=100,food101=101),
        transfer_sizes=dict(imagenet=5000,flickr=512),candidate_counts=dict(imagenet=1000,flickr=512),
        margin_thresholds=[.01,.02],top_k=[3,5,10,20,50,100],
        tie_rule='smallest_candidate_index',native_and_initial_saved_separately=True,
        resampling=dict(unit='paired_seed_within_fixed_dataset',replicates=20000,
                        seed=20261121,interval='95_percentile'))
    for key,value in exact.items():
        if protocol.get(key) != value:
            raise ValueError(f'Unexpected replacement protocol field: {key}')
    if tuple(protocol['modes']) != MODES:
        raise ValueError('Only the two fixed replacement modes are supported')
    if set(lock['datasets']) != set(exact['datasets']) or set(lock['transfer']) != {'imagenet','flickr'}:
        raise ValueError('Replacement requires all three sources and both transfer views')


def validate_inputs(config, lock):
    """Verify before model loading; never consume transfer or eval labels."""
    protocol, _ = read_document(config['protocol'])
    validate_protocol(protocol, lock)
    if not config.get('smoke',False):
        if lock.get('formal_ready') is not True:
            raise ValueError('Formal three-source DataLock is not ready')
        if not lock.get('protocol_sha256'):
            raise ValueError('Formal DataLock must bind the exact protocol file')
        for name,classes in protocol['source_class_counts'].items():
            data = lock['datasets'][name]
            validate_source_quotas(data,classes)
            if len(data['class_names']) != classes:
                raise ValueError('Incorrect source candidate count: ' + name)
            for split,count in [('train',2000),('calibration',16*classes),('test',16*classes)]:
                if len(data['splits'][split]) != count:
                    raise ValueError('Incorrect locked source split size: ' + name + '/' + split)
        if lock['datasets']['cifar100']['class_names'][26] != 'crab':
            raise ValueError('Canonical CIFAR100 class 26 must be crab')
        for name,count in protocol['transfer_sizes'].items():
            if len(lock['transfer'][name]['rows']) != count or len(lock['transfer'][name]['texts']) != protocol['candidate_counts'][name]:
                raise ValueError('Incorrect transfer row or candidate count: ' + name)
    root = Path(config['root']).resolve()
    model_path = Path(config.get('model_path') or (root / lock['model']['path'])).resolve()
    if not model_path.is_dir():
        raise FileNotFoundError(f'Local locked model missing: {model_path}')
    files = lock['model']['files']
    required = {'config.json','preprocessor_config.json','tokenizer_config.json'}
    required.update({'tokenizer.json'} if (model_path/'tokenizer.json').is_file() else {'vocab.json','merges.txt'})
    if not required.issubset(files):
        raise ValueError('Missing consumed model/processor/tokenizer lock members')
    optional = {'added_tokens.json','special_tokens_map.json','chat_template.jinja','merges.txt','vocab.json'}
    optional.update(path.name for path in model_path.glob('*.json') if path.is_file())
    if any((model_path/name).is_file() and name not in files for name in optional):
        raise ValueError('Unlisted computation-affecting model/tokenizer override')
    if not files or 'config.json' not in files:
        raise ValueError('Model lock must include config.json and weights')
    for relative, expected in files.items():
        if digest_file(resolve_inside(model_path, relative)) != expected:
            raise ValueError(f'Model hash mismatch: {relative}')
    weights = [path for path in model_path.rglob('*') if path.is_file() and
               (path.suffix in ('.safetensors', '.bin') or path.name.endswith('.index.json'))]
    if not weights or any(path.relative_to(model_path).as_posix() not in files for path in weights):
        raise ValueError('Unlisted model weights or no locked weights')
    checked = {}

    def check_rows(rows):
        if not rows:
            raise ValueError('Empty locked row collection')
        identifiers, pixels = set(), set()
        for row in rows:
            if not isinstance(row['id'], str) or row['id'] in identifiers:
                raise ValueError('Duplicate or invalid row ID')
            identifiers.add(row['id'])
            path = resolve_inside(root, row['path'])
            signature = (str(path), row['sha256'], row['pixel_sha256'])
            if signature not in checked:
                if digest_file(path) != row['sha256']:
                    raise ValueError(f'Image byte hash mismatch: {path}')
                with Image.open(path) as image:
                    if rgb_hash(image) != row['pixel_sha256']:
                        raise ValueError(f'Image pixel hash mismatch: {path}')
                checked[signature] = True
            if row['pixel_sha256'] in pixels:
                raise ValueError('Duplicate image content within collection')
            pixels.add(row['pixel_sha256'])
        return identifiers, pixels

    training_sets = []
    for dataset in lock['datasets'].values():
        names = dataset['class_names']
        if len(names) < 2 or len(names) != len(set(names)):
            raise ValueError('Candidate class names must be unique and nonempty')
        if dataset['template'].count('{}') != 1:
            raise ValueError('Dataset template must contain exactly one {}')
        expected_texts = [dataset['template'].format(name.replace('_',' ')) for name in names]
        if dataset.get('texts',expected_texts) != expected_texts:
            raise ValueError('Locked source candidate texts differ from canonical class/template mapping')
        ids, hashes = set(), set()
        for split in ('train', 'calibration', 'test'):
            rows = dataset['splits'][split]
            new_ids, new_hashes = check_rows(rows)
            if ids & new_ids or hashes & new_hashes:
                raise ValueError('Train/calibration/test identity overlap')
            ids.update(new_ids)
            hashes.update(new_hashes)
            if split in ('train','calibration','test'):
                labels = [row['label'] for row in rows]
                if any(type(label) is not int or not 0 <= label < len(names) for label in labels):
                    raise ValueError('Source label outside exact candidate class mapping')
                if set(labels) != set(range(len(names))):
                    raise ValueError('A candidate class has no training images')
        if any(hashes & previous for previous in training_sets):
            raise ValueError('Independent datasets contain shared image content')
        training_sets.append(hashes)
    transfer_hashes = set()
    for name, view in lock['transfer'].items():
        _, pixels = check_rows(view['rows'])
        if any(pixels & hashes for hashes in training_sets) or pixels & transfer_hashes:
            raise ValueError('Transfer content overlaps training/evaluation or another transfer view')
        transfer_hashes.update(pixels)
        if not view['texts'] or any(not isinstance(text,str) or not text for text in view['texts']):
            raise ValueError('Missing exact candidate texts')
        if name == 'imagenet' and len(view['class_names']) != len(view['texts']):
            raise ValueError('ImageNet class/text mapping mismatch')
        if name == 'flickr' and (len(view['rows']) != len(view['texts']) or
                any(row['caption'] != text for row,text in zip(view['rows'],view['texts']))):
            raise ValueError('Flickr pairing mismatch')
    return protocol, model_path


def view_specs(lock, dataset):
    data = lock['datasets'][dataset]
    return {
        'calibration': dict(rows=data['splits']['calibration'],
                            texts=data.get('texts',[data['template'].format(name.replace('_',' ')) for name in data['class_names']]),
                            context_texts=data['class_names']),
        'test': dict(rows=data['splits']['test'],
                     texts=data.get('texts',[data['template'].format(name.replace('_',' ')) for name in data['class_names']]),
                     context_texts=data['class_names']),
        'imagenet': dict(rows=lock['transfer']['imagenet']['rows'],
                         texts=lock['transfer']['imagenet']['texts'],
                         context_texts=lock['transfer']['imagenet']['class_names']),
        'flickr': dict(rows=lock['transfer']['flickr']['rows'],
                       texts=lock['transfer']['flickr']['texts'],
                       context_texts=lock['transfer']['flickr']['texts'])}
