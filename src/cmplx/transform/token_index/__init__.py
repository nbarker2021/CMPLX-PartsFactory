"""
cmplx.transform.token_index — substrate-first quad-bond token index.

The index is built by composing three structural layers plus a case
layer, with iterative cache-driven warm-starts at every step:

  1. Bond enumeration  — outer ring, then first / second involution rings.
  2. Case shift        — LOWER, UPPER, LEAD_LEFT/RIGHT/BOTH, CAMEL_INNER,
                          ALTERNATING, PALINDROME. The seam cases capture
                          inter-quad case transitions.
  3. Language filter   — pluggable; defaults: `any` (permissive) and
                          `english` (bigram-based plausibility).
  4. Warm-start probe  — for every prospective entry, look up cache by
                          exact concat, then case-base, then predecessor,
                          then geometric neighbor. Defined / vague / cold
                          classification feeds the build stats.

Public surface:

    from cmplx.transform.token_index import (
        TokenIndexBuilder, TokenIndexBuildConfig,
        QuadBond, CaseMode, LanguageFilter,
        TokenIndexStore,
    )

    result = TokenIndexBuilder(TokenIndexBuildConfig(levels=(1, 2))).build()
    print(result.as_dict())
"""
from __future__ import annotations

from .bonds import (
    DEFAULT_ALPHABET,
    DEFAULT_BASE_CHAR,
    QUAD_LEN,
    QuadBond,
    count_bonds,
    enumerate_bonds,
    enumerate_levels,
)
from .builder import BuildResult, TokenIndexBuildConfig, TokenIndexBuilder
from .case import (
    DEFAULT_CASE_MODES,
    SEAM_CASE_MODES,
    CaseMode,
    apply_case,
    case_variants,
)
from .language import (
    LanguageFilter,
    REGISTRY,
    any_filter,
    english_filter,
    get_filter,
)
from .store import TokenIndexStore
from .substrate_epoch import compute_substrate_epoch, notify_substrate_mutation
from .template_frame import (
    AdmitSet,
    ForcedCellReport,
    SlotCoverage,
    TemplateFrame,
    template_report,
)
from .warmstart import (
    IndexEntryPayload,
    WarmStartHit,
    WarmStartLookup,
    WarmStartOutcome,
    WarmStartStats,
)

from ..meaning_store import AddressMeaningStore, MeaningRow

__all__ = [
    # bonds
    "DEFAULT_ALPHABET",
    "DEFAULT_BASE_CHAR",
    "QUAD_LEN",
    "QuadBond",
    "count_bonds",
    "enumerate_bonds",
    "enumerate_levels",
    # case
    "DEFAULT_CASE_MODES",
    "SEAM_CASE_MODES",
    "CaseMode",
    "apply_case",
    "case_variants",
    # language
    "LanguageFilter",
    "REGISTRY",
    "any_filter",
    "english_filter",
    "get_filter",
    # warmstart
    "IndexEntryPayload",
    "WarmStartHit",
    "WarmStartLookup",
    "WarmStartOutcome",
    "WarmStartStats",
    # substrate epoch
    "compute_substrate_epoch",
    "notify_substrate_mutation",
    # store + builder
    "TokenIndexStore",
    "TokenIndexBuilder",
    "TokenIndexBuildConfig",
    "BuildResult",
    # template frame
    "TemplateFrame",
    "SlotCoverage",
    "AdmitSet",
    "ForcedCellReport",
    "template_report",
    # meaning table
    "AddressMeaningStore",
    "MeaningRow",
]
