"""
Data loading module — Flickr30k, MS-COCO
Adapted to CLIP training format: (image, text) paired data
"""

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import json
import os
from typing import List, Dict, Tuple, Optional


# ============================================================
# CLIP standard preprocessing
# ============================================================

CLIP_MEAN = [0.48145466, 0.4578275, 0.40821073]
CLIP_STD = [0.26862954, 0.26130258, 0.27577711]


def get_clip_transform(image_size: int = 224, is_train: bool = True):
    """CLIP standard image preprocessing"""
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
    Flickr30k image-text retrieval dataset

    Expected directory structure:
        flickr30k/
        ├── flickr30k-images/
        │   ├── 1000092795.jpg
        │   └── ...
        └── flickr30k.json  (or results_20130124.token)
            [{"image": "xxx.jpg", "captions": ["...", "...", ...]}, ...]
    """

    _tokenizer = None  # class-level shared, avoid loading multiple times

    def __init__(
        self,
        data_dir: str,
        split: str = "train",   # train, val, test
        image_size: int = 224,
        max_samples: Optional[int] = None,
        pre_tokenize: bool = True,  # pre-tokenize on the dataset side, use multi-worker parallelism
    ):
        self.data_dir = data_dir
        self.split = split
        self.image_size = image_size
        self.max_samples = max_samples
        self.pre_tokenize = pre_tokenize

        self.image_dir = os.path.join(data_dir, "flickr30k-images")
        self.transform = get_clip_transform(image_size, is_train=(split == "train"))

        # load tokenizer (lazy loading, shared)
        if pre_tokenize and Flickr30kDataset._tokenizer is None:
            from transformers import CLIPTokenizerFast
            Flickr30kDataset._tokenizer = CLIPTokenizerFast.from_pretrained(
                "openai/clip-vit-base-patch32", local_files_only=True
            )

        # load annotations
        self.samples = self._load_annotations()

    def _load_annotations(self) -> List[Dict]:
        """Load and parse the annotation file"""
        # try multiple formats
        csv_path = os.path.join(self.data_dir, "results.csv")
        json_path = os.path.join(self.data_dir, "flickr30k.json")
        token_path = os.path.join(self.data_dir, "results_20130124.token")

        samples = []

        # try CSV format first (pipe-separated: image_name | comment_number | comment)
        if os.path.exists(csv_path):
            import csv
            captions_by_image = {}
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')
                header = next(reader, None)  # skip the header row
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
            print(f"   📋 CSV format ({len(captions_by_image)} images, {len(samples)} annotations)")

        elif os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # each image has 5 annotations → expand into independent samples
            for item in data:
                image_file = item["image"]
                for caption in item["captions"]:
                    samples.append({
                        "image": image_file,
                        "caption": caption,
                    })

        elif os.path.exists(token_path):
            # parse the standard .token file format
            # format: image_id#caption_id<TAB>caption_text
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
                f"Annotation file not found! Please put flickr30k.json or results_20130124.token in {self.data_dir}/"
            )

        if self.max_samples:
            samples = samples[:self.max_samples]

        print(f"📦 Flickr30k [{self.split}]: {len(samples)} samples")
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        image_path = os.path.join(self.image_dir, sample["image"])

        # load image
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            # fallback: random image
            print(f"⚠️ Failed to load {image_path}: {e}")
            image = Image.new("RGB", (self.image_size, self.image_size))

        image = self.transform(image)

        result = {
            "image": image,
            "caption": sample["caption"],
            "image_path": sample["image"],
        }

        # pre-tokenize: use DataLoader multi-worker parallel processing
        # note: Windows spawn multiprocessing does not share class variables, so lazy-load inside each worker
        if self.pre_tokenize:
            if Flickr30kDataset._tokenizer is None:
                from transformers import CLIPTokenizerFast
                Flickr30kDataset._tokenizer = CLIPTokenizerFast.from_pretrained(
                    "openai/clip-vit-base-patch32", local_files_only=True
                )
            tok = Flickr30kDataset._tokenizer(
                sample["caption"], padding="max_length", truncation=True,
                max_length=77, return_tensors="pt",
            )
            result["input_ids"] = tok["input_ids"].squeeze(0)
            result["attention_mask"] = tok["attention_mask"].squeeze(0)

        return result


# ============================================================
# MS-COCO Dataset
# ============================================================

class COCODataset(Dataset):
    """
    MS-COCO image-text retrieval dataset

    Expected directory structure:
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

        # COCO image directory — auto-detect 2017 or 2014
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

        # load annotations
        self.samples = self._load_annotations()

    def _load_annotations(self) -> List[Dict]:
        import json
        ann_file = os.path.join(self.data_dir, "annotations", f"captions_{self.split}{self._coco_year}.json")

        if not os.path.exists(ann_file):
            raise FileNotFoundError(
                f"COCO annotations not found: {ann_file}\n"
                f"Please download from https://cocodataset.org"
            )

        with open(ann_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # build image_id → file_name mapping
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

        print(f"📦 MS-COCO [{self.split}]: {len(samples)} samples")
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
# General out-of-domain datasets (simple image classification datasets, to test generalization)
# ============================================================

class ImageNetStyleDataset(Dataset):
    """
    Convert an image classification dataset into image-text pairs: use the class name as the text description

    Supports: Food101, DTD, Flowers102, CIFAR100 and other torchvision datasets
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
            self.class_names = [str(i) for i in range(102)]  # Flowers102 has no class names
        else:
            raise ValueError(f"Unsupported dataset: {dataset_name}")

        self.prompts = [
            f"a photo of a {name}" for name in self.class_names
        ]

        if max_samples:
            import random
            indices = random.sample(range(len(self.dataset)), min(max_samples, len(self.dataset)))
            self.indices = indices
        else:
            self.indices = list(range(len(self.dataset)))

        print(f"📦 {dataset_name} [{split}]: {len(self.indices)} samples, {len(self.class_names)} classes")

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
# DataLoader construction
# ============================================================

def create_dataloaders(
    dataset_name: str = "flickr30k",
    data_dir: str = "./data",
    batch_size: int = 64,
    image_size: int = 224,
    num_workers: int | None = None,   # None=auto-detect (4 for CUDA, otherwise 0)
    max_samples: Optional[int] = None,
    pre_tokenize: bool = True,         # False=no CLIP tokenizer needed (used by BLIP)
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    if num_workers is None:
        import multiprocessing
        num_workers = 0 if not pre_tokenize else (min(4, multiprocessing.cpu_count() // 2) if torch.cuda.is_available() else 0)
    use_pin = torch.cuda.is_available()  # pin_memory speeds up transfer under CUDA

    dataset_cls = {
        "flickr30k": Flickr30kDataset,
        "coco": COCODataset,
    }

    if dataset_name not in dataset_cls:
        raise ValueError(f"Unknown dataset: {dataset_name}, options: {list(dataset_cls.keys())}")

    cls = dataset_cls[dataset_name]
    data_root = os.path.join(data_dir, dataset_name)

    # For Flickr30k, train/val/test are usually different splits of the same data
    # Simplified here: 80% train, 10% val, 10% test
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

    # for Flickr30k: manual split
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

# module-level collate function (Windows spawn multiprocessing requires it to be picklable)
def _collate_fn(batch):
    """Batching: collect and pad text (supports pre-tokenization)"""
    images = torch.stack([item["image"] for item in batch])
    captions = [item["caption"] for item in batch]

    result = {"image": images, "caption": captions}

    # if the dataset is already pre-tokenized, directly stack the tensors
    if "input_ids" in batch[0]:
        result["input_ids"] = torch.stack([item["input_ids"] for item in batch])
        result["attention_mask"] = torch.stack([item["attention_mask"] for item in batch])

    return result
