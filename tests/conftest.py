"""
tests/conftest.py — pytest configuration for DERMA-GUARD v4.0

Fixes:
  - KMP_DUPLICATE_LIB_OK: resolves Anaconda libiomp5md.dll dual-init crash
    (PyTorch + MKL both ship OpenMP on Windows)
  - Sets deterministic seeds for reproducibility
"""
import os

# MUST be set before any numpy/torch import to prevent OpenMP DLL crash on Windows
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import random
import numpy as np
import torch
import pytest


def pytest_configure(config):
    """Called after command line options have been parsed."""
    # Silence transformers download warnings during tests
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_DATASETS_VERBOSITY", "error")


@pytest.fixture(autouse=True)
def set_deterministic_seed():
    """Set seeds for reproducibility on every test."""
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    yield
