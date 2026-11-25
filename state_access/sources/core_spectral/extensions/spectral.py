"""Per-example spectral head gating: an explicit CLIP adaptation, not exact DSW.

This standalone component does not choose layers, install hooks, alter adapter
rank, collect calibration data, run training or establish a causal mechanism.
"""

import math

import torch
from torch import nn


__all__ = ["SpectralHeadGate"]


class SpectralHeadGate(nn.Module):
    """Gate real head outputs [B,H,T,D] using valid-prefix token spectra.

    Both modes require an explicitly supplied, one-time calibration reference.
    Dynamic mode uses current per-example E*entropy; frozen_reference mode uses
    the locked per-head mean. Both use w = 1 + alpha + tanh(beta)*(f - 0.5).
    Alpha [H] and scalar beta start at zero. Static beta can be absorbed into
    alpha, so nominal parameter equality is not effective-capacity equivalence.

    All positions in the returned tensor are scaled, including padded positions;
    padding never contributes to spectra. The caller retains the original mask.
    Full valid-prefix statistics do not establish autoregressive prefix causality.
    """

    def __init__(self, num_heads: int, mode: str = "dynamic"):
        super().__init__()
        if isinstance(num_heads, bool) or not isinstance(num_heads, int):
            raise TypeError("num_heads must be an integer")
        if num_heads < 1:
            raise ValueError("num_heads must be positive")
        if mode not in ("dynamic", "frozen_reference"):
            raise ValueError("mode must be dynamic or frozen_reference")
        self.num_heads = num_heads
        self.mode = mode
        self.alpha = nn.Parameter(torch.zeros(num_heads))
        self.beta = nn.Parameter(torch.zeros(()))
        self.register_buffer("_reference", torch.zeros(num_heads))
        self.register_buffer("_reference_ready", torch.tensor(False))

    @property
    def reference(self):
        """Return a detached copy; editing it cannot replace the locked buffer."""
        if not self._reference_ready.item():
            raise RuntimeError("Calibration reference has not been set")
        return self._reference.detach().clone()

    def _checked_reference(self, means):
        value = torch.as_tensor(means)
        if value.is_complex() or value.dtype == torch.bool:
            raise TypeError("reference must contain real numeric means")
        if tuple(value.shape) != (self.num_heads,):
            raise ValueError("reference must have shape [H]")
        if not torch.isfinite(value).all().item():
            raise ValueError("reference must be finite")
        if not ((value >= 0) & (value <= 1)).all().item():
            raise ValueError("reference must lie in [0, 1]")
        return value.detach().to(self._reference).clone()

    def set_reference(self, means):
        """Lock explicit calibration means once; never estimate from a forward."""
        if self._reference_ready.item():
            raise RuntimeError("Calibration reference is immutable after it is set")
        value = self._checked_reference(means)
        with torch.no_grad():
            self._reference.copy_(value)
            self._reference_ready.fill_(True)

    def get_extra_state(self):
        """Bind mode and gate definition to strict state restoration."""
        return {"version": 1, "num_heads": self.num_heads, "mode": self.mode,
                "centering": 0.5, "high_band_cycles_per_token": 0.25}

    def set_extra_state(self, state):
        if not isinstance(state, dict) or state != self.get_extra_state():
            raise RuntimeError("Spectral gate state configuration does not match")

    def load_state_dict(self, state_dict, strict=True, assign=False):
        """Require complete restoration, including reference and configuration."""
        if not strict:
            raise ValueError("Spectral gate state must be restored strictly")
        return super().load_state_dict(state_dict, strict=True, assign=assign)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                              missing_keys, unexpected_keys, error_msgs):
        # Validate before copying any local values, including when nested in a
        # parent module. Missing calibration must never become an implicit zero.
        names = ("alpha", "beta", "_reference", "_reference_ready", "_extra_state")
        absent = [prefix + name for name in names if prefix + name not in state_dict]
        if absent:
            error_msgs.append("Missing spectral gate state: " + ", ".join(absent))
            return
        try:
            self.set_extra_state(state_dict[prefix + "_extra_state"])
            ref = self._checked_reference(state_dict[prefix + "_reference"])
            ready = state_dict[prefix + "_reference_ready"]
            if not (torch.is_tensor(ready) and ready.shape == torch.Size([])
                    and ready.dtype == torch.bool):
                raise ValueError("reference readiness must be a scalar boolean tensor")
            if not ready.item() and torch.count_nonzero(ref).item():
                raise ValueError("Uninitialized reference state must contain zero means")
            if self._reference_ready.item() and (
                    not ready.item() or not torch.equal(ref, self._reference)):
                raise ValueError("Locked reference cannot be replaced by state loading")
            for name, shape in (("alpha", (self.num_heads,)), ("beta", ())):
                param = state_dict[prefix + name]
                if not (torch.is_tensor(param) and param.is_floating_point()
                        and tuple(param.shape) == shape
                        and torch.isfinite(param).all().item()):
                    raise ValueError("Invalid spectral parameter state: " + name)
        except (TypeError, ValueError, RuntimeError) as exc:
            error_msgs.append(prefix + "spectral state: " + str(exc))
            return
        super()._load_from_state_dict(state_dict, prefix, local_metadata, strict,
                                     missing_keys, unexpected_keys, error_msgs)

    def _validate_inputs(self, heads, valid_mask):
        if not torch.is_tensor(heads) or not heads.is_floating_point():
            raise TypeError("heads must be a real floating-point tensor")
        if heads.ndim != 4 or any(n < 1 for n in heads.shape):
            raise ValueError("heads must have nonempty shape [B,H,T,D]")
        if heads.shape[1] != self.num_heads:
            raise ValueError("Input head count does not match num_heads")
        if not torch.is_tensor(valid_mask) or valid_mask.dtype != torch.bool:
            raise TypeError("valid_mask must be a boolean tensor")
        if tuple(valid_mask.shape) != (heads.shape[0], heads.shape[2]):
            raise ValueError("valid_mask must have shape [B,T]")
        if valid_mask.device != heads.device or self.alpha.device != heads.device:
            raise ValueError("Inputs, mask and gate must be on the same device")
        if not torch.isfinite(heads).all().item():
            raise ValueError("heads must be finite, including padded positions")
        lengths = valid_mask.sum(dim=1)
        if (lengths == 0).any().item():
            raise ValueError("Every example requires at least one valid token")
        if ((~valid_mask[:, :-1]) & valid_mask[:, 1:]).any().item():
            raise ValueError("valid_mask must describe a contiguous valid prefix")
        if not (torch.isfinite(self.alpha).all().item()
                and torch.isfinite(self.beta).item()):
            raise ValueError("Gate parameters must be finite")
        return lengths

    @staticmethod
    def _features(valid_heads):
        """Return per-head high-band energy and entropy on exactly valid tokens."""
        dtype = torch.float64 if valid_heads.dtype == torch.float64 else torch.float32
        signal = valid_heads.to(dtype=dtype)
        n = signal.shape[1]
        # Ratios are scale invariant. Detached per-head scaling prevents avoidable
        # overflow/underflow while retaining the analytic ratio derivatives.
        scale = signal.detach().abs().amax(dim=(1, 2), keepdim=True)
        scale = torch.where(scale > 0, scale, torch.ones_like(scale))
        signal = signal / scale
        spectrum = torch.fft.rfft(signal, dim=1)
        raw_power = (spectrum.real.square() + spectrum.imag.square()).sum(dim=-1)
        multiplicity = torch.full_like(raw_power, 2.0)
        multiplicity[:, 0] = 1.0
        if n % 2 == 0:
            multiplicity[:, -1] = 1.0  # Nyquist has no distinct negative partner.
        power = raw_power * multiplicity
        total = power.sum(dim=-1, keepdim=True)
        denominator = torch.where(total > 0, total, torch.ones_like(total))
        probabilities = power / denominator
        # k/n >= 0.25 exactly, without floating-point boundary ambiguity.
        high = 4 * torch.arange(power.shape[-1], device=signal.device) >= n
        energy = probabilities[:, high].sum(dim=-1)
        bins = power.shape[-1]
        if bins == 1:
            entropy = total.squeeze(-1) * 0.0
        else:
            safe_p = probabilities.clamp_min(torch.finfo(dtype).tiny)
            entropy = -(probabilities * safe_p.log()).sum(dim=-1) / math.log(bins)
        # Correct only possible floating-point excursions from theoretical bounds.
        return energy.clamp(0.0, 1.0), entropy.clamp(0.0, 1.0)

    def forward(self, heads, valid_mask):
        """Return (gated_heads, diagnostics); no calibration state is inferred.

        Diagnostics retain autograd for feature/weight inspection. In both modes
        E, entropy and observed_feature describe current inputs. The separate
        feature key is the actual gate input: observed_feature in dynamic mode,
        reference broadcast across examples in frozen_reference mode. Computing
        observed diagnostics in static mode is deliberate, not a speed claim.
        """
        if not self._reference_ready.item():
            raise RuntimeError("Explicit calibration reference is required in both modes")
        lengths = self._validate_inputs(heads, valid_mask)
        # Group by exact prefix length, never pad/average spectra across examples.
        # Flattening independent example/head signals amortizes FFT launches while
        # preserving the per-example statistic and its analytic gradients.
        length_values = lengths.tolist()
        dtype = torch.float64 if heads.dtype == torch.float64 else torch.float32
        energy = torch.zeros(heads.shape[:2],dtype=dtype,device=heads.device)
        entropy = torch.zeros_like(energy)
        for length in sorted(set(length_values)):
            selected = [index for index,value in enumerate(length_values) if value == length]
            indices = torch.tensor(selected,dtype=torch.long,device=heads.device)
            signals = heads.index_select(0,indices)[:,:,:length,:]
            e,h = self._features(signals.reshape(-1,length,heads.shape[-1]))
            energy = energy.index_copy(0,indices,e.reshape(len(selected),self.num_heads))
            entropy = entropy.index_copy(0,indices,h.reshape(len(selected),self.num_heads))
        observed = energy * entropy
        reference = self.reference.to(dtype=observed.dtype)
        feature = (observed if self.mode == "dynamic"
                   else reference.unsqueeze(0).expand(heads.shape[0], -1))
        weights = (1.0 + self.alpha.to(dtype=observed.dtype)
                   + self.beta.to(dtype=observed.dtype).tanh() * (feature - 0.5))
        gated = heads * weights.to(dtype=heads.dtype)[:, :, None, None]
        diagnostics = {"energy_ratio": energy, "entropy": entropy,
                       "observed_feature": observed, "feature": feature,
                       "weights": weights, "reference": reference,
                       "valid_lengths": lengths}
        return gated, diagnostics
