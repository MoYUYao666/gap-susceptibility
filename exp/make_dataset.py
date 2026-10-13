"""Second dataset preparation — convert to Alpaca parquet format (compatible with run_training.py)

Usage:
  # 1. Download the raw ShareGPT (or WizardLM) data
  # 2. Convert:
  python exp/make_dataset.py --input sharegpt.json --output /root/autodl-tmp/dataset.parquet

Notes:
  - ShareGPT format: [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]
  - Alpaca format:   {"instruction": "...", "input": "", "output": "..."}
  - Take only single-turn dialogue (the first human/gpt turn), consistent with the Alpaca experimental setup
"""
import json, argparse, pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help='ShareGPT/WizardLM JSON path')
parser.add_argument('--output', default='/root/autodl-tmp/dataset.parquet',
                    help='output parquet path')
parser.add_argument('--max-samples', type=int, default=2000,
                    help='maximum number of records to take (16-256 is enough for experiments)')
args = parser.parse_args()

def convert_sharegpt(data):
    """ShareGPT → Alpaca format (single turn)."""
    records = []
    for item in data:
        convs = item.get('conversations', item if isinstance(item, list) else [])
        if isinstance(convs, list) and convs:
            # take the first human→gpt turn
            human = next((c['value'] for c in convs if c.get('from') == 'human'), None)
            gpt = next((c['value'] for c in convs if c.get('from') == 'gpt'), None)
            if human and gpt:
                records.append({'instruction': human, 'input': '', 'output': gpt})
    return records

def convert_wizardlm(data):
    """WizardLM → Alpaca format."""
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

    # auto-detect format
    if isinstance(data, list) and data and 'conversations' in data[0]:
        records = convert_sharegpt(data)
        print(f'ShareGPT format: {len(records)} single-turn dialogues')
    elif isinstance(data, list) and data and 'instruction' in data[0]:
        records = convert_wizardlm(data)
        print(f'WizardLM format: {len(records)} records')
    else:
        print('Unrecognized format; please confirm it is ShareGPT or WizardLM JSON')
        return

    records = records[:args.max_samples]
    df = pd.DataFrame(records)
    df.to_parquet(args.output)
    print(f'Saved: {args.output} ({len(df)} records)')
    print(f'Fields: {list(df.columns)}')
    print('Example:', df.iloc[0]['instruction'][:80], '→', df.iloc[0]['output'][:80])

if __name__ == '__main__':
    main()
