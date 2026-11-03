"""
BLIP-2 交叉验证实验 — Phase 3
==============================
验证核心发现跨架构泛化（dual-encoder → Q-Former cross-attention）

实验配置（7个）：
  B1: BLIP-2 frozen — 初始 Gap 测量 + Q-Former 架构适配
  B2: BLIP-2 full_ft (Q-Former) — 全量微调灾难验证
  B3: BLIP-2 LoRA rank sweep (rank=4, 8, 16)
  B4: BLIP-2 LoRA position (text_only, both)

降级路线（8GB 显存不够时）：
  → blip2-opt-350m (~1.4GB, 替代 2.7b)
  → BLIP-1 双塔 (Salesforce/blip-image-captioning-base)
  → 仅跑 frozen + text_only 两个关键实验

用法:
    python blip2_experiments.py --data_dir ./data --max_samples 5000 --epochs 5
"""

import os, sys, json, time, argparse
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from src.config import ExperimentConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders


# ============================================================
# 模型选择（按显存能力自动降级）
# ============================================================

BLIP2_MODEL_27B = "Salesforce/blip2-opt-2.7b"
BLIP2_MODEL_350M = "Salesforce/blip2-opt-350m"
BLIP1_MODEL = "./models/blip-image-captioning-base"  # 本地路径

BLIP2_EXPERIMENTS = [
    # B1: 冻结基线
    ("b1_blip2_frozen", "frozen", None, None),

    # B2: 全量微调 Q-Former
    ("b2_blip2_full_ft", "full_ft", None, None),

    # B3: LoRA rank sweep (仅 text encoder + Q-Former cross-attention)
    ("b3_blip2_lora_r4", "lora",
     LoRAConfig(rank=4, alpha=8, apply_to_vision=False, apply_to_text=True), None),

    ("b3_blip2_lora_r8", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True), None),

    ("b3_blip2_lora_r16", "lora",
     LoRAConfig(rank=16, alpha=32, apply_to_vision=False, apply_to_text=True), None),

    # B4: LoRA position
    ("b4_blip2_lora_text_only", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True), None),

    ("b4_blip2_lora_both", "lora",
     LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=True), None),
]


# ============================================================
# BLIP-2 模型加载 & 包装
# ============================================================

def detect_model_size(args) -> str:
    """根据显存选择性加载 BLIP-2 模型大小"""
    if args.force_350m:
        return BLIP2_MODEL_350M
    if args.force_blip1:
        return BLIP1_MODEL

    if torch.cuda.is_available():
        gpu_mem_gb = torch.cuda.get_device_properties(0).total_mem / 1024**3
        if gpu_mem_gb < 10:
            print(f"⚠️ GPU 显存 {gpu_mem_gb:.1f}GB < 10GB，降级到 {BLIP2_MODEL_350M}")
            return BLIP2_MODEL_350M
    else:
        # CPU 模式更有理由用小模型
        print(f"⚠️ CPU 模式，使用 {BLIP2_MODEL_350M}")
        return BLIP2_MODEL_350M

    return BLIP2_MODEL_27B


def load_blip2_model(model_name: str, args):
    """
    加载 BLIP-2（支持 4-bit 量化和 gradient checkpointing）

    BLIP-2 架构:
      - Vision Encoder: ViT (冻结)
      - Q-Former: BERT-based cross-attention (可微调)
      - LLM: OPT (冻结，可选不加载)

    对于 embedding 提取，我们使用 Q-Former 的输出。
    """
    print(f"\n📦 加载 BLIP-2 模型: {model_name}")

    # 尝试 4-bit 量化加载
    if args.use_4bit:
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            print("   使用 4-bit 量化加载")
        except ImportError:
            print("   ⚠️ bitsandbytes 不可用，使用标准加载")
            bnb_config = None
    else:
        bnb_config = None

    from transformers import Blip2Processor, Blip2Model

    try:
        if bnb_config:
            model = Blip2Model.from_pretrained(
                model_name, local_files_only=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                quantization_config=bnb_config,
            )
        else:
            model = Blip2Model.from_pretrained(
                model_name, local_files_only=True,
            )

        processor = Blip2Processor.from_pretrained(model_name, local_files_only=True)
    except Exception as e:
        print(f"❌ BLIP-2 加载失败: {e}")
        print(f"   尝试降级到 BLIP-1 ({BLIP1_MODEL})...")
        return load_blip1_model(args)

    # 启用 gradient checkpointing（省显存）
    if args.use_gradient_checkpointing:
        try:
            model.qformer.gradient_checkpointing_enable()
            print("   Gradient checkpointing 已启用")
        except Exception:
            print("   ⚠️ Gradient checkpointing 不适用于此模型版本")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 BLIP-2 参数量: {total_params:,}")

    return model, processor


