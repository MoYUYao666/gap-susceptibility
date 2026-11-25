"""Scoped CLIP attention hooks for the explicitly adapted spectral head gate.

No training, model loading, layer search or protocol mutation occurs here.
Reference JSON plus every trainable tensor must be bound by the parent identity.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import json
import math
import numbers

import torch
from torch import nn

from .spectral import SpectralHeadGate


__all__ = ["HookController"]


class HookController:
    """Attach both-tower early/late gates to an AdaptedCLIP instance.

    A text_context(boolean_mask) must enclose each enabled text forward. The
    actual text tower input must contain that same mask and exactly one valid
    EOS at its last valid position. This is encoder head-output gating; full
    valid-token spectral statistics do not preserve autoregressive causality.

    This object owns hook handles and model.spectral_gates. close() removes
    both; export references/trainables before closing. Use one controller per
    model, serial forwards and no checkpoint recomputation outside its contexts.
    """

    PRESETS = {"early": (0, 1, 2), "late": (9, 10, 11)}

    def __init__(self, model, preset="early", mode="dynamic"):
        if preset not in self.PRESETS:
            raise ValueError("preset must be early or late")
        if mode not in ("dynamic", "frozen_reference"):
            raise ValueError("mode must be dynamic or frozen_reference")
        if hasattr(model, "spectral_gates"):
            raise ValueError("Model already has a spectral gate controller")
        if not isinstance(model, nn.Module) or not callable(getattr(model, "frozen_baseline", None)):
            raise TypeError("model must expose the AdaptedCLIP frozen_baseline context")
        self.model, self.preset, self.mode = model, preset, mode
        self.layers = self.PRESETS[preset]
        self._closed = False
        self._locked = False
        self._mask = ContextVar("spectral_text_mask", default=None)
        self._disabled = ContextVar("spectral_disabled", default=False)
        self._collecting = ContextVar("spectral_collecting", default=False)
        self._depth = ContextVar("spectral_context_depth", default=0)
        self._handles = []
        self._layout = {}
        self._sums, self._counts = {}, {}
        self._locked_counts = None
        self.last_diagnostics = {}
        gates = nn.ModuleDict()
        targets = []
        for tower_name in ("text", "vision"):
            tower = getattr(model.clip, tower_name + "_model")
            if len(tower.encoder.layers) != 12:
                raise ValueError("Both CLIP towers must have exactly twelve layers")
            for index in self.layers:
                attention = tower.encoder.layers[index].self_attn
                width, heads = attention.embed_dim, attention.num_heads
                if heads < 1 or width % heads:
                    raise ValueError("Attention width must be divisible by its head count")
                key = f"{tower_name}_{index}"
                projection = attention.out_proj
                gates[key] = SpectralHeadGate(heads, mode=mode).to(
                    device=projection.weight.device, dtype=projection.weight.dtype)
                self._layout[key] = {"tower": tower_name, "layer": index,
                                     "width": width, "heads": heads, "head_dim": width // heads}
                self._sums[key] = torch.zeros(heads, dtype=torch.float64)
                self._counts[key] = 0
                targets.append((key, projection))
        self.gates = gates
        self._eos = model.clip.config.text_config.eos_token_id
        if isinstance(self._eos, bool) or not isinstance(self._eos, int):
            raise ValueError("A single integer text EOS token id is required")
        model.add_module("spectral_gates", gates)
        try:
            self._handles.append(model.clip.text_model.register_forward_pre_hook(
                self._guard_text, with_kwargs=True))
            for key, projection in targets:
                self._handles.append(projection.register_forward_pre_hook(self._make_hook(key)))
        except Exception:
            self.close()
            raise

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("HookController is closed")

    @staticmethod
    def _check_mask(mask):
        if not torch.is_tensor(mask) or mask.dtype != torch.bool:
            raise TypeError("Text mask must be a boolean tensor")
        if mask.ndim != 2 or any(n < 1 for n in mask.shape):
            raise ValueError("Text mask must have nonempty shape [B,T]")
        if (~mask[:, 0]).any().item() or ((~mask[:, :-1]) & mask[:, 1:]).any().item():
            raise ValueError("Text mask must be a nonempty valid prefix through EOS")

    @contextmanager
    def text_context(self, attention_mask):
        """Bind a copied boolean mask to the current candidate batch; nest safely."""
        self._ensure_open()
        self._check_mask(attention_mask)
        mask_token = self._mask.set(attention_mask.detach().clone())
        depth_token = self._depth.set(self._depth.get() + 1)
        try:
            yield self
        finally:
            self._depth.reset(depth_token)
            self._mask.reset(mask_token)

    @contextmanager
    def disabled(self):
        """True gate/guard bypass, with no no_grad or LoRA state modification."""
        self._ensure_open()
        if self._collecting.get():
            raise RuntimeError("Cannot disable hooks inside calibration collection")
        token = self._disabled.set(True)
        depth_token = self._depth.set(self._depth.get() + 1)
        try:
            yield self
        finally:
            self._depth.reset(depth_token)
            self._disabled.reset(token)

    def _guard_text(self, module, args, kwargs):
        if self._disabled.get():
            return None
        mask = self._mask.get()
        if mask is None:
            raise RuntimeError("Enabled text forward requires a current text mask context")
        ids = kwargs.get("input_ids", args[0] if args else None)
        actual = kwargs.get("attention_mask", args[1] if len(args) > 1 else None)
        self._check_mask(actual)
        if not (torch.is_tensor(ids) and ids.ndim == 2 and ids.dtype in (torch.int32, torch.int64)):
            raise ValueError("Text input_ids must be an integer [B,T] tensor")
        if (tuple(ids.shape) != tuple(mask.shape) or tuple(actual.shape) != tuple(mask.shape)
                or ids.device != mask.device or actual.device != mask.device
                or not torch.equal(actual, mask)):
            raise ValueError("Text mask context must match the actual current text batch")
        lengths = mask.sum(-1)
        ends = ids.gather(1, (lengths - 1).unsqueeze(1)).squeeze(1)
        valid_eos = ((ids == self._eos) & mask).sum(-1)
        if (ends != self._eos).any().item() or (valid_eos != 1).any().item():
            raise ValueError("Text mask must include exactly the first EOS and no later valid tokens")
        return None

    def _make_hook(self, key):
        def before_projection(module, args):
            if self._disabled.get():
                return None
            if not args or not torch.is_tensor(args[0]):
                raise ValueError("Attention out_proj must receive a [B,T,width] tensor")
            value = args[0]
            layout = self._layout[key]
            if value.ndim != 3 or value.shape[-1] != layout["width"]:
                raise ValueError("Unexpected attention out_proj shape")
            batch, tokens, width = value.shape
            heads = value.reshape(batch, tokens, layout["heads"], layout["head_dim"]).transpose(1, 2)
            mask = (self._mask.get() if layout["tower"] == "text"
                    else torch.ones(batch, tokens, dtype=torch.bool, device=value.device))
            if mask is None:
                raise RuntimeError("Text attention requires a current text mask context")
            gate = self.gates[key]
            if self._collecting.get():
                lengths = gate._validate_inputs(heads, mask)
                features = []
                for index, length in enumerate(lengths.tolist()):
                    energy, entropy = gate._features(heads[index, :, :length, :])
                    features.append((energy * entropy).detach().to(device="cpu", dtype=torch.float64))
                self._sums[key] += torch.stack(features).sum(0)
                self._counts[key] += batch
                # Returning None preserves the exact original tensor and graph.
                return None
            gated, diagnostics = gate(heads, mask)
            self.last_diagnostics[key] = {name: tensor.detach().clone()
                                          for name, tensor in diagnostics.items()}
            flat = gated.transpose(1, 2).reshape(batch, tokens, width)
            return (flat,) + args[1:]
        return before_projection

    @contextmanager
    def calibration(self):
        """Collect ungated native frozen eval features, explicitly and label-free.

        Counts weight examples, not batches. Multiple contexts accumulate. An
        exceptional context rolls its local statistics back. Caller must supply
        approved source calibration inputs and invoke this before optimization.
        """
        self._ensure_open()
        if self._locked or self._collecting.get() or self._disabled.get():
            raise RuntimeError("Calibration requires unlocked, enabled, non-nested collection")
        old_sums = {key: value.clone() for key, value in self._sums.items()}
        old_counts = self._counts.copy()
        training = [(module, module.training) for module in self.model.modules()]
        token = self._collecting.set(True)
        depth_token = self._depth.set(self._depth.get() + 1)
        try:
            self.model.eval()
            with self.model.frozen_baseline(), torch.no_grad():
                yield self
        except BaseException:
            self._sums, self._counts = old_sums, old_counts
            raise
        finally:
            for module, flag in training:
                module.training = flag
            self._depth.reset(depth_token)
            self._collecting.reset(token)

    def calibration_statistics(self):
        """Return copies of counts and per-head example means, or None if empty."""
        self._ensure_open()
        return {key: {"count": self._counts[key],
                      "mean": (self._sums[key] / self._counts[key]).tolist()
                      if self._counts[key] else None} for key in self.gates}

    def _check_unlocked(self):
        self._ensure_open()
        if self._locked or any(g._reference_ready.item() for g in self.gates.values()):
            raise RuntimeError("References are already locked; construct a fresh controller")
        if self._depth.get():
            raise RuntimeError("Reference finalization must occur outside active contexts")

    def freeze_references(self):
        """Explicit one-shot freeze after all selected layers/towers were observed."""
        self._check_unlocked()
        if any(count < 1 for count in self._counts.values()):
            raise RuntimeError("Every selected tower/layer needs calibration observations")
        means = {key: self._sums[key] / self._counts[key] for key in self.gates}
        checked = {key: self.gates[key]._checked_reference(value) for key, value in means.items()}
        for key, value in checked.items():
            self.gates[key].set_reference(value)
        self._locked = True
        self._locked_counts = self._counts.copy()

    def _configuration(self):
        return {"controller_version": 1, "spectral_version": 1,
                "preset": self.preset, "layers": list(self.layers), "mode": self.mode,
                "towers": ["text", "vision"], "text_eos_token_id": self._eos,
                "text_mask": "boolean nonempty valid prefix through first EOS",
                "vision_mask": "all tokens valid, including CLS",
                "gates": {key: dict(layout, reference_dtype=str(self.gates[key]._reference.dtype))
                          for key, layout in self._layout.items()},
                "spectral": {"input_layout": "B,H,T,D", "axis": "valid-prefix token axis",
                             "power_reduction": "sum feature dimension",
                             "one_sided_multiplicity": "DC=1, even Nyquist=1, others=2",
                             "high_band_cycles_per_token": 0.25,
                             "entropy_normalization": "log(floor(valid_length/2)+1)",
                             "zero_energy_feature": 0.0},
                "gate": {"formula": "1+alpha+tanh(beta)*(f-0.5)",
                         "alpha": "per-head", "beta": "per-layer scalar",
                         "dynamic_f": "current per-example E*entropy",
                         "frozen_reference_f": "locked per-head calibration mean"}}

    def export_references(self):
        """Return complete finite JSON values/config; not a trainable checkpoint."""
        self._ensure_open()
        if not self._locked:
            raise RuntimeError("References must be explicitly frozen or loaded before export")
        payload = {"schema_version": 1, "configuration": self._configuration(),
                   "references": {key: gate.reference.cpu().tolist() for key, gate in self.gates.items()},
                   "calibration_counts": self._locked_counts.copy()}
        return json.loads(json.dumps(payload, allow_nan=False))

    def load_references(self, payload):
        """Strict, prevalidated one-shot restore into a fresh matching controller."""
        self._check_unlocked()
        if not isinstance(payload, dict) or set(payload) != {
                "schema_version", "configuration", "references", "calibration_counts"}:
            raise ValueError("Reference JSON has missing or unexpected fields")
        if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
            raise ValueError("Unsupported reference JSON schema")
        if json.dumps(payload["configuration"], sort_keys=True, allow_nan=False) != json.dumps(
                self._configuration(), sort_keys=True, allow_nan=False):
            raise ValueError("Reference mode/layer/head configuration mismatch")
        refs, counts = payload["references"], payload["calibration_counts"]
        if not isinstance(refs, dict) or not isinstance(counts, dict) or (
                set(refs) != set(self.gates) or set(counts) != set(self.gates)):
            raise ValueError("Reference JSON must cover exactly all selected gates")
        checked = {}
        for key, gate in self.gates.items():
            values = refs[key]
            if not isinstance(values, list) or len(values) != gate.num_heads:
                raise ValueError("Reference values must have exactly one mean per head")
            if any(isinstance(v, bool) or not isinstance(v, numbers.Real)
                   or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
                raise ValueError("Reference means must be finite real values in [0,1]")
            if type(counts[key]) is not int or counts[key] < 1:
                raise ValueError("Calibration counts must be positive integers")
            # Construct in the declared buffer dtype: torch.as_tensor(list)
            # otherwise defaults to float32 and truncates float64 references.
            tensor = torch.tensor(values, dtype=gate._reference.dtype,
                                  device=gate._reference.device)
            checked[key] = gate._checked_reference(tensor)
        for key, values in checked.items():
            self.gates[key].set_reference(values)
        self._locked_counts = counts.copy()
        self._locked = True

    def close(self):
        """Remove only owned handles and gate registration; safe to call twice."""
        if self._closed:
            return
        if self._depth.get():
            raise RuntimeError("Cannot close HookController inside an active context")
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        if getattr(self.model, "spectral_gates", None) is self.gates:
            delattr(self.model, "spectral_gates")
        self.last_diagnostics.clear()
        self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
