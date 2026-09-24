"""
SigLIP 交叉验证实验 — Phase 2
=============================
验证核心发现跨训练范式泛化（CLIP contrastive loss → SigLIP sigmoid loss）

实验配置（8个）：
  S1: SigLIP frozen — 初始 Gap 测量
  S2: SigLIP full_ft — 全量微调灾难验证
  S3: SigLIP LoRA rank sweep (rank=4, 8, 16)
  S4: SigLIP LoRA position (text_only, both)
  S5: SigLIP Adapter text_only — 新增：跨 PEFT 验证

故事线：SigLIP 用 sigmoid loss 做 pairwise similarity，与 CLIP InfoNCE
有本质区别。如果 text_only 也成立，说明发现不依赖训练目标。

用法:
    python siglip_experiments.py --data_dir ./data --max_samples 20000 --epochs 10
"""

import os, sys, json, time, argparse
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
import numpy as np

from src.config import ExperimentConfig, LoRAConfig, AdapterConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders


# ============================================================
# 实验定义
# ============================================================

SIGLIP_MODEL = "./models/siglip-base-patch16-224"
SIGLIP_IMAGE_SIZE = 224

SIGLIP_EXPERIMENTS = [
    # S1: 冻结基线
    ("s1_siglip_frozen", "frozen", None, None),

    # S3: LoRA rank sweep
    ("s3_siglip_lora_r4", "lora",
     LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True), None),
    ("s3_siglip_lora_r8", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True), None),
    ("s3_siglip_lora_r16", "lora",
     LoRAConfig(rank=16, alpha=32, apply_to_vision=True, apply_to_text=True), None),

    # S4: LoRA position
    ("s4_siglip_lora_text_only", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True), None),
    ("s4_siglip_lora_both", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True), None),

    # S5: Adapter text_only（跨 PEFT 验证）
    ("s5_siglip_adapter_text_only", "adapter", None,
     AdapterConfig(bottleneck_dim=16, apply_to_vision=False, apply_to_text=True)),
]


# ============================================================
# SigLIP 模型加载
# ============================================================

def load_siglip_model(model_name: str = SIGLIP_MODEL):
    """
    加载 SigLIP 模型

    SigLIP 与 CLIP 的关键差异:
    - SigLIP: sigmoid loss for pairwise similarity
    - CLIP: InfoNCE contrastive loss
    - SigLIP 输出有 logit_scale 和 logit_bias
    - Embedding 接口兼容: image_embeds / text_embeds（需验证）
    """
    from transformers import AutoModel, AutoProcessor

    print(f"\n📦 加载 SigLIP 模型: {model_name}")

    model = AutoModel.from_pretrained(model_name, local_files_only=True)
    processor = AutoProcessor.from_pretrained(model_name, local_files_only=True)

    # 检查输出接口
    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 SigLIP 参数量: {total_params:,}")

    # SigLIP 使用 VisionTransformer + T5Encoder，输出在 pooled_* 或 last_hidden_state
    # 验证 embedding 提取方式
    print(f"   架构类型: {type(model).__name__}")

    return model, processor


class SigLIPWrapper(torch.nn.Module):
    """
    SigLIP 模型包装器 — 统一 embedding 提取接口为 CLIP 风格

    SigLIPModel 输出:
    - vision_model_output: BaseModelOutput with last_hidden_state, pooler_output
    - text_model_output: BaseModelOutput with last_hidden_state, pooler_output
    """

    def __init__(self, siglip_model):
        super().__init__()
        self.siglip = siglip_model

    @property
    def logit_scale(self):
        return self.siglip.logit_scale

    @property
    def logit_bias(self):
        return self.siglip.logit_bias

    @property
    def vision_model(self):
        return self.siglip.vision_model

    @property
    def text_model(self):
        return self.siglip.text_model

    def get_image_features(self, pixel_values):
        """提取图像特征 (兼容 CLIP 接口)"""
        vision_outputs = self.siglip.vision_model(pixel_values=pixel_values)
        # pooler_output: (B, hidden_dim)
        if hasattr(vision_outputs, 'pooler_output') and vision_outputs.pooler_output is not None:
            return vision_outputs.pooler_output
        # fallback: mean of last_hidden_state
        return vision_outputs.last_hidden_state.mean(dim=1)

    def get_text_features(self, input_ids, attention_mask=None):
        """提取文本特征 (兼容 CLIP 接口)"""
        text_outputs = self.siglip.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        # pooler_output: (B, hidden_dim)
        if hasattr(text_outputs, 'pooler_output') and text_outputs.pooler_output is not None:
            return text_outputs.pooler_output
        # fallback: EOS token 或 mean pooling
        if attention_mask is not None:
            # 取 EOS token（最后非 padding 的位置）
            eos_idx = attention_mask.sum(dim=1) - 1
            return text_outputs.last_hidden_state[
                torch.arange(text_outputs.last_hidden_state.shape[0]), eos_idx
            ]
        return text_outputs.last_hidden_state.mean(dim=1)

    def forward(self, pixel_values=None, input_ids=None, attention_mask=None, **kwargs):
        """
        统一 forward 为 CLIP 风格: 返回 image_embeds 和 text_embeds
        """
        outputs = self.siglip(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs,
        )

        # SigLIP 输出有 loss, logits_per_image, logits_per_text 等
        image_embeds = outputs.image_embeds if hasattr(outputs, 'image_embeds') else None
        text_embeds = outputs.text_embeds if hasattr(outputs, 'text_embeds') else None

        if image_embeds is None:
            image_embeds = self.get_image_features(pixel_values)
        if text_embeds is None:
            text_embeds = self.get_text_features(input_ids, attention_mask)

        # 返回一个简单对象以匹配 CLIP 的输出格式
        return SigLIPOutput(image_embeds, text_embeds, outputs)


