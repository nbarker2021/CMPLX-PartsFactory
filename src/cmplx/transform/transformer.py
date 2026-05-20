"""
GeometricTransformer — Slot 48 stack.

Composes the embed → N × block → head shape:

  1. `MorphonicTokenizer.tokenize(content)` returns the initial
     HiddenState and TokenizedRibbon.
  2. The stack runs `num_layers` `GeometricTransformerLayer` blocks.
     Each layer enforces its NSL gate, mints a layer trace, and caches
     the residual through SpeedLight when available.
  3. The output head delegates to `MorphonicEversionNetwork.forward`
     (just stages 0–6) for canonical ribbon projection. The transformer
     uses only the head's `result` dict, never its training surface.
  4. The full forward is keyed and cached through SpeedLight so the
     second identical call returns `speedlight_hit=True`.

All ports are looked up lazily through `bridge.py` so the transformer
imports cheaply.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .shell import MorphonShell

import numpy as np

from cmplx.engine.eversion.network import MorphonicEversionNetwork

from .bridge import (
    ensure_bootstrapped,
    get_cache_provider,
    get_receipt_provider,
    has_provider,
)
from .config import TransformerConfig
from .layer import GeometricTransformerLayer
from .tokenizer import MorphonicTokenizer
from .token_index.substrate_epoch import compute_substrate_epoch
from .types import HiddenState, LayerTrace, ShellViolation, TokenizedRibbon, TransformerOutput

logger = logging.getLogger(__name__)


def _config_digest(config: TransformerConfig) -> str:
    """Stable digest of the config tree — used as part of the cache key."""
    safe = {
        "num_layers": config.num_layers,
        "n_domains": config.n_domains,
        "hidden_dim": config.hidden_dim,
        "seq_length": config.seq_length,
        "output_mode": config.output_mode,
        "tokenizer": asdict(config.tokenizer),
        "layers": [
            {
                "attention": asdict(layer.attention),
                "ffn": asdict(layer.ffn),
                "nsl_mode": layer.nsl_mode,
                "nsl_budget": layer.nsl_budget,
                "use_speedlight_residual": layer.use_speedlight_residual,
            }
            for layer in (config.layers or [])
        ],
    }
    return hashlib.sha256(
        json.dumps(safe, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


class GeometricTransformer:
    """The full Slot 48 stack."""

    def __init__(
        self,
        config: Optional[TransformerConfig] = None,
        *,
        shell: Optional["MorphonShell"] = None,
    ) -> None:
        self.config = config or TransformerConfig()
        self.shell = shell
        if self.config.register_ports_on_init:
            ensure_bootstrapped(mmdb_path=self.config.mmdb_path)

        self.tokenizer = MorphonicTokenizer(
            self.config.tokenizer,
            hidden_dim=self.config.hidden_dim or 24,
            seq_length=self.config.seq_length,
        )
        self.layers = [
            GeometricTransformerLayer(layer_cfg)
            for layer_cfg in (self.config.layers or [])
        ]
        # Eversion head: a single instance is reused; receipts are
        # snapshotted per forward call.
        self.head = MorphonicEversionNetwork(n_domains=self.config.n_domains)
        self._config_digest = _config_digest(self.config)

    def _substrate_epoch(self) -> str:
        store = getattr(self.shell, "store", None) if self.shell is not None else None
        if store is not None:
            try:
                epoch_fn = getattr(store, "substrate_epoch", None)
                if callable(epoch_fn):
                    return str(epoch_fn())
                return compute_substrate_epoch(store._conn)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("substrate_epoch failed: %s", exc)
        return "0"

    # ── Public API ──────────────────────────────────────────────────────

    def forward(
        self,
        ribbon: Any,
        *,
        context_morphon: Optional[Any] = None,
    ) -> TransformerOutput:
        # 1. Embed
        tokenized = self.tokenizer.tokenize(ribbon, context_morphon=context_morphon)
        meta: dict[str, Any] = {"canonical_info": tokenized.canonical_info}
        ribbon_text = ribbon if isinstance(ribbon, str) else str(ribbon)
        if len(ribbon_text) >= 1:
            from .metrics import compute_token_metrics

            anchor = ribbon_text[:8].ljust(8, "a")
            meta["token_metrics"] = compute_token_metrics(anchor).as_dict()
        state = HiddenState(
            tensor=tokenized.tensor,
            morphon=tokenized.morphon,
            metadata=meta,
        )

        # Full-forward cache key — used both for SpeedLight hit detection
        # and as the public `cache_key` return field.
        substrate_epoch = self._substrate_epoch()
        cache_key = (
            f"transform::{self._config_digest}::{substrate_epoch}::{tokenized.content_hash}"
        )

        # 2. SpeedLight whole-forward cache
        cached_payload = self._read_full_cache(cache_key)
        if cached_payload is not None:
            return self._inflate_cached(cache_key, cached_payload, tokenized.morphon)

        # 3. Layer stack
        traces: list[LayerTrace] = []
        for idx, layer in enumerate(self.layers):
            if self.config.hook_pre_layer is not None:
                try:
                    self.config.hook_pre_layer(state, idx, self.config.layers[idx])  # type: ignore[index]
                except Exception as exc:  # pragma: no cover - hooks are user code
                    logger.warning("hook_pre_layer raised at idx %d: %s", idx, exc)
            state, trace = layer.forward(state, idx, cache_namespace=self._config_digest)
            traces.append(trace)
            if self.config.hook_post_layer is not None:
                try:
                    self.config.hook_post_layer(state, idx, self.config.layers[idx])  # type: ignore[index]
                except Exception as exc:  # pragma: no cover - hooks are user code
                    logger.warning("hook_post_layer raised at idx %d: %s", idx, exc)

        # 4. Head
        head_result = self.head.forward(ribbon)
        ribbon_out = self._project_output(ribbon, tokenized, state, head_result)

        if self.config.shell_bind:
            self._shell_bind_ribbon_out(ribbon_out, traces)

        # 5. Mint a single forward receipt when the port is registered.
        receipts: list[Any] = []
        if has_provider("receipt"):
            try:
                receipt = get_receipt_provider().mint(
                    receipt_type="PROCESS",
                    atom_id=tokenized.morphon.id,
                    operation="transformer.forward",
                    delta_phi=float(sum(t.delta_phi_attention + t.delta_phi_ffn for t in traces)),
                    payload={
                        "cache_key": cache_key,
                        "num_layers": len(self.layers),
                        "snap_key": tokenized.canonical_info.get("snap_key", "")[:16],
                        "config_digest": self._config_digest,
                        "substrate_epoch": substrate_epoch,
                    },
                )
                receipts.append(receipt)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("receipt mint failed: %s", exc)

        output = TransformerOutput(
            ribbon_out=ribbon_out,
            final_morphon=state.morphon,
            cache_key=cache_key,
            receipts=receipts,
            layer_traces=traces,
            speedlight_hit=False,
            summary={
                "config_digest": self._config_digest,
                "substrate_epoch": substrate_epoch,
                "head_committed": bool(head_result.get("committed", False)),
                "head_loss_total": float(head_result.get("loss", {}).get("total", 0.0)),
                "snap_key": tokenized.canonical_info.get("snap_key", ""),
                "lane": tokenized.canonical_info.get("lane", ""),
                "digital_root": tokenized.canonical_info.get("digital_root", 0),
            },
        )

        self._write_full_cache(cache_key, output, tokenized)
        return output

    # ── Internals ───────────────────────────────────────────────────────

    def _shell_bind_ribbon_out(self, ribbon_out: Any, traces: list[LayerTrace]) -> None:
        if self.shell is None:
            return
        if isinstance(ribbon_out, dict):
            token = str(ribbon_out.get("snap_key", ""))[:8].ljust(8, "a")
        else:
            token = str(ribbon_out)[:8].ljust(8, "a")
        admit = self.shell.admit(token, lang=self.shell.config.language)
        if not admit.admitted:
            if traces:
                traces[-1].shell_violation = True
                traces[-1].shell_reason = admit.reason
            raise ShellViolation(token, admit.reason)

    def _project_output(
        self,
        ribbon: Any,
        tokenized: TokenizedRibbon,
        state: HiddenState,
        head_result: dict,
    ) -> Any:
        mode = self.config.output_mode
        if mode == "raw":
            return ribbon
        if mode == "etp":
            if tokenized.etp_program is not None:
                return tokenized.etp_program
            if has_provider("symbolic"):
                from .bridge import get_symbolic_provider

                try:
                    return get_symbolic_provider().encode_to_etp(state.morphon)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("etp output fallback: %s", exc)
        # default: canonical JSON
        return {
            "snap_key": head_result.get("snap_key", ""),
            "morphon_id": state.morphon.id,
            "digital_root": head_result.get("dr"),
            "lane": head_result.get("lane"),
            "committed": head_result.get("committed", False),
            "brs_all_pass": head_result.get("brs_all_pass", False),
            "delta_phi": head_result.get("cumulative_delta_phi", 0.0),
            "loss_total": head_result.get("loss", {}).get("total"),
            "receipt_hash": head_result.get("receipt_hash", ""),
        }

    def _read_full_cache(self, cache_key: str) -> Optional[dict]:
        if not has_provider("cache"):
            return None
        try:
            return get_cache_provider().get(cache_key)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("speedlight whole-forward get failed: %s", exc)
            return None

    def _write_full_cache(
        self,
        cache_key: str,
        output: TransformerOutput,
        tokenized: TokenizedRibbon,
    ) -> None:
        if not has_provider("cache"):
            return
        try:
            get_cache_provider().put(
                cache_key,
                {
                    "ribbon_out": output.ribbon_out,
                    "morphon_id": tokenized.morphon.id,
                    "summary": output.summary,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("speedlight whole-forward put failed: %s", exc)

    def _inflate_cached(
        self,
        cache_key: str,
        payload: dict,
        morphon: Any,
    ) -> TransformerOutput:
        return TransformerOutput(
            ribbon_out=payload.get("ribbon_out"),
            final_morphon=morphon,
            cache_key=cache_key,
            receipts=[],
            layer_traces=[],
            speedlight_hit=True,
            summary=dict(payload.get("summary", {})),
        )


__all__ = ["GeometricTransformer"]
