"""Build the captioning task-family parquet (real images + real captions, 20 samples, isomorphic to the reference protocol)."""
import json
import pandas as pd

caps = json.load(open('data/marine_captions/captions.json', encoding='utf-8'))['captions']
df = pd.DataFrame([{'instruction': 'Describe the image.', 'input': '', 'output': cap,
                    'image': '%04d.jpg' % i} for i, cap in enumerate(caps[:20])])
df.to_parquet('paper3/train-caption-00000.parquet')
print('rows', len(df))
print(df[['image', 'output']].head(3).to_string())
