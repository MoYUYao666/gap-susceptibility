# -*- coding: utf-8 -*-
r"""Make the text sequence length backbone-aware so SigLIP can run.

SigLIP's text tower caps `max_position_embeddings` at 64 while the data pipeline pads to CLIP's 77, which killed all
fifteen SigLIP arms before training (`ValueError: Sequence length must be less than max_position_embeddings`).
Fix: the trainer derives the limit from the loaded model's text config (capped at 77), records it in `self.max_seq_len`
and exports `PEFT_MAX_SEQ_LEN`; the dataset reads that variable instead of the hardcoded 77. CLIP-family backbones keep
77, so no existing result changes.
"""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

# ---------------------------------------------------------------- trainer: derive the limit
P = "src/trainer.py"
t = io.open(P, encoding="utf-8").read()
ANCHOR = """        self.processor = _Proc.from_pretrained(
            self.train_cfg.clip_model
        )"""
ADD = ANCHOR + """
        # Backbone-aware text length: SigLIP caps positions at 64, CLIP at 77. The dataset reads this variable.
        _tc = getattr(self.model.config, "text_config", None)
        _maxpos = getattr(_tc, "max_position_embeddings", None) if _tc is not None else None
        self.max_seq_len = int(min(77, _maxpos)) if _maxpos else 77
        os.environ["PEFT_MAX_SEQ_LEN"] = str(self.max_seq_len)
        print(f"text sequence length: {self.max_seq_len}")"""
if "PEFT_MAX_SEQ_LEN" not in t:
    assert ANCHOR in t, "trainer anchor missing"
    t = t.replace(ANCHOR, ADD, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(t)
    print("trainer patched: backbone-aware max_seq_len")
else:
    print("trainer already carries PEFT_MAX_SEQ_LEN")

# ---------------------------------------------------------------- dataset: use it
D = "src/dataset.py"
td = io.open(D, encoding="utf-8").read()
OLD = "max_length=77,"
NEW = 'max_length=int(os.environ.get("PEFT_MAX_SEQ_LEN", "77")),'
if OLD in td:
    assert "import os" in td, "dataset.py has no os import"
    td = td.replace(OLD, NEW)
    io.open(D, "w", encoding="utf-8", newline="\n").write(td)
    print("dataset patched: max_length from PEFT_MAX_SEQ_LEN")
elif "PEFT_MAX_SEQ_LEN" in td:
    print("dataset already patched")
else:
    raise SystemExit("max_length anchor missing in dataset.py")

for f in ("src/trainer.py", "src/dataset.py"):
    src = io.open(f, encoding="utf-8").read()
    assert "PEFT_MAX_SEQ_LEN" in src, f
print("both files verified")
