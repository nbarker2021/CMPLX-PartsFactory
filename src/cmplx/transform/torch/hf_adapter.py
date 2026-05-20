"""
HuggingFace adapter stub — maps Slot 48 config to external trainer hooks.

Full HF integration is out of scope; this module documents the boundary and
exports admit masks over the indexed concat set when a shell is provided.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from ..config import ProductionTransformerConfig, TransformerConfig
from ..crystal_pack import CrystalPackager, LoadedCrystal
from ..shell import MorphonShell
from ..transformer import GeometricTransformer


@dataclass
class HFAdapterConfig:
    model_name: str = "cmplx/geometric-transformer-stub"
    admit_mask_export: bool = True
    num_layers: int = 8
    production: bool = False


class HuggingFaceAdapterStub:
    """Stub adapter: wraps GeometricTransformer for HF-style train/eval loops."""

    def __init__(
        self,
        config: Optional[TransformerConfig] = None,
        *,
        hf_config: Optional[HFAdapterConfig] = None,
        shell: Optional[MorphonShell] = None,
    ) -> None:
        self.hf_config = hf_config or HFAdapterConfig()
        if config is not None:
            tcfg = config
        elif self.hf_config.production:
            tcfg = ProductionTransformerConfig(register_ports_on_init=False)
        else:
            tcfg = TransformerConfig(
                num_layers=self.hf_config.num_layers,
                register_ports_on_init=False,
            )
        self.transformer = GeometricTransformer(tcfg, shell=shell)
        self.shell = shell

    def forward(self, ribbon: Any) -> dict[str, Any]:
        out = self.transformer.forward(ribbon)
        return {
            "ribbon_out": out.ribbon_out,
            "cache_key": out.cache_key,
            "speedlight_hit": out.speedlight_hit,
            "model": self.hf_config.model_name,
        }

    def export_admit_mask(self, tokens: list[str]) -> list[bool]:
        if not self.hf_config.admit_mask_export:
            return [True] * len(tokens)
        if self.shell is None:
            return [False] * len(tokens)
        mask: list[bool] = []
        for token in tokens:
            concat = token[:8].ljust(8, "a")
            result = self.shell.admit(concat)
            mask.append(bool(result.admitted))
        return mask


@dataclass
class TrainerHarnessSketch:
    """
    Crystal → shell → admit-mask batch → stub loss loop (no real HF weights).

    Integration point for future custom models; substrate law stays admit + crystal.
    """

    crystal_bundle: Path
    tokens: Sequence[str] = field(default_factory=list)
    max_steps: int = 1

    _loaded: Optional[LoadedCrystal] = field(default=None, repr=False)
    _adapter: Optional[HuggingFaceAdapterStub] = field(default=None, repr=False)

    def load(self) -> LoadedCrystal:
        if self._loaded is None:
            self._loaded = CrystalPackager().load(self.crystal_bundle)
        return self._loaded

    def adapter(self) -> HuggingFaceAdapterStub:
        if self._adapter is None:
            loaded = self.load()
            self._adapter = HuggingFaceAdapterStub(
                hf_config=HFAdapterConfig(production=True, admit_mask_export=True),
                shell=loaded.shell,
            )
        return self._adapter

    def admit_mask_batch(self, tokens: Optional[Sequence[str]] = None) -> list[bool]:
        batch = list(tokens if tokens is not None else self.tokens)
        return self.adapter().export_admit_mask(batch)

    def stub_train_step(self, tokens: Optional[Sequence[str]] = None) -> dict[str, Any]:
        """One masked batch step: count admitted tokens, return stub loss metadata."""
        mask = self.admit_mask_batch(tokens)
        admitted = sum(1 for m in mask if m)
        loss_stub = 0.0 if admitted == 0 else 1.0 / admitted
        return {
            "batch_size": len(mask),
            "admitted": admitted,
            "loss_stub": loss_stub,
            "crystal_id": self.load().crystal.crystal_id,
        }


__all__ = [
    "HFAdapterConfig",
    "HuggingFaceAdapterStub",
    "TrainerHarnessSketch",
]
