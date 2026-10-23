from modelscope.hub.api import HubApi

api = HubApi()
cands = [
    "lmms-lab/LLaVA-OneVision-Qwen2-0.5B-Instruct",
    "AI-ModelScope/LLaVA-OneVision-Qwen2-0.5B-Instruct",
    "lmms-lab/llava-onevision-qwen2-0.5b-ov",
    "OpenGVLab/InternVL2-2B",
    "OpenGVLab/InternVL2-1B",
    "HuggingFaceTB/SmolVLM-500M-Instruct",
    "AI-ModelScope/SmolVLM-500M-Instruct",
    "Qwen/Qwen2-VL-2B-Instruct",
]
for repo in cands:
    try:
        files = api.get_model_files(repo)
        print(repo, "OK", len(files))
    except Exception as e:
        print(repo, "ERR", str(e)[:60])
