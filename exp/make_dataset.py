"""第二数据集准备 — 转成 Alpaca parquet 格式（与 run_training.py 兼容）

用法：
  # 1. 下载 ShareGPT（或 WizardLM）原始数据
  # 2. 转换：
  python exp/make_dataset.py --input sharegpt.json --output /root/autodl-tmp/dataset.parquet

说明：
  - ShareGPT 格式: [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]
  - Alpaca 格式:   {"instruction": "...", "input": "", "output": "..."}
  - 只取单轮对话（第一轮 human/gpt），与 Alpaca 实验设置一致
"""
import json, argparse, pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help='ShareGPT/WizardLM JSON 路径')
parser.add_argument('--output', default='/root/autodl-tmp/dataset.parquet',
                    help='输出 parquet 路径')
parser.add_argument('--max-samples', type=int, default=2000,
                    help='最多取多少条（实验用 16-256 即可）')
args = parser.parse_args()

def convert_sharegpt(data):
    """ShareGPT → Alpaca 格式（单轮）。"""
    records = []
    for item in data:
        convs = item.get('conversations', item if isinstance(item, list) else [])
        if isinstance(convs, list) and convs:
            # 取第一轮 human→gpt
            human = next((c['value'] for c in convs if c.get('from') == 'human'), None)
            gpt = next((c['value'] for c in convs if c.get('from') == 'gpt'), None)
            if human and gpt:
                records.append({'instruction': human, 'input': '', 'output': gpt})
    return records

def convert_wizardlm(data):
    """WizardLM → Alpaca 格式。"""
    records = []
    for item in data:
        if isinstance(item, dict) and 'instruction' in item:
            records.append({
                'instruction': item.get('instruction', ''),
                'input': item.get('input', ''),
                'output': item.get('output', ''),
            })
    return records

def main():
    with open(args.input, encoding='utf-8') as f:
        data = json.load(f)

    # 自动检测格式
    if isinstance(data, list) and data and 'conversations' in data[0]:
        records = convert_sharegpt(data)
        print(f'ShareGPT 格式: {len(records)} 条单轮对话')
    elif isinstance(data, list) and data and 'instruction' in data[0]:
        records = convert_wizardlm(data)
        print(f'WizardLM 格式: {len(records)} 条')
    else:
        print('无法识别格式，请确认是 ShareGPT 或 WizardLM JSON')
        return

    records = records[:args.max_samples]
    df = pd.DataFrame(records)
    df.to_parquet(args.output)
    print(f'保存: {args.output} ({len(df)} 条)')
    print(f'字段: {list(df.columns)}')
    print('示例:', df.iloc[0]['instruction'][:80], '→', df.iloc[0]['output'][:80])

if __name__ == '__main__':
    main()
