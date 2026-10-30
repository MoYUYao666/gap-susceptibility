"""构建 instruction 文本 + 真实图像 的 2x2 组合数据集(20 样本, 与参考协议同构)。"""
import pandas as pd

src = pd.read_parquet('paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet').head(20)
rows = []
for i, s in src.iterrows():
    rows.append({
        'instruction': s.get('instruction', ''),
        'input': s.get('input', ''),
        'output': s.get('output', ''),
        'image': '%04d.jpg' % (i - src.index[0]),
    })
df = pd.DataFrame(rows)
df.to_parquet('paper3/train-instr-00000.parquet')
print('rows', len(df))
print(df[['instruction', 'image']].head(3).to_string())
import os
print('imgs exist:', all(os.path.exists(os.path.join('data/marine_captions', im)) for im in df['image']))
