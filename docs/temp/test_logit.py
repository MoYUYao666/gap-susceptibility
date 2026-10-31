import os; os.environ.pop("HF_HUB_OFFLINE",None); os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import open_clip
m,_,_=open_clip.create_model_and_transforms("ViT-B-32",pretrained="laion2b_s34b_b79k")
print("logit_scale:", hasattr(m,"logit_scale"))
print("logit_bias:", hasattr(m,"logit_bias"))
for n,_ in m.named_parameters():
    if "logit" in n.lower(): print("Found:",n)
