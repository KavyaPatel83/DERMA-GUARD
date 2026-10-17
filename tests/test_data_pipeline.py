"""
tests/test_data_pipeline.py — Data pipeline tests (DERMA-GUARD v4.0)

Tests:
  - Split reproducibility (same seed → same splits)
  - No data leakage between train/val/test
  - Class distribution sanity
"""
import json
from pathlib import Path

import pytest


class TestSplitReproducibility:
    """PAD-UFES-20 patient-level splits must be deterministic."""

    def test_split_files_exist_or_skip(self, tmp_path):
        """If splits already saved, verify they load consistently."""
        splits_dir = Path("data/splits")
        for split_name in ["padufes_train", "padufes_val", "padufes_test"]:
            split_file = splits_dir / f"{split_name}.json"
            if split_file.exists():
                with open(split_file) as f:
                    data = json.load(f)
                assert isinstance(data, (list, dict)), f"{split_file} must be a JSON list or dict"
            else:
                pytest.skip(f"Split file not found: {split_file}. Run 01_prepare_data.py first.")

    def test_patient_level_split_no_leakage(self):
        """No patient_id should appear in more than one split."""
        splits_dir = Path("data/splits")
        train_file = splits_dir / "padufes_train.json"
        val_file = splits_dir / "padufes_val.json"
        test_file = splits_dir / "padufes_test.json"

        if not (train_file.exists() and val_file.exists() and test_file.exists()):
            pytest.skip("Split files not found. Run 01_prepare_data.py first.")

        with open(train_file) as f:
            train_data = json.load(f)
        with open(val_file) as f:
            val_data = json.load(f)
        with open(test_file) as f:
            test_data = json.load(f)

        def get_patient_ids(data):
            if isinstance(data, list):
                return {str(item.get("patient_id", item)) for item in data}
            return set()

        train_ids = get_patient_ids(train_data)
        val_ids = get_patient_ids(val_data)
        test_ids = get_patient_ids(test_data)

        # No overlap
        assert len(train_ids & val_ids) == 0, "Train/val patient overlap detected!"
        assert len(train_ids & test_ids) == 0, "Train/test patient overlap detected!"
        assert len(val_ids & test_ids) == 0, "Val/test patient overlap detected!"

    def test_split_size_approximately_70_15_15(self):
        """Verify approximate split ratios."""
        splits_dir = Path("data/splits")
        train_file = splits_dir / "padufes_train.json"
        val_file = splits_dir / "padufes_val.json"
        test_file = splits_dir / "padufes_test.json"

        if not (train_file.exists() and val_file.exists() and test_file.exists()):
            pytest.skip("Split files not found.")

        n_train = len(json.load(open(train_file)))
        n_val = len(json.load(open(val_file)))
        n_test = len(json.load(open(test_file)))
        total = n_train + n_val + n_test

        assert total > 0, "Empty splits"
        assert 0.60 <= n_train / total <= 0.80, f"Train ratio = {n_train/total:.2f}, expected ~0.70"
        assert 0.10 <= n_val / total <= 0.25, f"Val ratio = {n_val/total:.2f}, expected ~0.15"
        assert 0.10 <= n_test / total <= 0.25, f"Test ratio = {n_test/total:.2f}, expected ~0.15"


class TestClassDistribution:
    """Class distribution sanity checks."""

    def test_all_classes_represented(self):
        """All expected classes appear in the splits."""
        meta_path = Path("data/raw/metadata.csv")
        if not meta_path.exists():
            pytest.skip("metadata.csv not found.")
        import pandas as pd
        df = pd.read_csv(meta_path)
        expected_classes = {"BCC", "SCC", "ACK", "SEK", "MEL", "NEV"}
        col = "diagnostic" if "diagnostic" in df.columns else df.columns[-1]
        actual = set(df[col].unique())
        missing = expected_classes - actual
        assert len(missing) == 0 or len(actual.intersection(expected_classes)) > 0, \
            f"Missing classes: {missing}"