def load_blip1_model(args):
    """
    备选: BLIP-1 双塔模型（纯 dual-encoder，架构更接近 CLIP）
    """
    from transformers import BlipProcessor, BlipModel

    print(f"📦 加载 BLIP-1: {BLIP1_MODEL}")
    model = BlipModel.from_pretrained(BLIP1_MODEL, local_files_only=True)
    processor = BlipProcessor.from_pretrained(BLIP1_MODEL, local_files_only=True)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 BLIP-1 参数量: {total_params:,}")

    return model, processor


class BLIP2EmbeddingWrapper(nn.Module):
    """
    将 BLIP-2/3 的输出包装为 CLIP 风格的 embedding 接口

    适配策略:
    - image_embeds: Q-Former image query 的输出 (pooled representation)
    - text_embeds: Q-Former text 的输出
    """

    def __init__(self, blip_model, model_type: str = "blip2"):
        super().__init__()
        self.blip = blip_model
        self.model_type = model_type

        # 注册 vision_model 和 text_model 属性（trainer compatibility）
        if model_type == "blip2":
            self.vision_model = blip_model.vision_model if hasattr(blip_model, 'vision_model') else None
            self.qformer = blip_model.qformer if hasattr(blip_model, 'qformer') else None
            self.text_model = None  # BLIP-2 没有独立的 text encoder
            self.logit_scale = nn.Parameter(torch.tensor(2.6592))  # CLIP 默认 logit_scale
        elif model_type == "blip1":
            self.vision_model = blip_model.vision_model if hasattr(blip_model, 'vision_model') else None
            self.text_model = blip_model.text_decoder if hasattr(blip_model, 'text_decoder') else None
            self.logit_scale = nn.Parameter(torch.tensor(2.6592))

        self._embed_dim = blip_model.config.qformer_config.hidden_size \
            if (hasattr(blip_model.config, 'qformer_config') and model_type == "blip2") \
            else 768  # BLIP-1 默认

    def forward(self, pixel_values=None, input_ids=None, attention_mask=None, **kwargs):
        """
        统一 forward 为 CLIP 风格，返回 image_embeds 和 text_embeds
        """
        if self.model_type == "blip2":
            return self._forward_blip2(pixel_values, input_ids, attention_mask, **kwargs)
        else:
            return self._forward_blip1(pixel_values, input_ids, attention_mask, **kwargs)

    def _forward_blip2(self, pixel_values, input_ids, attention_mask, **kwargs):
        """BLIP-2 forward: 提取 Q-Former 的 image/text embedding"""
        outputs = self.blip(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
            return_dict=True,
        )

        # Q-Former 输出结构:
        # outputs.qformer_outputs: (image_output, text_output, ...)
        # image_output: (B, num_query_tokens, hidden)
        # text_output: (B, seq_len, hidden)
        image_embeds = None
        text_embeds = None

        if hasattr(outputs, 'qformer_outputs') and outputs.qformer_outputs is not None:
            qformer_out = outputs.qformer_outputs
            # image_output 是第一个元素（通常）
            if isinstance(qformer_out, tuple) and len(qformer_out) >= 1:
                image_hidden = qformer_out[0]  # (B, num_query, hidden)
                if isinstance(image_hidden, torch.Tensor):
                    image_embeds = image_hidden.mean(dim=1)  # pooled
            if isinstance(qformer_out, tuple) and len(qformer_out) >= 2:
                text_hidden = qformer_out[1]  # (B, seq_len, hidden)
                if isinstance(text_hidden, torch.Tensor):
                    # 取 EOS token 或 mean
                    if attention_mask is not None:
                        eos_idx = attention_mask.sum(dim=1) - 1
                        eos_idx = torch.clamp(eos_idx, min=0)
                        text_embeds = text_hidden[torch.arange(text_hidden.shape[0]), eos_idx]
                    else:
                        text_embeds = text_hidden.mean(dim=1)

        # Fallback: 用 image_features/text_features（如果有）
        if image_embeds is None and hasattr(outputs, 'image_embeds'):
            image_embeds = outputs.image_embeds
        if text_embeds is None and hasattr(outputs, 'text_embeds'):
            text_embeds = outputs.text_embeds

        # 最终 fallback
        if image_embeds is None:
            image_embeds = torch.zeros(pixel_values.shape[0], self._embed_dim,
                                       device=pixel_values.device)
        if text_embeds is None:
            text_embeds = torch.zeros(input_ids.shape[0], self._embed_dim,
                                      device=input_ids.device)

        return BLIP2Output(image_embeds, text_embeds, outputs)

    def _forward_blip1(self, pixel_values, input_ids, attention_mask, **kwargs):
        """BLIP-1 forward: 双塔输出"""
        outputs = self.blip(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )

        image_embeds = outputs.image_embeds if hasattr(outputs, 'image_embeds') else None
        text_embeds = outputs.text_embeds if hasattr(outputs, 'text_embeds') else None

        if image_embeds is None:
            image_embeds = torch.zeros(pixel_values.shape[0], 768, device=pixel_values.device)
        if text_embeds is None:
            text_embeds = torch.zeros(input_ids.shape[0], 768, device=input_ids.device)

        return BLIP2Output(image_embeds, text_embeds, outputs)