class SigLIPOutput:
    """模拟 CLIPOutput 的接口"""
    def __init__(self, image_embeds, text_embeds, raw_outputs):
        self.image_embeds = image_embeds
        self.text_embeds = text_embeds
        self.raw_outputs = raw_outputs


# ============================================================
# 单实验运行
# ============================================================

def run_one_siglip(args, name, peft_method, lora_cfg, adapter_cfg):
    """运行单个 SigLIP 实验"""
    print(f"\n{'='*60}")
    print(f"🔬 SigLIP: {name}")
    print(f"   PEFT: {peft_method}")
    print(f"{'='*60}")

    config = ExperimentConfig(
        name=name,
        peft_method=peft_method,
        lora=lora_cfg if lora_cfg else LoRAConfig(rank=0),
        adapter=adapter_cfg,
        train=TrainConfig(
            dataset=args.dataset,
            clip_model=SIGLIP_MODEL,
            device="cuda" if torch.cuda.is_available() else "cpu",
            batch_size=args.batch_size,
            num_epochs=args.epochs if peft_method != "frozen" else 1,
            max_samples=args.max_samples,
            save_dir=f"{args.outputs_dir}/{name}",
            gradient_accumulation_steps=4 if peft_method == "full_ft" else 1,
        ),
    )

    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name=args.dataset,
        data_dir=args.data_dir,
        batch_size=config.train.batch_size,
        max_samples=config.train.max_samples,
        pre_tokenize=False,  # SigLIP needs its own tokenizer, not CLIP's
    )

    # 加载 SigLIP 模型（本地位於 models/）
    siglip_model, siglip_processor = load_siglip_model(SIGLIP_MODEL)
    wrapped_model = SigLIPWrapper(siglip_model)

    # 创建 trainer 并 monkey-patch setup_model
    trainer = GapAwareTrainer(config)

    original_setup = trainer.setup_model
    def siglip_setup():
        trainer.model = wrapped_model.to(trainer.device)
        trainer.processor = siglip_processor  # trainer tokenization 用

        total_params = sum(p.numel() for p in trainer.model.parameters())
        print(f"📊 SigLIP 参数量: {total_params:,}")

        if peft_method == "lora" and lora_cfg is not None and lora_cfg.rank > 0:
            from lora import apply_lora_to_model
            trainer.model, trainer.lora_layers, trainable = apply_lora_to_model(
                trainer.model,
                rank=lora_cfg.rank,
                alpha=lora_cfg.alpha,
                dropout=lora_cfg.dropout,
                target_modules=lora_cfg.target_modules,
                apply_to_vision=lora_cfg.apply_to_vision,
                apply_to_text=lora_cfg.apply_to_text,
            )
            print(f"📊 可训练参数占比: {trainable/total_params*100:.2f}%")
        elif peft_method == "adapter" and adapter_cfg is not None:
            from peft_methods import apply_adapter_to_model
            trainer.model, trainer.adapter_layers, trainable = apply_adapter_to_model(
                trainer.model,
                bottleneck_dim=adapter_cfg.bottleneck_dim,
                activation=adapter_cfg.activation,
                apply_to_vision=adapter_cfg.apply_to_vision,
                apply_to_text=adapter_cfg.apply_to_text,
            )
        elif peft_method == "full_ft":
            print("⚠️ 全量微调模式")
            for p in trainer.model.parameters():
                p.requires_grad = True
        else:
            print("🔒 冻结模式")
            for p in trainer.model.parameters():
                p.requires_grad = False

        trainer.model = trainer.model.to(trainer.device)
        trainer.model.train()
        print(f"✅ SigLIP 模型准备完成 (设备: {trainer.device})")

    trainer.setup_model = siglip_setup
    trainer.max_seq_len = 64  # SigLIP max sequence length

    # 如果使用 gradient collection，在 full_ft 和 lora text_only 两种 key 实验上启用
    if args.collect_gradients and peft_method in ("lora", "full_ft"):
        trainer.enable_gradient_collection(collect_every_n_steps=50)

    result = trainer.train(train_loader, val_loader)

    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    result["test_metrics"] = test_metrics

    # 保存梯度快照
    if args.collect_gradients and trainer.gradient_snapshots:
        grad_path = f"{args.outputs_dir}/{name}/gradient_snapshots.json"
        os.makedirs(os.path.dirname(grad_path), exist_ok=True)
        with open(grad_path, 'w') as f:
            json.dump(trainer.gradient_snapshots, f, indent=2)

    # 保存结果
    save_path = f"{args.outputs_dir}/{name}/results.json"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=".",
                       help="数据根目录")
    parser.add_argument("--outputs_dir", type=str, default="./outputs/siglip")
    parser.add_argument("--dataset", type=str, default="flickr30k")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max_samples", type=int, default=20000)
    parser.add_argument("--skip_full_ft", action="store_true",
                       help="跳过全量微调（省时间/显存）")
    parser.add_argument("--collect_gradients", action="store_true",
                       help="启用梯度对齐分析收集")
    args = parser.parse_args()

    # 检查 SigLIP 模型是否已缓存
    from transformers.utils.hub import cached_file
    try:
        cached_file(SIGLIP_MODEL, "config.json")
        print(f"✅ SigLIP 模型已缓存: {SIGLIP_MODEL}")
    except Exception:
        print(f"⚠️ SigLIP 模型未缓存，将尝试下载: {SIGLIP_MODEL}")
        print("   如果网络受限，请先在其他环境下载后拷贝到 models/ 目录")

    total_start = time.time()
    results = {}

    for name, peft_method, lora_cfg, adapter_cfg in SIGLIP_EXPERIMENTS:
        if args.skip_full_ft and "full_ft" in name:
            print(f"⏭ 跳过 {name}（全量微调）")
            continue

        # Skip if already completed
        save_path = f"{args.outputs_dir}/{name}/results.json"
        if os.path.exists(save_path):
            print(f"⏭ 跳过 {name}（已完成）")
            with open(save_path, 'r') as f:
                results[name] = json.load(f)
            continue

        start = time.time()
        result = run_one_siglip(args, name, peft_method, lora_cfg, adapter_cfg)
        results[name] = result
        elapsed = time.time() - start

        r1 = result.get("test_metrics", {}).get("R@1", "N/A")
        cg_delta = None
        if result.get("initial_gap") and result.get("final_gap"):
            cg_delta = result["final_gap"]["centroid_gap"] - result["initial_gap"]["centroid_gap"]
        cg_str = f"{cg_delta:+.4f}" if cg_delta is not None else "N/A"
        print(f"   ✅ {name}: R@1={r1}, CG Δ={cg_str}, time={elapsed:.0f}s")

    total = time.time() - total_start
    print(f"\n🎉 SigLIP 实验完成！总耗时: {total/60:.0f} 分钟")

    # ---- 汇总验证 ----
    print("\n" + "=" * 60)
    print("📊 SigLIP 核心发现验证")
    print("=" * 60)

    for name, result in results.items():
        cg_init = result.get("initial_gap", {}).get("centroid_gap")
        cg_final = result.get("final_gap", {}).get("centroid_gap")
        if cg_init and cg_final:
            delta = cg_final - cg_init
            r1 = result.get("test_metrics", {}).get("R@1", "N/A")
            marker = "✅" if delta < 0 else ("⚠️" if delta == 0 else "❌")
            print(f"   {marker} {name:<40s} CG Δ={delta:+.4f}  R@1={r1}")

    # 保存汇总
    summary = {}
    for name, result in results.items():
        summary[name] = {
            "initial_cg": result.get("initial_gap", {}).get("centroid_gap"),
            "final_cg": result.get("final_gap", {}).get("centroid_gap"),
            "R@1": result.get("test_metrics", {}).get("R@1"),
            "train_loss": result.get("final_train_loss"),
        }

    os.makedirs(args.outputs_dir, exist_ok=True)
    with open(f"{args.outputs_dir}/siglip_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n📁 汇总: {args.outputs_dir}/siglip_summary.json")


if __name__ == "__main__":
    main()
