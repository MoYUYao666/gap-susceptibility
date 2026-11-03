"""
DG* Trajectory Tracker — records DG* at every epoch for ODE fitting (V1).

Unlike GapTracker (which records CG and DG every N epochs),
this records DG* at EVERY epoch to enable reliable exponential curve fitting
for the Gap Susceptibility theory paper.
"""

import torch
import torch.nn.functional as F
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class DGStarRecord:
    """Single DG* measurement at one epoch."""
    epoch: int
    dg_star: float            # DG* = (1/N) Σ||z_i^I - z_i^T||²
    dg_empirical: float       # 2-Wasserstein DG (for cross-validation)
    cg: float                 # Centroid Gap ||μ_I - μ_T||


class DGStarTracker:
    """
    Records DG* at every epoch for ODE trajectory fitting (V1).

    Usage:
        tracker = DGStarTracker(sample_size=5000, device="cuda")
        for epoch in range(num_epochs):
            train(...)
            record = tracker.compute(image_embeds, text_embeds, epoch)
            tracker.record(record)
        # After training:
        dg_star_vals = tracker.get_dg_star_array()
    """

    def __init__(self, sample_size: int = 5000, device: str = "cuda"):
        self.sample_size = sample_size
        self.device = device
        self.history: List[DGStarRecord] = []

    @torch.no_grad()
    def compute(
        self,
        image_embeds: torch.Tensor,  # (N, D)
        text_embeds: torch.Tensor,    # (N, D)
        epoch: int = 0,
    ) -> DGStarRecord:
        """
        Compute DG*, empirical DG (2-Wasserstein), and CG from embeddings.
        Assumes inputs are already on the correct device.
        Will L2-normalize inputs first.
        """
        # Normalize
        image_embeds = F.normalize(image_embeds.float(), p=2, dim=-1)
        text_embeds = F.normalize(text_embeds.float(), p=2, dim=-1)

        # Sample if needed
        N = image_embeds.shape[0]
        if N > self.sample_size:
            indices = torch.randperm(N, device=image_embeds.device)[:self.sample_size]
            image_embeds = image_embeds[indices]
            text_embeds = text_embeds[indices]

        # DG* = pairwise squared L2 distance
        sq_diffs = ((image_embeds - text_embeds) ** 2).sum(dim=-1)
        dg_star = sq_diffs.mean().item()

        # CG = ||μ_I - μ_T||
        mu_i = image_embeds.mean(dim=0)
        mu_t = text_embeds.mean(dim=0)
        cg = (mu_i - mu_t).norm(p=2).item()

        # Empirical DG = 2-Wasserstein (diagonal covariance assumption)
        # W₂² = ||μ_I-μ_T||² + ||σ_I-σ_T||²
        sigma_i = image_embeds.std(dim=0)
        sigma_t = text_embeds.std(dim=0)
        var_term = (sigma_i - sigma_t).norm(p=2).item() ** 2
        dg_emp = (cg ** 2 + var_term) ** 0.5

        return DGStarRecord(
            epoch=epoch,
            dg_star=dg_star,
            dg_empirical=dg_emp,
            cg=cg,
        )

    def record(self, record: DGStarRecord):
        """Append a measurement to the history."""
        self.history.append(record)

    def get_dg_star_array(self) -> List[float]:
        """Return list of DG* values in recording order."""
        return [r.dg_star for r in self.history]

    def get_epochs(self) -> List[int]:
        """Return list of epoch numbers in recording order."""
        return [r.epoch for r in self.history]

    def get_dg_empirical_array(self) -> List[float]:
        """Return list of empirical DG (2-Wasserstein) values."""
        return [r.dg_empirical for r in self.history]

    def get_cg_array(self) -> List[float]:
        """Return list of CG values."""
        return [r.cg for r in self.history]

    def get_history_dict(self) -> Dict[str, List[float]]:
        """Return all history as a dict for JSON serialization."""
        return {
            "epochs": self.get_epochs(),
            "dg_star": self.get_dg_star_array(),
            "dg_empirical": self.get_dg_empirical_array(),
            "cg": self.get_cg_array(),
        }

    def __len__(self) -> int:
        return len(self.history)

    def __getitem__(self, idx: int) -> DGStarRecord:
        return self.history[idx]