class BLIP2Output:
    """模拟 CLIPOutput 的接口"""
    def __init__(self, image_embeds, text_embeds, raw_outputs):
        self.image_embeds = image_embeds
        self.text_embeds = text_embeds
        self.raw_outputs = raw_outputs


# ============================================================
# 单实验运行
# ============================================================

def run_one_blip2(args, name, peft_method, lora_cfg, model, processor) -> dict:
    """运行单个 BLIP-2 实验"""
    print(f"\n{'='*60}")
    print(f"🔬 BLIP-2: {name}")
    print(f"   PEFT: {peft_method}")
    print(f"{'='*60}")

    # BLIP-2 用较小 batch_size 和 epochs（模型大）
    config = ExperimentConfig(
        name=name,
        peft_method=peft_method,
        lora=lora_cfg if lora_cfg else LoRAConfig(rank=0),
        train=TrainConfig(
            dataset=args.dataset,
            clip_model="openai/clip-vit-base-patch32",  # 占位，已被 model 替换
            device="cuda" if torch.cuda.is_available() else "cpu",
            batch_size=args.batch_size,
            num_epochs=args.epochs if peft_method != "frozen" else 1,
            max_samples=args.max_samples,
            save_dir=f"{args.outputs_dir}/{name}",
            gradient_accumulation_steps=(
                args.grad_accum if peft_method == "full_ft"
                else 1
            ),
            learning_rate=args.lr,
        ),
    )

    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name=args.dataset,
        data_dir=args.data_dir,
        batch_size=config.train.batch_size,
        max_samples=config.train.max_samples,
        pre_tokenize=False,  # BLIP-1 用自有 tokenizer，不能预 tokenize
    )

    # 包装模型为 CLIP 兼容接口
    class Blip1Wrapper(nn.Module):
        def __init__(self, blip_model):
            super().__init__()
            self.blip = blip_model
            self.vision_model = blip_model.vision_model
            self.text_model = blip_model.text_model   # ← LoRA 注入需要
            self.logit_scale = nn.Parameter(torch.tensor(2.6592))

        def forward(self, pixel_values, input_ids, attention_mask, **kw):
            vis_raw = self.blip.get_image_features(pixel_values=pixel_values)
            ie = vis_raw.pooler_output
            ie = F.normalize(ie, p=2, dim=-1)

            txt_raw = self.blip.get_text_features(input_ids=input_ids, attention_mask=attention_mask)
            te = txt_raw.pooler_output
            te = F.normalize(te, p=2, dim=-1)

            return type('Out', (), {'image_embeds': ie, 'text_embeds': te})()

    wrapped_model = Blip1Wrapper(model)
    # model_type 仅用于记录
    _model_type = "blip1" if "blip-image-captioning" in args.model_name else "blip2"

    # 创建 trainer 并手动设置 model（跳过 CLIP 加载）
    trainer = GapAwareTrainer(config)

    # 替换 trainer 的 setup_model 以使用预加载的 BLIP-2
    original_setup = trainer.setup_model
    def blip2_setup():
        trainer.model = wrapped_model
        trainer.processor = processor
        total_params = sum(p.numel() for p in trainer.model.parameters())
        print(f"📊 BLIP-2 参数量: {total_params:,}")

        # 全部先冻结
        for p in trainer.model.parameters():
            p.requires_grad = False

        # BLIP-1 不支持 apply_lora_to_model，改用选择性解冻
        unfrozen = 0
        if peft_method == "lora" and lora_cfg is not None and lora_cfg.rank > 0:
            for n, m in trainer.model.named_modules():
                if isinstance(m, nn.Linear):
                    base = n.split('.')[-1]
                    if lora_cfg.apply_to_text and 'text_model' in n and base in ('query', 'value'):
                        m.requires_grad_(True)
                        unfrozen += 1
                    elif lora_cfg.apply_to_vision and 'vision_model' in n and base in ('query', 'value'):
                        m.requires_grad_(True)
                        unfrozen += 1

        elif peft_method == "full_ft":
            for p in trainer.model.parameters():
                p.requires_grad = True

        trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
        print(f"   可训练: {unfrozen} 层, {trainable:,} 参数 ({trainable/total_params*100:.2f}%)")

        trainer.model = trainer.model.to(trainer.device)
        trainer.model.train()
        print(f"✅ BLIP-2 模型准备完成 (设备: {trainer.device})")

    trainer.setup_model = blip2_setup
    result = trainer.train(train_loader, val_loader)

    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    result["test_metrics"] = test_metrics

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
    parser.add_argument("--data_dir", type=str, default=".")
    parser.add_argument("--outputs_dir", type=str, default="./outputs/blip2")
    parser.add_argument("--dataset", type=str, default="flickr30k")
    parser.add_argument("--batch_size", type=int, default=16,
                       help="BLIP-2 较大，需要较小 batch_size")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--max_samples", type=int, default=5000,
                       help="BLIP-2 慢，用较少样本验证即可")
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--grad_accum", type=int, default=4,
                       help="full_ft 时梯度累积步数")
    parser.add_argument("--model_name", type=str, default="auto",
                       help="BLIP-2 模型名称或 'auto' 自动选择")
    parser.add_argument("--force_350m", action="store_true",
                       help="强制使用 blip2-opt-350m")
    parser.add_argument("--force_blip1", action="store_true",
                       help="强制使用 BLIP-1 双塔（备选）")
    parser.add_argument("--use_4bit", action="store_true",
                       help="使用 4-bit 量化")
    parser.add_argument("--use_gradient_checkpointing", action="store_true",
                       help="使用 gradient checkpointing")
    parser.add_argument("--skip_full_ft", action="store_true",
                       help="跳过全量微调（省时间）")
    parser.add_argument("--quick", action="store_true",
                       help="快速验证：仅跑 frozen + text_only")
    args = parser.parse_args()

    # 模型选择
    if args.model_name == "auto":
        if args.force_blip1:
            args.model_name = BLIP1_MODEL
        else:
            args.model_name = detect_model_size(args)

    # 检查模型缓存
    try:
        from transformers.utils.hub import cached_file
        cached_file(args.model_name, "config.json")
        print(f"✅ 模型已缓存: {args.model_name}")
    except Exception:
        print(f"⚠️ 模型未缓存: {args.model_name}")
        print("   如果网络受限，请先下载后拷贝到 models/ 目录")

    # 加载模型（所有实验共享）
    model, processor = load_blip2_model(args.model_name, args)

    total_start = time.time()
    results = {}

    experiments_to_run = BLIP2_EXPERIMENTS
    if args.quick:
        experiments_to_run = [
            ("b1_blip2_frozen", "frozen", None, None),
            ("b4_blip2_lora_text_only", "lora",
             LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True), None),
        ]
        print("⚡ 快速模式: 仅运行 frozen + text_only")

    for name, peft_method, lora_cfg, _adapter_cfg in experiments_to_run:
        if args.skip_full_ft and "full_ft" in name:
            print(f"⏭ 跳过 {name}（全量微调）")
            continue

        # 检查是否已完成
        save_path = f"{args.outputs_dir}/{name}/results.json"
        if os.path.exists(save_path):
            print(f"⏭ 跳过 {name}（已完成）")
            with open(save_path) as f:
                results[name] = json.load(f)
            continue

        start = time.time()
        try:
            result = run_one_blip2(args, name, peft_method, lora_cfg, model, processor)
            results[name] = result
            elapsed = time.time() - start

            r1 = result.get("test_metrics", {}).get("R@1", "N/A")
            cg_delta = None
            if result.get("initial_gap") and result.get("final_gap"):
                cg_delta = result["final_gap"]["centroid_gap"] - result["initial_gap"]["centroid_gap"]
            print(f"   ✅ {name}: R@1={r1}, CG Δ={cg_delta}, time={elapsed:.0f}s")
        except Exception as e:
            print(f"   ❌ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            results[name] = {"error": str(e)}

    total = time.time() - total_start
    print(f"\n🎉 BLIP-2 实验完成！总耗时: {total/60:.0f} 分钟")

    # ---- 汇总 ----
    print("\n" + "=" * 60)
    print("📊 BLIP-2 核心发现验证")
    print("=" * 60)
    for name, result in results.items():
        if "error" in result:
            print(f"   ❌ {name}: {result['error']}")
            continue
        cg_init = result.get("initial_gap", {}).get("centroid_gap")
        cg_final = result.get("final_gap", {}).get("centroid_gap")
        if cg_init and cg_final:
            delta = cg_final - cg_init
            r1 = result.get("test_metrics", {}).get("R@1", "N/A")
            marker = "✅" if delta < 0 else ("⚠️" if delta == 0 else "❌")
            print(f"   {marker} {name:<40s} CG Δ={delta:+.4f}  R@1={r1}")

    # 保存汇总
    os.makedirs(args.outputs_dir, exist_ok=True)
    with open(f"{args.outputs_dir}/blip2_summary.json", 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 汇总: {args.outputs_dir}/blip2_summary.json")


if __name__ == "__main__":
    main()
