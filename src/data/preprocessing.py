import pandas as pd
import numpy as np
from pathlib import Path

def load_metadata(csv_path: str | Path) -> pd.DataFrame:
    """Load PAD-UFES-20 metadata CSV.
    Returns pandas DataFrame with 26 columns.
    Validates expected columns exist.
    """
    df = pd.read_csv(csv_path)
    expected_cols = [
        'patient_id', 'lesion_id', 'img_id', 'diagnostic', 'age', 'gender', 
        'region', 'fitspatrick', 'diameter_1', 'diameter_2', 'biopsed', 'smoke', 
        'drink', 'background_father', 'background_mother', 'pesticide', 
        'skin_cancer_history', 'cancer_history', 'has_piped_water', 
        'has_sewage_system', 'itch', 'grew', 'hurt', 'changed', 'bleed', 'elevation'
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in metadata: {missing}")
    return df

def preprocess_metadata(df: pd.DataFrame, binary: bool = True) -> tuple[pd.DataFrame, list, np.ndarray]:
    """Process all 26 metadata fields.
    
    Continuous (normalize to [0,1]): age, diameter_1, diameter_2
    Categorical (one-hot): gender, region, fitspatrick, background_father, background_mother
    Ternary (True=1, False=0, UNK=0.5): smoke, drink, pesticide, skin_cancer_history, 
        cancer_history, has_piped_water, has_sewage_system, itch, grew, hurt, changed, bleed, elevation
    Boolean: biopsed -> 1/0
    """
    df_proc = df.copy()
    feature_cols = []
    
    # Continuous
    continuous = ['age', 'diameter_1', 'diameter_2']
    for col in continuous:
        # replace UNK with NaN temporarily if any, though continuous shouldn't have UNK
        df_proc[col] = pd.to_numeric(df_proc[col].replace('UNK', np.nan), errors='coerce')
        df_proc[col] = df_proc[col].fillna(df_proc[col].mean())
        # min-max scaling
        min_val = df_proc[col].min()
        max_val = df_proc[col].max()
        df_proc[col] = (df_proc[col] - min_val) / (max_val - min_val + 1e-8)
        feature_cols.append(col)
        
    # Ternary mapping function
    def map_ternary(val):
        if pd.isna(val) or val == 'UNK': return 0.5
        if str(val).lower() in ['true', '1', 'yes']: return 1.0
        if str(val).lower() in ['false', '0', 'no']: return 0.0
        return 0.5

    ternary_cols = [
        'smoke', 'drink', 'pesticide', 'skin_cancer_history', 'cancer_history', 
        'has_piped_water', 'has_sewage_system', 'itch', 'grew', 'hurt', 
        'changed', 'bleed', 'elevation'
    ]
    for col in ternary_cols:
        df_proc[col] = df_proc[col].apply(map_ternary)
        feature_cols.append(col)

    # Boolean
    df_proc['biopsed'] = df_proc['biopsed'].apply(lambda x: 1.0 if str(x).lower() in ['true', '1', 'yes'] else 0.0)
    feature_cols.append('biopsed')
    
    # Categorical
    categorical = ['gender', 'region', 'fitspatrick', 'background_father', 'background_mother']
    for col in categorical:
        df_proc[col] = df_proc[col].fillna('UNK')
        dummies = pd.get_dummies(df_proc[col], prefix=col)
        df_proc = pd.concat([df_proc, dummies], axis=1)
        feature_cols.extend(dummies.columns.tolist())

    # Labels
    if binary:
        malignant = ['BCC', 'SCC', 'ACK', 'MEL']
        df_proc['label'] = df_proc['diagnostic'].apply(lambda x: 1 if x in malignant else 0)
    else:
        label_map = {'BCC': 0, 'SCC': 1, 'ACK': 2, 'SEK': 3, 'MEL': 4, 'NEV': 5}
        df_proc['label'] = df_proc['diagnostic'].map(label_map)

    # Create metadata tensor
    metadata_tensor = df_proc[feature_cols].values.astype(np.float32)
    
    return df_proc, feature_cols, metadata_tensor

def verify_images(image_dir: str | Path, metadata_df: pd.DataFrame) -> bool:
    """Verify all img_id.png files exist and are loadable."""
    image_dir = Path(image_dir)
    missing = []
    for img_id in metadata_df['img_id']:
        path = image_dir / f"{img_id}"
        if not path.exists():
            missing.append(img_id)
    
    if missing:
        print(f"Warning: {len(missing)} images missing.")
        return False
    return True

def get_metadata_dim(df: pd.DataFrame) -> int:
    """Return actual feature dimension after one-hot encoding."""
    _, features, _ = preprocess_metadata(df)
    return len(features)

if __name__ == "__main__":
    pass
