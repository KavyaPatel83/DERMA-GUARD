import argparse
import sys
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.utils import load_config, set_seed
from src.data.preprocessing import load_metadata, preprocess_metadata, verify_images
from src.data.splits import create_stratified_group_split, verify_splits

def main():
    parser = argparse.ArgumentParser(description="Prepare data for HealthSphere-Derm")
    parser.add_argument("--config", type=str, default="configs/base.yaml", help="Path to config file")
    parser.add_argument("--verify-only", action="store_true", help="Only verify data, do not process")
    args = parser.parse_args()
    
    config = load_config(args.config)
    set_seed(config.get('seed', 42))
    
    print("Loading metadata...")
    raw_meta_path = Path(config['data']['raw_metadata'])
    df = load_metadata(raw_meta_path)
    print(f"Loaded {len(df)} records.")
    
    print("Verifying images...")
    img_dir = Path(config['data']['raw_images'])
    verify_images(img_dir, df)
    
    if args.verify_only:
        print("Verification complete.")
        return
        
    print("Preprocessing metadata...")
    df_proc, feature_cols, meta_tensor = preprocess_metadata(df, binary=(config['num_classes']==2))
    
    print("Creating splits...")
    splits = create_stratified_group_split(
        df_proc, 
        seed=config.get('seed', 42),
        train_ratio=config.get('train_ratio', 0.7),
        val_ratio=config.get('val_ratio', 0.15)
    )
    
    verify_splits(splits, df_proc)
    
    # Save processed outputs
    out_dir = Path(config['data']['processed_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)
    
    splits_path = Path(config['data']['splits_file'])
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    with open(splits_path, 'w') as f:
        json.dump(splits, f, indent=4)
        
    print(f"Splits saved to {splits_path}")
    print("Data preparation complete.")

if __name__ == "__main__":
    main()
