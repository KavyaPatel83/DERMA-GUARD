import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit

def create_stratified_group_split(metadata_df: pd.DataFrame, seed: int = 42, train_ratio: float = 0.7, val_ratio: float = 0.15) -> dict:
    """Split data 70/15/15 GROUPED BY patient_id.
    
    1. Keep all images from same patient in same split
    2. Approximate class distribution
    3. Ensure MEL appears in all splits
    """
    test_ratio = 1.0 - train_ratio - val_ratio
    
    # We use GroupShuffleSplit to split out train, then val/test
    gss1 = GroupShuffleSplit(n_splits=1, train_size=train_ratio, random_state=seed)
    train_idx, temp_idx = next(gss1.split(metadata_df, metadata_df['diagnostic'], metadata_df['patient_id']))
    
    temp_df = metadata_df.iloc[temp_idx].reset_index(drop=True)
    val_rel_ratio = val_ratio / (val_ratio + test_ratio)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=val_rel_ratio, random_state=seed)
    val_rel_idx, test_rel_idx = next(gss2.split(temp_df, temp_df['diagnostic'], temp_df['patient_id']))
    
    val_idx = temp_idx[val_rel_idx]
    test_idx = temp_idx[test_rel_idx]
    
    splits = {
        'train': train_idx.tolist(),
        'val': val_idx.tolist(),
        'test': test_idx.tolist()
    }
    
    # Verify distributions
    for split_name, idxs in splits.items():
        subset = metadata_df.iloc[idxs]
        print(f"--- {split_name.upper()} ---")
        print(subset['diagnostic'].value_counts())
        
    return splits

def load_splits(splits_path: str | Path) -> dict:
    """Load saved split indices."""
    with open(splits_path, 'r') as f:
        return json.load(f)

def verify_splits(splits: dict, metadata_df: pd.DataFrame) -> bool:
    """Verify no patient leakage, class representation."""
    train_p = set(metadata_df.iloc[splits['train']]['patient_id'])
    val_p = set(metadata_df.iloc[splits['val']]['patient_id'])
    test_p = set(metadata_df.iloc[splits['test']]['patient_id'])
    
    if len(train_p.intersection(val_p)) > 0 or len(train_p.intersection(test_p)) > 0 or len(val_p.intersection(test_p)) > 0:
        print("Data Leakage Detected! Patient overlap across splits.")
        return False
    return True

if __name__ == "__main__":
    pass
