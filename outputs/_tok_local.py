
import os, sys, json
os.chdir(r"""D:\Realdesktop\Wan\Important\New""")
sys.path.insert(0, r"""D:\Realdesktop\Wan\Important\New""")
from transformers import CLIPTokenizerFast
tk = CLIPTokenizerFast.from_pretrained(r"""D:\Realdesktop\Wan\Important\New\models\clip-vit-base-patch32""", local_files_only=True)
ids = tk("a photo of a dog", return_tensors="pt")["input_ids"]
res = {
    "vocab_size": int(tk.vocab_size),
    "model_max_length": int(tk.model_max_length),
    "token_ids": ids.tolist()[0][:14],
    "n_tokens": int(ids.shape[1]),
}
# caption as provided by the dataset
from src.dataset import create_dataloaders
loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                  batch_size=8, max_samples=200)
b = next(iter(loader))
res["caption_0"] = str(b["caption"][0])[:80]
res["input_ids_0"] = b["input_ids"][0].tolist()[:16]
res["input_ids_shape"] = list(b["input_ids"].shape)
res["attention_sum_0"] = int(b["attention_mask"][0].sum())
res["n_unique_captions_in_batch"] = len(set(str(c) for c in b["caption"]))
print(json.dumps(res, indent=1))
