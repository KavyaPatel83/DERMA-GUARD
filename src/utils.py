import os
import random
import numpy as np
import torch
import yaml
from pathlib import Path
from torch.utils.tensorboard import SummaryWriter

def set_seed(seed: int = 42):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

def load_config(config_path: str | Path) -> dict:
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_device() -> torch.device:
    """Return available device (cuda/cpu)."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def setup_tensorboard(log_dir: str = 'outputs/logs', run_name: str = None) -> SummaryWriter:
    """Initialize TensorBoard SummaryWriter for experiment tracking.
    Free, local, no API keys required.
    """
    if run_name:
        log_dir = os.path.join(log_dir, run_name)
    writer = SummaryWriter(log_dir=log_dir)
    return writer

class EarlyStopping:
    """Early stopping to stop the training when the loss does not improve."""
    def __init__(self, patience: int = 10, delta: float = 0.0, save_path: str | Path = 'checkpoint.pt'):
        self.patience = patience
        self.delta = delta
        self.save_path = save_path
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.Inf

    def __call__(self, val_loss: float, model: torch.nn.Module):
        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss: float, model: torch.nn.Module):
        """Saves model when validation loss decrease."""
        Path(self.save_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), self.save_path)
        self.val_loss_min = val_loss

def compute_class_weights(labels: np.ndarray) -> torch.Tensor:
    """Compute inverse frequency weights for classes."""
    classes, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    weights = total / (len(classes) * counts)
    return torch.FloatTensor(weights)

class AverageMeter:
    """Computes and stores the average and current value."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

def count_parameters(model: torch.nn.Module) -> int:
    """Count trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

if __name__ == "__main__":
    pass
