"""LabelerService — 14-pass SNAP semantic saturation labeler."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("labeler_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))


class SNAPLabel:
    def __init__(self, name: str, value: Any = None, source: str = "",
                 pass_num: int = 1, confidence: float = 1.0,
                 parent_labels: list = None):
        self.name = name
        self.value = value
        self.source = source or f"pass{pass_num}"
        self.pass_num = pass_num
        self.confidence = confidence
        self.parent_labels = parent_labels or []


DOMAIN_KEYWORDS = {
    "geometry": ["geometry", "e8", "lattice", "vector", "manifold", "weyl", "leech", "niemeier", "morsr", "alena"],
    "morphonic": ["morphon", "conservation", "delta_phi", "field", "potential", "coupling"],
    "tarpit": ["tarpit", "glyph", "grain", "bond", "e6", "token", "encode", "ribbon"],
    "snap": ["snap", "label", "classify", "domain", "layer", "pass", "saturate"],
    "mdhg": ["mdhg", "hash", "planet", "city", "hierarchy", "address", "fabric"],
    "agent": ["agent", "brain", "epoch", "spawn", "death", "wallet", "nano", "sidecar"],
    "orchestration": ["daemon", "crt", "channel", "dispatch", "schedule", "breathability"],
    "auditing": ["sap", "sentinel", "arbiter", "governance", "audit", "deception"],
    "network": ["board", "post", "thread", "bounty", "quorum", "broadcast", "subscribe"],
    "caching": ["speedlight", "cache", "receipt", "merkle", "idempotent"],
    "simulation": ["ca", "cellular", "automata", "civilization", "wolfram", "simulation"],
    "database": ["pg", "postgresql", "sql", "table", "insert", "query", "atom"],
    "cryptographic": ["hash", "sha256", "merkle", "signature", "receipt_chain"],
    "testing": ["test", "assert", "verify", "validate", "check"],
}

FAMILY_PATTERNS = {
    "family_e8": [r"\be8\b", r"\bleech\b", r"\bniemeier\b", r"\bweyl\b", r"\bcartan\b", r"\bcoxeter\b", r"\blattice\b"],
    "family_morphonic": [r"\bmorphon\b", r"\bfield\b", r"\bpotential\b", r"\bcoupling\b", r"\bconservation\b"],
    "family_aletheia": [r"\baletheia\b", r"\btruth\b", r"\beverification\b", r"\bproof\b"],
    "family_tarpit": [r"\btarpit\b", r"\bglyph\b", r"\btape\b", r"\bjot\b", r"\bwall\b", r"\bribbon\b"],
    "family_cqe": [r"\bcqe\b", r"\bmonolith\b", r"\bprocessor\b", r"\bgrain_chain\b"],
    "family_agent": [r"\bagent\b", r"\bbrain\b", r"\bspawn\b", r"\bdaemon\b", r"\bnanobot\b", r"\bsidecar\b"],
    "family_snap": [r"\bsnap\b", r"\blabel\b", r"\bsaturate\b", r"\bmass\b"],
    "family_mdhg": [r"\bmdhg\b", r"\bplanet\b", r"\bhash.?fabric\b", r"\bhierarch\b"],
}

RETURN_TYPE_PATTERNS = {
    "return_dict": r"return\s*\{", "return_list": r"return\s*\[",
    "return_none": r"return\s*None\b|return\s*$", "return_generator": r"\byield\b",
}

EFFECT_PATTERNS = {
    "effect_writes_storage": r"\.write\b|\.save\b|\.dump\b|\.to_file\b|open\(.+['\"]w",
    "effect_reads_storage": r"\.read\b|\.load\b|open\(.+['\"]r",
    "effect_raises": r"\braise\b",
    "effect_accumulates": r"\b\w+\s*[+]=|\.append\b|\.extend\b",
    "effect_iterates": r"\bfor\s+\w+\s+in\b|\bwhile\b",
    "effect_branches": r"\bif\b.+:",
    "effect_uses_numpy": r"\bnp\.\b|\bnumpy\b",
    "effect_mutates_state": r"\bself\.\w+\s*=",
}

INPUT_TYPE_PATTERNS = {
    "input_vector": r"\bvector\b|\barray\b|\bnp\.array\b|\btensor\b|\bcoords\b",
    "input_text": r"\bstr\b|\btext\b|\bcontent\b|\bmessage\b|\bprompt\b",
    "input_structured": r"\bdict\b|\bjson\b|\bconfig\b|\bschema\b|\brecord\b",
    "input_path": r"\bpath\b|\bfile\b|\bfilename\b|\bdirectory\b",
    "input_db_handle": r"\bconn\b|\bcursor\b|\bsession\b|\bdb\b|\bengine\b",
}

TRANSFORM_SIGNATURES = {
    "xform_validate": [r"\bvalidat\w*\b", r"\bcheck\b", r"\bverif\w*\b"],
    "xform_merge": [r"\bmerge\b", r"\bjoin\b", r"\bcombine\b", r"\bunion\b"],
    "xform_split": [r"\bsplit\b", r"\bpartition\b", r"\bchunk\b", r"\bshard\b"],
    "xform_filter": [r"\bfilter\b", r"\bwhere\b", r"\bselect\b", r"\bexclude\b"],
    "xform_sort": [r"\bsort\b", r"\border\b", r"\brank\b"],
    "xform_compare": [r"\bcompare\b", r"\bdiff\b", r"\bsimilar\b", r"\bdistance\b"],
    "xform_encode": [r"\bencode\b", r"\bserializ\w*\b", r"\bcompress\b", r"\bpack\b"],
}

SUBSYSTEM_DETECTORS = {
    "sub_geometry": [r"\blattice\b", r"\bmanifold\b", r"\be8\b", r"\bweyl\b", r"\bleech\b", r"\bniemeier\b"],
    "sub_hashing": [r"\bsha\b", r"\bhash\b", r"\bdigest\b", r"\bhmac\b", r"\bmd5\b"],
    "sub_auditing": [r"\baudit\b", r"\blog\b", r"\btrace\b", r"\bsap\b", r"\bsentinel\b"],
    "sub_caching": [r"\bcache\b", r"\blru\b", r"\bmemo\b", r"\bspeedlight\b", r"\bidempotent\b"],
    "sub_database": [r"\bsql\b", r"\bpg\b", r"\binsert\b", r"\bselect\b", r"\bpostgres\b"],
    "sub_network": [r"\bhttp\b", r"\burl\b", r"\brequest\b", r"\bapi\b", r"\bendpoint\b"],
    "sub_validation": [r"\bassert\b", r"\bcheck\b", r"\bverif\w*\b", r"\bvalidat\w*\b"],
    "sub_logging": [r"\blogger\b", r"\blogging\b", r"\blog\b"],
    "sub_deployment": [r"\bdocker\b", r"\bcompose\b", r"\bdeploy\b", r"\bcontainer\b"],
    "sub_orchestration": [r"\bdispatch\b", r"\bschedule\b", r"\bqueue\b", r"\broute\b"],
    "sub_morphonic": [r"\bmorphon\b", r"\bfield\b", r"\bpotential\b", r"\bcoupling\b"],
    "sub_coding_theory": [r"\bgolay\b", r"\bhamming\b", r"\breed\b", r"\bparity\b", r"\becc\b"],
}

LITERAL_TERMS = [
    "matrix", "vector", "dimension", "angle", "lattice", "symmetry", "tensor",
    "field", "energy", "parity", "graph", "tree", "state", "orbit", "shell",
    "root", "weight", "node", "edge", "boundary", "manifold", "fiber", "bundle",
    "section", "curvature", "torsion", "connection", "gauge", "spinor", "braid",
]

SEMANTIC_DOMAINS = {
    "dom_algebra": [r"\bgroup\b", r"\bring\b", r"\bfield\b", r"\bmodule\b", r"\balgebra\b"],
    "dom_geometry": [r"\bgeometr\w*\b", r"\bangle\b", r"\bsurface\b", r"\bpolygon\b"],
    "dom_topology": [r"\btopolog\w*\b", r"\bhomotop\w*\b", r"\bfibration\b", r"\bbundle\b"],
    "dom_combinatorics": [r"\bcombinat\w*\b", r"\bpermutation\b", r"\bcombination\b", r"\bgraph\b"],
    "dom_probability": [r"\bprobabil\w*\b", r"\bstochastic\b", r"\brandom\b", r"\bsample\b"],
    "dom_optimization": [r"\boptimiz\w*\b", r"\bminimiz\w*\b", r"\bmaximiz\w*\b", r"\bgradient\b"],
    "dom_cryptography": [r"\bcrypt\w*\b", r"\bcipher\b", r"\bencrypt\b", r"\bdecrypt\b"],
    "dom_machine_learning": [r"\bml\b", r"\bneural\b", r"\btrain\b", r"\bmodel\b", r"\bepoch\b"],
    "dom_linguistics": [r"\blinguist\w*\b", r"\bparser?\b", r"\bgrammar\b", r"\bsyntax\b"],
    "dom_physics": [r"\bphysic\w*\b", r"\benergy\b", r"\bmomentum\b", r"\bforce\b", r"\bfield\b"],
    "dom_number_theory": [r"\bprime\b", r"\bmodular\b", r"\bdiophantine\b", r"\bresidue\b"],
    "dom_category_theory": [r"\bfunctor\b", r"\bcategory\b", r"\bnatural\s+transformation\b", r"\bmorphism\b"],
    "dom_information_theory": [r"\bentropy\b", r"\binformation\b", r"\bchannel\b", r"\bcoding\b"],
    "dom_graph_theory": [r"\bgraph\b", r"\bvertex\b", r"\bedge\b", r"\badjacen\w*\b", r"\bpath\b"],
    "dom_dynamical_systems": [r"\bdynamic\w*\b", r"\battractor\b", r"\bchaos\b", r"\borbit\b", r"\bbifurcat\w*\b"],
}

METAPHOR_VERBS = ["traverse", "explore", "build", "grow", "bridge", "repair", "protect",
                   "transform", "reflect", "balance", "flow", "spawn", "crystallize",
                   "navigate", "compose"]
INTENT_VERBS = ["compute", "return", "validate", "convert", "find", "store", "load",
                "create", "update", "map", "reduce", "verify", "measure", "classify", "optimize"]
FORMAL_TERMS = ["invariant", "idempotent", "commutative", "associative", "eigenvalue",
                "determinant", "kernel", "image", "dihedral", "weyl", "cartan", "coxeter",
                "representation", "automorphism", "functor", "category", "metric",
                "orthogonal", "manifold", "curvature", "geodesic", "isomorphism",
                "homomorphism", "fibration", "foliation"]
SCIENTIFIC_TERMS = ["hypothesis", "theorem", "model", "threshold", "stability", "resonance",
                    "simulation", "spectrum", "convergence", "complexity", "recursion",
                    "termination", "completeness"]
PROOF_TERMS = ["prove", "implies", "iff", "preserve", "satisfy", "guarantee"]

NOTATION_PATTERNS = {
    "notation_power": r"\*\*", "notation_sqrt": r"\bsqrt\b|math\.sqrt",
    "notation_trig": r"\bsin\b|\bcos\b|\btan\b", "notation_exp": r"\bexp\b|math\.exp",
    "notation_abs": r"\babs\b", "notation_minmax": r"\bmax\b|\bmin\b",
    "notation_sum": r"\bsum\b", "notation_transpose": r"\.T\b|transpose",
    "notation_eig": r"\beig\b|\beigenvalue\b", "notation_mod": r"\bmod\b|%",
    "notation_log": r"\blog\b|math\.log", "notation_pi": r"\bpi\b|math\.pi",
    "notation_phi": r"\bphi\b|golden", "notation_infinity": r"\binf\b|\binfinity\b|float\(['\"]inf",
    "notation_integral": r"\bintegral\b|\bintegrate\b",
    "notation_derivative": r"\bderivativ\w*\b|\bdiff\b|\bgradient\b",
}

SNAPOP_VERB_MAP = {
    "snap": "SNAPop_pi", "reflect": "SNAPop_sigma", "classify": "SNAPop_delta",
    "transform": "SNAPop_tau", "embed": "SNAPop_epsilon", "reduce": "SNAPop_rho",
    "measure": "SNAPop_mu", "normalize": "SNAPop_nu", "compose": "SNAPop_chi",
    "test": "SNAPop_theta", "cache": "SNAPop_kappa", "generate": "SNAPop_gamma",
    "detect": "SNAPop_detect", "construct": "SNAPop_construct", "verify": "SNAPop_verify",
    "infer": "SNAPop_infer", "extract": "SNAPop_extract", "persist": "SNAPop_persist",
    "evaluate": "SNAPop_evaluate", "scan": "SNAPop_scan", "analyze": "SNAPop_analyze",
    "repair": "SNAPop_repair", "resolve": "SNAPop_resolve",
}

_labeled_count = 0


class LabelerService:
    """14-pass SNAP semantic saturation labeler."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._labeled_count = 0

    def snap_label(self, content: str) -> List[str]:
        tracked: List[SNAPLabel] = []
        content_lower = content.lower()
        char_count = len(content)

        def _add(name: str, pass_num: int, value: Any = None, source: str = "",
                 confidence: float = 1.0, parents: List[str] = None):
            tracked.append(SNAPLabel(name=name, value=value, source=source or f"pass{pass_num}",
                                     pass_num=pass_num, confidence=confidence, parent_labels=parents or []))

        _add(f"SNAPchars_{min(char_count, 9999)}", 1, value=char_count, source="identity_size")
        size_tag = "small" if char_count < 200 else "medium" if char_count < 2000 else "large"
        _add(f"SNAPsize_{size_tag}", 1, source="identity_size")

        has_def = bool(re.search(r"\bdef\s+\w+", content))
        has_class = bool(re.search(r"\bclass\s+\w+", content))
        has_import = bool(re.search(r"\bimport\s+", content))
        if has_class: _add("SNAPtype_class", 1, source="identity_type")
        if has_def: _add("SNAPtype_function", 1, source="identity_type")
        if has_import: _add("SNAPtype_module", 1, source="identity_type")
        if not has_def and not has_class: _add("SNAPtype_fragment", 1, source="identity_type")

        for domain, keywords in DOMAIN_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in content_lower)
            if hits >= 2:
                _add(f"SNAPdomain_{domain}", 1, value=hits, source="identity_domain")
                _add(f"SNAPtouch_{domain}", 1, value=hits, source="identity_domain")
            elif hits >= 1:
                _add(f"SNAPkeyword_{domain}", 1, source="identity_domain")

        for fam, patterns in FAMILY_PATTERNS.items():
            if any(re.search(p, content_lower) for p in patterns):
                _add(f"SNAP{fam}", 1, source="identity_family")

        imports = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content)
        for imp in imports[:10]:
            _add(f"SNAPimport_{imp.split('.')[-1]}", 1, source="identity_import")

        if re.search(r"\bself\b", content):
            _add("SNAPis_method", 2, source="structural")
        for name, pattern in RETURN_TYPE_PATTERNS.items():
            if re.search(pattern, content):
                _add(f"SNAP{name}", 2, source="structural_return")
        for name, pattern in EFFECT_PATTERNS.items():
            if re.search(pattern, content):
                _add(f"SNAP{name}", 2, source="structural_effect")

        for name, pattern in INPUT_TYPE_PATTERNS.items():
            if re.search(pattern, content_lower):
                _add(f"SNAP{name}", 3, source="transform_input")
        for name, sigs in TRANSFORM_SIGNATURES.items():
            if any(re.search(s, content_lower) for s in sigs):
                _add(f"SNAP{name}", 3, source="transform_sig")

        touched_subsystems = []
        for sub, patterns in SUBSYSTEM_DETECTORS.items():
            if any(re.search(p, content_lower) for p in patterns):
                _add(f"SNAP{sub}", 4, source="system_touch")
                touched_subsystems.append(sub)
        n_sub = len(touched_subsystems)
        if n_sub == 0: _add("SNAProle_isolated", 4, source="system_role")
        elif n_sub == 1: _add("SNAProle_specialist", 4, source="system_role")
        elif n_sub <= 3: _add("SNAProle_bridge", 4, source="system_role")
        else: _add("SNAProle_integrator", 4, source="system_role")

        for term in LITERAL_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", content_lower):
                _add(f"SNAPliteral_{term}", 5, source="literal")

        for dom, patterns in SEMANTIC_DOMAINS.items():
            if any(re.search(p, content_lower) for p in patterns):
                _add(f"SNAP{dom}", 6, source="semantic_domain")

        for verb in METAPHOR_VERBS:
            if re.search(r"\b" + re.escape(verb) + r"\w*\b", content_lower):
                _add(f"SNAPmetaphor_{verb}", 7, source="metaphor")

        docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
        docstrings += re.findall(r"'''(.*?)'''", content, re.DOTALL)
        if docstrings:
            _add("SNAPhas_docstring", 8, source="intent_doc")
            doc_text = " ".join(docstrings).lower()
            for verb in INTENT_VERBS:
                if re.search(r"\b" + re.escape(verb) + r"\w*\b", doc_text):
                    _add(f"SNAPintent_{verb}", 8, source="intent_verb")
        for verb in INTENT_VERBS:
            if re.search(r"\b" + re.escape(verb) + r"\w*\b", content_lower):
                _add(f"SNAPaction_{verb}", 8, source="intent_action")

        for term in FORMAL_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\w*\b", content_lower):
                _add(f"SNAPformal_{term}", 9, source="formal")

        for term in SCIENTIFIC_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\w*\b", content_lower):
                _add(f"SNAPscience_{term}", 10, source="scientific")
        for term in PROOF_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\w*\b", content_lower):
                _add(f"SNAPproof_{term}", 10, source="scientific_proof")

        for name, pattern in NOTATION_PATTERNS.items():
            if re.search(pattern, content):
                _add(f"SNAP{name}", 11, source="notation")

        existing_names = {t.name for t in tracked}
        if "SNAPtype_function" in existing_names:
            _add("SNAPexpand_callable", 12, source="expansion", parents=["SNAPtype_function"])
            _add("SNAPexpand_atomic", 12, source="expansion", parents=["SNAPtype_function"])
        if "SNAPtype_class" in existing_names:
            _add("SNAPexpand_composite", 12, source="expansion", parents=["SNAPtype_class"])
            _add("SNAPexpand_instantiable", 12, source="expansion", parents=["SNAPtype_class"])
        geo_families = {"SNAPfamily_e8", "SNAPfamily_morphonic"}
        if existing_names & geo_families:
            _add("SNAPexpand_geometric", 12, source="expansion", parents=sorted(existing_names & geo_families))
        if "SNAPfamily_agent" in existing_names:
            _add("SNAPexpand_agent_domain", 12, source="expansion", parents=["SNAPfamily_agent"])
        if "SNAPdomain_database" in existing_names or "SNAPfamily_mdhg" in existing_names:
            _add("SNAPexpand_storage", 12, source="expansion",
                 parents=sorted(existing_names & {"SNAPdomain_database", "SNAPfamily_mdhg"}))

        dr_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()
        dr_sum = sum(int(c, 16) for c in dr_hash)
        while dr_sum >= 10:
            dr_sum = sum(int(d) for d in str(dr_sum))
        dr_val = dr_sum or 9
        _add(f"SNAPdr_{dr_val}", 12, value=dr_val, source="expansion_dr")
        if dr_val in (3, 6, 9):
            _add("SNAPdr_channel_creative", 12, source="expansion_dr", parents=[f"SNAPdr_{dr_val}"])
        elif dr_val in (1, 4, 7):
            _add("SNAPdr_channel_structural", 12, source="expansion_dr", parents=[f"SNAPdr_{dr_val}"])
        else:
            _add("SNAPdr_channel_connective", 12, source="expansion_dr", parents=[f"SNAPdr_{dr_val}"])

        domain_labels = [t.name for t in tracked if t.name.startswith("SNAPdomain_") or
                         t.name.startswith("SNAPdom_") or t.name.startswith("SNAPfamily_")]
        structural_labels = [t.name for t in tracked if t.name.startswith("SNAPtype_") or
                             t.name.startswith("SNAProle_") or t.name.startswith("SNAPexpand_")]
        composites_added = 0
        for d_label in domain_labels:
            if composites_added >= 20: break
            d_short = d_label.replace("SNAP", "").replace("domain_", "").replace("dom_", "").replace("family_", "")
            for s_label in structural_labels:
                if composites_added >= 20: break
                s_short = s_label.replace("SNAP", "").replace("type_", "").replace("role_", "").replace("expand_", "")
                _add(f"SNAPcomposite_{d_short}_{s_short}", 13, source="composite",
                     confidence=0.8, parents=[d_label, s_label])
                composites_added += 1

        for verb, snapop in SNAPOP_VERB_MAP.items():
            if re.search(r"\b" + re.escape(verb) + r"\w*\b", content_lower):
                _add(snapop, 14, source="inferential_crt", parents=[f"verb:{verb}"])

        seen: set = set()
        result: List[str] = []
        for t in tracked:
            if t.name not in seen:
                seen.add(t.name)
                result.append(t.name)
        return result

    def snap_label_full(self, content: str) -> Dict[str, Any]:
        labels = self.snap_label(content)
        pass_counts = {}
        for lbl in labels:
            p = 1
            if "effect_" in lbl or "return_" in lbl or "is_method" in lbl: p = 2
            elif "input_" in lbl or "xform_" in lbl: p = 3
            elif "sub_" in lbl or "role_" in lbl: p = 4
            elif "literal_" in lbl: p = 5
            elif "dom_" in lbl: p = 6
            elif "metaphor_" in lbl: p = 7
            elif "intent_" in lbl or "action_" in lbl or "docstring" in lbl: p = 8
            elif "formal_" in lbl: p = 9
            elif "science_" in lbl or "proof_" in lbl: p = 10
            elif "notation_" in lbl: p = 11
            elif "expand_" in lbl or "dr_" in lbl: p = 12
            elif "composite_" in lbl: p = 13
            elif lbl.startswith("SNAPop_"): p = 14
            pass_counts[p] = pass_counts.get(p, 0) + 1
        return {"labels": labels, "count": len(labels), "mass": len(labels), "pass_counts": pass_counts}

    def label(self, content: str) -> Dict[str, Any]:
        if not content or len(content.strip()) < 5:
            return {"labels": [], "count": 0, "mass": 0}
        labels = self.snap_label(content)
        self._labeled_count += 1
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"lbl-{hashlib.sha256(content[:100].encode()).hexdigest()[:8]}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"label_count": len(labels), "content_len": len(content)},
                boundary_type="labeler_label",
            ))
        return {"labels": labels, "count": len(labels), "mass": len(labels)}

    def label_full(self, content: str) -> Dict[str, Any]:
        if not content or len(content.strip()) < 5:
            return {"labels": [], "count": 0, "mass": 0, "pass_counts": {}}
        result = self.snap_label_full(content)
        self._labeled_count += 1
        return result

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "service": "opencmplx-labeler", "passes": 14, "labeled": self._labeled_count}
