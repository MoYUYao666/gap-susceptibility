"""
数据加载模块 — Flickr30k, MS-COCO
适配 CLIP 训练格式: (image, text) 配对数据
"""

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import json
import os
from typing import List, Dict, Tuple, Optional


# ============================================================
# CLIP 标准预处理
# ============================================================

CLIP_MEAN = [0.48145466, 0.4578275, 0.40821073]
CLIP_STD = [0.26862954, 0.26130258, 0.27577711]


def get_clip_transform(image_size: int = 224, is_train: bool = True):
    """CLIP 标准图像预处理"""
    if is_train:
        return transforms.Compose([
            transforms.Resize((image_size, image_size), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD),
        ])


# ============================================================
# Flickr30k Dataset
# ============================================================

class Flickr30kDataset(Dataset):
    """
    Flickr30k 图文检索数据集

    预期目录结构:
        flickr30k/
        ├── flickr30k-images/
        │   ├── 1000092795.jpg
        │   └── ...
        └── flickr30k.json  (或 results_20130124.token)
            [{"image": "xxx.jpg", "captions": ["...", "...", ...]}, ...]
    """

    _tokenizer = None  # 类级别共享，避免多次加载

    def __init__(
        self,
        data_dir: str,
        split: str = "train",   # train, val, test
        image_size: int = 224,
        max_samples: Optional[int] = None,
        pre_tokenize: bool = True,  # 在 dataset 端预 tokenize，利用多 worker 并行
    ):
        self.data_dir = data_dir
        self.split = split
        self.image_size = image_size
        self.max_samples = max_samples
        self.pre_tokenize = pre_tokenize

        self.image_dir = os.path.join(data_dir, "flickr30k-images")
        self.transform = get_clip_transform(image_size, is_train=(split == "train"))

        # 加载 tokenizer（懒加载，共享）
        if pre_tokenize and Flickr30kDataset._tokenizer is None:
            from transformers import CLIPTokenizerFast
            Flickr30kDataset._tokenizer = CLIPTokenizerFast.from_pretrained(
                "openai/clip-vit-base-patch32", local_files_only=True
            )

        # 加载标注
        self.samples = self._load_annotations()

    def _load_annotations(self) -> List[Dict]:
        """加载并解析标注文件"""
        # 尝试多种格式
        csv_path = os.path.join(self.data_dir, "results.csv")
        json_path = os.path.join(self.data_dir, "flickr30k.json")
        token_path = os.path.join(self.data_dir, "results_20130124.token")

        samples = []

        # 优先尝试 CSV 格式 (pipe分隔: image_name | comment_number | comment)
        if os.path.exists(csv_path):
            import csv
            captions_by_image = {}
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')
                header = next(reader, None)  # 跳过表头
                for row in reader:
                    if len(row) >= 3:
                        image_file = row[0].strip()
                        caption = row[2].strip()
                        if image_file not in captions_by_image:
                            captions_by_image[image_file] = []
                        captions_by_image[image_file].append(caption)

            for image_file, captions in captions_by_image.items():
                for caption in captions:
                    samples.append({
                        "image": image_file,
                        "caption": caption,
                    })
            print(f"   📋 CSV格式 ({len(captions_by_image)} 图像, {len(samples)} 标注)")

        elif os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 每张图对应5条标注 → 展开为独立样本
            for item in data:
                image_file = item["image"]
                for caption in item["captions"]:
                    samples.append({
                        "image": image_file,
                        "caption": caption,
                    })

        elif os.path.exists(token_path):
            # 解析标准 .token 文件格式
            # 格式: image_id#caption_id<TAB>caption_text
            captions_by_image = {}
            with open(token_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        name_part = parts[0]
                        caption = parts[1]
                        # image_id#0 -> image_id.jpg
                        image_id = name_part.split('#')[0]
                        if image_id not in captions_by_image:
                            captions_by_image[image_id] = []
                        captions_by_image[image_id].append(caption)

            for image_id, captions in captions_by_image.items():
                for caption in captions:
                    samples.append({
                        "image": f"{image_id}.jpg",
                        "caption": caption,
                    })
        else:
            raise FileNotFoundError(
                f"未找到标注文件！请将 flickr30k.json 或 results_20130124.token 放在 {self.data_dir}/"
            )

        if self.max_samples:
            samples = samples[:self.max_samples]

        print(f"📦 Flickr30k [{self.split}]: {len(samples)} 样本")
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        image_path = os.path.join(self.image_dir, sample["image"])

        # 加载图像
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            # 兜底：随机图像
            print(f"⚠️ 无法加载 {image_path}: {e}")
            image = Image.new("RGB", (self.image_size, self.image_size))

        image = self.transform(image)

        result = {
            "image": image,
            "caption": sample["caption"],
            "image_path": sample["image"],
        }

        # 预 tokenize：利用 DataLoader 多 worker 并行处理
        # 注意：Windows spawn 多进程不共享类变量，需在每个 worker 内懒加载
        if self.pre_tokenize:
            if Flickr30kDataset._tokenizer is None:
                from transformers import CLIPTokenizerFast
                Flickr30kDataset._tokenizer = CLIPTokenizerFast.from_pretrained(
                    "openai/clip-vit-base-patch32", local_files_only=True
                )
            tok = Flickr30kDataset._tokenizer(
                sample["caption"], padding="max_length", truncation=True,
                max_length=int(os.environ.get("PEFT_MAX_SEQ_LEN", "77")), return_tensors="pt",
            )
            result["input_ids"] = tok["input_ids"].squeeze(0)
            result["attention_mask"] = tok["attention_mask"].squeeze(0)

        return result


# ============================================================
# MS-COCO Dataset
# ============================================================

class COCODataset(Dataset):
    """
    MS-COCO 图文检索数据集

    预期目录结构:
        coco/
        ├── train2014/
        ├── val2014/
        └── annotations/
            └── captions_train2014.json
            └── captions_val2014.json
    """

    def __init__(
        self,
        data_dir: str,
        split: str = "train",      # train, val
        image_size: int = 224,
        max_samples: Optional[int] = None,
    ):
        self.data_dir = data_dir
        self.split = split
        self.image_size = image_size
        self.max_samples = max_samples

        # COCO图像目录 — auto-detect 2017 or 2014
        self.image_dir = None
        for year in ["2017", "2014"]:
            d = os.path.join(data_dir, f"{split}{year}")
            if os.path.isdir(d):
                self.image_dir = d
                self._coco_year = year
                break
        if self.image_dir is None:
            self.image_dir = os.path.join(data_dir, f"{split}2014")
            self._coco_year = "2014"
        self.transform = get_clip_transform(image_size, is_train=(split == "train"))

        # 加载标注
        self.samples = self._load_annotations()

    def _load_annotations(self) -> List[Dict]:
        import json
        ann_file = os.path.join(self.data_dir, "annotations", f"captions_{self.split}{self._coco_year}.json")

        if not os.path.exists(ann_file):
            raise FileNotFoundError(
                f"未找到COCO标注: {ann_file}\n"
                f"请从 https://cocodataset.org 下载"
            )

        with open(ann_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 构建 image_id → file_name 映射
        id_to_file = {}
        for img_info in data["images"]:
            id_to_file[img_info["id"]] = img_info["file_name"]

        samples = []
        for ann in data["annotations"]:
            image_file = id_to_file.get(ann["image_id"])
            if image_file:
                samples.append({
                    "image": image_file,
                    "caption": ann["caption"],
                })

        if self.max_samples:
            samples = samples[:self.max_samples]

        print(f"📦 MS-COCO [{self.split}]: {len(samples)} 样本")
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        image_path = os.path.join(self.image_dir, sample["image"])

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (self.image_size, self.image_size))

        image = self.transform(image)

        return {
            "image": image,
            "caption": sample["caption"],
            "image_path": sample["image"],
        }


# ============================================================
# 通用域外数据集（简单图像分类数据集，测试泛化）
# ============================================================

class ImageNetStyleDataset(Dataset):
    """
    将图像分类数据集转换为图文对：使用类别名作文本描述

    支持: Food101, DTD, Flowers102, CIFAR100 等 torchvision 数据集
    """

    def __init__(
        self,
        dataset_name: str = "Food101",
        root: str = "./data",
        split: str = "train",
        image_size: int = 224,
        max_samples: Optional[int] = None,
    ):
        import torchvision.datasets as dsets

        self.image_size = image_size
        self.transform = get_clip_transform(image_size, is_train=(split == "train"))

        is_train = (split == "train")

        if dataset_name == "Food101":
            self.dataset = dsets.Food101(root=root, split=split, download=True)
            self.class_names = self.dataset.classes
        elif dataset_name == "DTD":
            self.dataset = dsets.DTD(root=root, split=split, download=True)
            self.class_names = self.dataset.classes
        elif dataset_name == "Flowers102":
            self.dataset = dsets.Flowers102(root=root, split=split, download=True)
            self.class_names = [str(i) for i in range(102)]  # Flowers102 没有类别名
        else:
            raise ValueError(f"不支持的数据集: {dataset_name}")

        self.prompts = [
            f"a photo of a {name}" for name in self.class_names
        ]

        if max_samples:
            import random
            indices = random.sample(range(len(self.dataset)), min(max_samples, len(self.dataset)))
            self.indices = indices
        else:
            self.indices = list(range(len(self.dataset)))

        print(f"📦 {dataset_name} [{split}]: {len(self.indices)} 样本, {len(self.class_names)} 类")

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        image, label = self.dataset[self.indices[idx]]
        image = self.transform(image)
        caption = self.prompts[label]

        return {
            "image": image,
            "caption": caption,
            "image_path": f"cls_{label}",
        }


# ============================================================
# DataLoader 构建
# ============================================================

def create_dataloaders(
    dataset_name: str = "flickr30k",
    data_dir: str = "./data",
    batch_size: int = 64,
    image_size: int = 224,
    num_workers: int | None = None,   # None=自动检测（CUDA用4, 否则0）
    max_samples: Optional[int] = None,
    pre_tokenize: bool = True,         # False=不需要 CLIP tokenizer（BLIP用）
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    if num_workers is None:
        import multiprocessing
        num_workers = 0 if not pre_tokenize else (min(4, multiprocessing.cpu_count() // 2) if torch.cuda.is_available() else 0)
    use_pin = torch.cuda.is_available()  # CUDA 下 pin_memory 加速传输

    dataset_cls = {
        "flickr30k": Flickr30kDataset,
        "coco": COCODataset,
    }

    if dataset_name not in dataset_cls:
        raise ValueError(f"未知数据集: {dataset_name}, 可选: {list(dataset_cls.keys())}")

    cls = dataset_cls[dataset_name]
    data_root = os.path.join(data_dir, dataset_name)

    # 对于Flickr30k，训练/验证/测试通常是同一批数据的不同分割
    # 这里简化：80%训练, 10%验证, 10%测试
    kwargs = {"split": "train", "image_size": image_size, "max_samples": max_samples}
    if dataset_name == "flickr30k":  # only Flickr30k supports pre_tokenize
        kwargs["pre_tokenize"] = pre_tokenize
    train_dataset = cls(data_root, **kwargs)

    kwargs["split"] = "val"
    val_dataset = cls(data_root, **kwargs)
    # COCO has no test captions; fall back to val
    if dataset_name == "coco":
        test_dataset = val_dataset
    else:
        kwargs["split"] = "test"
        test_dataset = cls(data_root, **kwargs)

    # 对 Flickr30k: 手动分割
    if dataset_name == "flickr30k":
        from torch.utils.data import random_split
        n = len(train_dataset)
        n_train = int(0.8 * n)
        n_val = int(0.1 * n)
        n_test = n - n_train - n_val
        train_dataset, val_dataset, test_dataset = random_split(
            train_dataset, [n_train, n_val, n_test],
            generator=torch.Generator().manual_seed(42)
        )

    loader_kwargs = dict(
        num_workers=num_workers,
        collate_fn=_collate_fn,
        pin_memory=use_pin,
        persistent_workers=(num_workers > 0),
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, **loader_kwargs)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, **loader_kwargs)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, **loader_kwargs)

    return train_loader, val_loader, test_loader

# 模块级 collate 函数（Windows spawn 多进程要求可 pickle）
def _collate_fn(batch):
    """Batch items; image_path is kept so retrieval evaluation can group captions by image."""
    images = torch.stack([item["image"] for item in batch])
    captions = [item["caption"] for item in batch]

    result = {"image": images, "caption": captions}

    # image identity must travel with the batch: once the loader is flattened into (image, caption)
    # rows, nothing else reveals which captions belong to the same image.
    if "image_path" in batch[0]:
        result["image_path"] = [item["image_path"] for item in batch]

    # 如果 dataset 已预 tokenize，直接 stack tensor
    if "input_ids" in batch[0]:
        result["input_ids"] = torch.stack([item["input_ids"] for item in batch])
        result["attention_mask"] = torch.stack([item["attention_mask"] for item in batch])

    return result
