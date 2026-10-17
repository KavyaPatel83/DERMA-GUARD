"""Multi-modal PyTorch Dataset and DataLoader factory for HealthSphere-Derm.

Returns batches containing:
- image: (B, 3, 224, 224) tensor
- metadata: (B, metadata_dim) tensor  
- text_input_ids: (B, 128) token IDs
- text_attention_mask: (B, 128) attention mask
- ptis_features: (B, 7) PTIS feature vector
- label: (B,) class label
- img_id: list of image IDs
- raw_text: list of text descriptions
"""
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from PIL import Image
from pathlib import Path


class HealthSphereDataset(Dataset):
    """Multi-modal dataset for HealthSphere-Derm."""
    def __init__(self, metadata_df: pd.DataFrame, indices: list, image_dir: str | Path, 
                 texts_df: pd.DataFrame = None, tokenizer=None, transform=None, 
                 metadata_columns: list = None, ptis_extractor=None, binary: bool = True):
        self.metadata_df = metadata_df.iloc[indices].reset_index(drop=True)
        self.image_dir = Path(image_dir)
        self.tokenizer = tokenizer
        self.transform = transform
        self.metadata_columns = metadata_columns
        self.ptis_extractor = ptis_extractor
        self.binary = binary
        
        # Merge texts if provided
        self.text_map = {}
        if texts_df is not None and not texts_df.empty:
            # Prefer paraphrased, fall back to filled
            for _, row in texts_df.iterrows():
                img_id = row.get('img_id', '')
                text = row.get('paraphrased_description', '') or row.get('filled_description', '')
                if text and isinstance(text, str):
                    self.text_map[img_id] = text

    def __len__(self):
        return len(self.metadata_df)

    def __getitem__(self, idx):
        row = self.metadata_df.iloc[idx]
        img_id = row['img_id']
        
        # ── Image ──────────────────────────────────────────────
        img_path = self.image_dir / f"{img_id}"
        if not img_path.exists():
            # Try with .png extension
            img_path = self.image_dir / f"{img_id}.png"
        
        if img_path.exists():
            try:
                image = Image.open(img_path).convert('RGB')
                if self.transform:
                    image = self.transform(image)
                else:
                    image = torch.zeros(3, 224, 224)
            except Exception:
                image = torch.zeros(3, 224, 224)
        else:
            image = torch.zeros(3, 224, 224)
                
        # ── Metadata ───────────────────────────────────────────
        if self.metadata_columns:
            try:
                meta_vec = row[self.metadata_columns].values.astype(np.float32)
                meta_tensor = torch.from_numpy(meta_vec)
            except Exception:
                meta_tensor = torch.zeros(len(self.metadata_columns))
        else:
            meta_tensor = torch.zeros(1)
            
        # ── Label ──────────────────────────────────────────────
        label = int(row.get('label', 0))
        
        # ── Text ───────────────────────────────────────────────
        raw_text = self.text_map.get(img_id, "Patient skin lesion description not available.")
        
        input_ids = torch.zeros(128, dtype=torch.long)
        attention_mask = torch.zeros(128, dtype=torch.long)
        
        if self.tokenizer:
            text_out = self.tokenizer(
                raw_text, padding='max_length', max_length=128, 
                truncation=True, return_tensors='pt'
            )
            input_ids = text_out['input_ids'].squeeze(0)
            attention_mask = text_out['attention_mask'].squeeze(0)
            
        # ── PTIS Features ─────────────────────────────────────
        if self.ptis_extractor:
            ptis_features = torch.from_numpy(self.ptis_extractor(raw_text)).float()
        else:
            ptis_features = torch.zeros(7, dtype=torch.float32)
        
        return {
            'image': image,
            'metadata': meta_tensor,
            'text_input_ids': input_ids,
            'text_attention_mask': attention_mask,
            'label': torch.tensor(label, dtype=torch.long),
            'ptis_features': ptis_features,
            'img_id': img_id,
            'raw_text': raw_text
        }


def create_dataloaders(config: dict, metadata_df=None, feature_cols=None, 
                       splits=None, texts_df=None, tokenizer=None,
                       train_transform=None, eval_transform=None):
    """Create train/val/test DataLoaders with proper configuration.
    
    Args:
        config: YAML config dict
        metadata_df: preprocessed DataFrame with 'label' column
        feature_cols: list of metadata feature column names
        splits: dict with 'train', 'val', 'test' index lists
        texts_df: DataFrame with img_id + text columns
        tokenizer: BERT tokenizer instance
        train_transform: torchvision transforms for training
        eval_transform: torchvision transforms for evaluation
    
    Returns:
        dict with 'train', 'val', 'test' DataLoaders (or None for missing components)
    """
    if metadata_df is None or splits is None:
        print("Warning: metadata_df or splits not provided. Returning None dataloaders.")
        return {'train': None, 'val': None, 'test': None}
    
    # Import PTIS feature extractor
    try:
        from src.ptis.features import extract_ptis_features
        ptis_fn = extract_ptis_features
    except ImportError:
        ptis_fn = None
    
    image_dir = Path(config.get('data', {}).get('raw_images', 'data/raw/images'))
    batch_size = config.get('batch_size', 16)
    
    # Create datasets
    train_ds = HealthSphereDataset(
        metadata_df=metadata_df, indices=splits['train'],
        image_dir=image_dir, texts_df=texts_df, tokenizer=tokenizer,
        transform=train_transform, metadata_columns=feature_cols,
        ptis_extractor=ptis_fn
    )
    
    val_ds = HealthSphereDataset(
        metadata_df=metadata_df, indices=splits['val'],
        image_dir=image_dir, texts_df=texts_df, tokenizer=tokenizer,
        transform=eval_transform, metadata_columns=feature_cols,
        ptis_extractor=ptis_fn
    )
    
    test_ds = HealthSphereDataset(
        metadata_df=metadata_df, indices=splits['test'],
        image_dir=image_dir, texts_df=texts_df, tokenizer=tokenizer,
        transform=eval_transform, metadata_columns=feature_cols,
        ptis_extractor=ptis_fn
    )
    
    # Custom collate to handle mixed types (strings + tensors)
    def collate_fn(batch):
        result = {}
        for key in batch[0]:
            if key in ('img_id', 'raw_text'):
                result[key] = [item[key] for item in batch]
            else:
                result[key] = torch.stack([item[key] for item in batch])
        return result
    
    dataloaders = {
        'train': DataLoader(train_ds, batch_size=batch_size, shuffle=True, 
                           num_workers=0, collate_fn=collate_fn, drop_last=True),
        'val': DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                         num_workers=0, collate_fn=collate_fn),
        'test': DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                          num_workers=0, collate_fn=collate_fn)
    }
    
    print(f"Created dataloaders — Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")
    return dataloaders


if __name__ == "__main__":
    pass
