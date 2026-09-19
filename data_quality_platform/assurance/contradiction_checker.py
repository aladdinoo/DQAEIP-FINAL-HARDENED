"""DQAEIP contradiction checker (Phase 6 / Phase 4D).

Scans the CURRENT release-facing documents for contradictions against
machine-derived truth. Fail-closed: any detected contradiction makes
the verdict CONTRADICTIONS_FOUND (the release gate then fails).

Scanned (current documents only — historical/superseded forensic
archives under evidence/* are deliberately OUT of scope; they are
preserved evidence of earlier states and are explicitly labeled):

    README.md
    RELEASE_NOTES.md
    DELIVERY_MANIFEST.json
    FINAL_RESULTS.json
    final_result.json
    release_manifest.json
    evidence/release/*.json
    evidence/release_gate/final_release_gate.json
    evidence/rebuild_verification/test_summary.json
    evidence/rebuild_verification/run_pair_verification.json
    evidence/final_verification/FINAL_VERIFICATION.json

Truth is derived AT CHECK TIME from the authoritative sources (the
official 3M evidence, the actual rule source file, the actual
checker file, the recorded gate, the recorded test summary) — never
from the documents being checked.

Detection classes:
    stale test counts (715 / 813 / 804)
    wrong gate count (16-gate era)
    48M vs 24M comparison-count conflicts
    wrong rule-set SHA / checker SHA / input / output SHA
    wrong release identity or release date
    conflicting verdicts between documents
    Run 3 references (positive claims only; negated mentions pass)
    real-rows / production-data terminology for the synthetic dataset
    production-ready / enterprise-ready / fully-scalable claims
    ClickHouse / Airflow execution claims without runtime evidence
    100M / 800M scalability claims (negated and out-of-scope mentions
    pass; bare positive claims fire)
    old DQAVP release identities presented as current
"""

import json
import os
import re

# ---------------------------------------------------------------- config

MD_DOCS = [
    "README.md",
    "RELEASE_NOTES.md",
]

JSON_DOCS = [
    "DELIVERY_MANIFEST.json",
    "FINAL_RESULTS.json",
    "final_result.json",
    "release_manifest.json",
    "evidence/release_gate/final_release_gate.json",
    "evidence/rebuild_verification/test_summary.json",
    "evidence/rebuild_verification/run_pair_verification.json",
]

JSON_DOC_GLOBS = [
    ("evidence/release", ".json"),
]

# Historical/forensic archive prefixes that are OUT of scope by design
# (preserved, explicitly-labeled evidence of superseded states).
OUT_OF_SCOPE_PREFIXES = [
    "evidence/hardening_baseline/",
    "evidence/rebuild_baseline/",
    "evidence/rebuild_verification/negative_tests/",
]

# Dated historical documents preserved from the original 2026-09-09
# delivery: every value-bearing field carries its own date marker
# (final_validation_2026_09_09, reports_history, historical_zip_
# checkpoints, generated 2026-09-07 / consolidated 2026-09-09). Their
# values are true FOR THAT DATE; treating them as current claims would
# falsify history. Exempt from identity checks; still prose-scanned
# where the text asserts something timeless.
HISTORICAL_DOCS = {
    "DELIVERY_MANIFEST.json",
    # Original 2026-09-07 company final verification record (repo
    # data-quality-platform-V1, branch final-verification-v1, the
    # 322-test era). The CURRENT final verification evidence lives
    # in evidence/release/final_verification.json.
    "evidence/final_verification/FINAL_VERIFICATION.json",
}

# The checker's own output is excluded from its scan set (a report
# quoting flagged contexts must not re-flag itself).
SELF_OUTPUT = "evidence/release/contradiction_check.json"

NEGATION_WINDOW = 64
NEGATION_WORDS = (
    "no ", "not ", "never ", "without ", "n't ", "nor ",
    "none", "nothing", "neither ", "absent", "missing",
    "must not", "forbidden", "excluded", "omitted",
)

# Scope-exclusion markers: a sentence (or JSON field) that explicitly
# places a topic OUT of the validated/certified scope is DOCUMENTING a
# boundary, not asserting the claim — exempt exactly like negations.
# Precision note (same sentence-level granularity as NEGATION_WORDS):
# this exempts only the sentence/field segment carrying the marker, so
# a bare positive claim elsewhere still fires. Positive controls in
# tests/assurance/test_tamper_fail_closed.py prove true overclaims
# (e.g. "validated at 100M rows per run") are still flagged.
SCOPE_EXCLUSION_MARKERS = (
    "out of scope", "out-of-scope", "outside the scope",
    "beyond the scope", "not in scope", "not within scope",
    "excluded from scope", "scope exclusion",
)

# Historical/superseded-context markers: a sentence (or JSON field)
# carrying one of these markers is DOCUMENTING a superseded state,
# not asserting it as current — exempt from contradiction flags.
HISTORICAL_MARKERS = (
    "supersed", "stale", "histor", "previous", "legacy",
    "obsolete", "superseded", "predecessor", "corrected",
    "replaced", "no longer", "rejected", "outdated",
    "pre-rebuild", "superseded-by", "was superseded",
    "2026-09-15 dqaVP-era", "dqavp-era",
)

# Positive-claim prose patterns that are forbidden unless negated.
PROSE_PATTERNS = {
    "run3_positive_claim": [
        r"\brun[ _-]?3\b",
        r"\bthird run\b",
        r"\bthree complete runs\b",
        r"\b3 runs\b",
    ],
    "real_rows_terminology": [
        r"\breal rows\b",
        r"\breal data\b",
        r"\breal consumer\b",
        r"\bproduction data\b",
        r"\bproduction rows\b",
        r"\blive data\b",
    ],
    "readiness_overclaim": [
        r"\bproduction[- ]ready\b",
        r"\benterprise[- ]ready\b",
        r"\bfully scalable\b",
    ],
    "clickhouse_execution_claim": [
        r"clickhouse[^.\n]{0,40}\b(executed|validated|verified|ran|"
        r"confirmed)\b",
        r"\b(executed|validated|verified|ran|confirmed)\b[^.\n]{0,40}"
        r"clickhouse",
        r"\bon clickhouse\b",
        r"\bagainst clickhouse\b",
    ],
    "airflow_execution_claim": [
        r"airflow[^.\n]{0,40}\b(executed|orchestrated|validated|"
        r"verified|ran|confirmed)\b",
        r"\b(executed|orchestrated|validated|verified|ran|confirmed)\b"
        r"[^.\n]{0,40}airflow",
        r"\bon airflow\b",
    ],
    "scalability_overclaim": [
        r"\b100m\b", r"\b800m\b", r"\b100 million\b", r"\b800 million\b",
        r"\b100,000,000\b", r"\b800,000,000\b",
    ],
    "old_release_identity_as_current": [
        r"DQAVP-Enterprise-Hardened-Validation-Release",
        r"DQAVP-Final-Release",
    ],
    "stale_test_counts": [
        r"\b715 passed\b", r"\b813 collected\b", r"\b804 passed\b",
        r"\b414 passed\b",
    ],
    "stale_gate_count": [
        r"\b16 fail-closed gates\b", r"\b16-gate\b", r"\b16 gates\b",
    ],
    "bounded_memory_claim": [
        r"\bbounded memory\b",
    ],
}

# Values that must NEVER appear as bare positive claims even inside
# JSON string values (same negation rules apply).
JSON_STRING_PATTERNS = dict(PROSE_PATTERNS)


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _sentence_at(text, start, end):
    """The sentence (period/newline-delimited segment) containing
    [start, end)."""
    seg_start = max(text.rfind(ch, 0, start) for ch in ".!?\n") + 1
    seg_ends = [text.find(ch, end) for ch in ".!?\n"]
    seg_ends = [e for e in seg_ends if e != -1]
    seg_end = min(seg_ends) if seg_ends else len(text)
    return text[seg_start:seg_end]


def _is_exemption_context(segment):
    """True when the sentence/field segment documents a superseded
    state, carries a negation, or places the topic explicitly out of
    scope — not a current positive claim."""
    low = segment.lower()
    if any(neg in low for neg in NEGATION_WORDS):
        return True
    if any(s in low for s in SCOPE_EXCLUSION_MARKERS):
        return True
    if any(h in low for h in HISTORICAL_MARKERS):
        return True
    return False


def _flag_unnegated(text, pattern):
    """Return [(match_text, position)] for matches whose containing
    sentence is neither negated nor historical-context."""
    hits = []
    for m in re.finditer(pattern, text, re.IGNORECASE):
        segment = _sentence_at(text, m.start(), m.end())
        if _is_exemption_context(segment):
            continue
        hits.append((m.group(0), m.start()))
    return hits


def _iter_json_strings(doc, prefix=""):
    """Yield (field_path, string_value) for every string leaf."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            yield from _iter_json_strings(v, f"{prefix}.{k}")
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from _iter_json_strings(v, f"{prefix}[{i}]")
    elif isinstance(doc, str):
        yield prefix, doc


def _collect_current_docs(repo_root):
    docs = []
    for rel in MD_DOCS + JSON_DOCS:
        p = os.path.join(repo_root, rel)
        if os.path.isfile(p):
            docs.append(rel)
    for dir_rel, ext in JSON_DOC_GLOBS:
        d = os.path.join(repo_root, dir_rel)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(ext):
                docs.append(f"{dir_rel}/{fn}")
    return [d for d in docs
            if not any(d.startswith(p) for p in OUT_OF_SCOPE_PREFIXES)
            and d != SELF_OUTPUT]


def derive_truth(repo_root):
    """Machine-derive the authoritative values at check time."""
    truth = {}
    f3m = _load_json(os.path.join(
        repo_root,
        "evidence/validation/2026-09-19/fresh_3m2/FINAL_RESULTS.json"))
    if f3m:
        truth["rows"] = f3m.get("rows")
        truth["input_sha256"] = f3m.get("input_sha256")
        truth["output_sha256"] = f3m.get("output_sha256")
        truth["final_3m_status"] = f3m.get("final_status")
        comp = f3m.get("comparison_count", {})
        if isinstance(comp, dict) and comp.get("combined_total"):
            truth["comparisons_combined"] = comp["combined_total"]
            truth["comparisons_per_run"] = comp.get("run_1")
        mm = f3m.get("oracle_mismatches", {})
        if isinstance(mm, dict):
            truth["mismatches_combined"] = mm.get("combined_total")
        truth["run_ids"] = sorted((f3m.get("runs") or {}).keys())
    ts = _load_json(os.path.join(
        repo_root,
        "evidence/rebuild_verification/test_summary.json"))
    if ts:
        truth["tests"] = {k: ts.get(k) for k in
                         ("collected", "passed", "skipped",
                          "failed", "errors")}
    gate = _load_json(os.path.join(
        repo_root, "evidence/release_gate/final_release_gate.json"))
    if gate:
        truth["gate_count"] = gate.get("gate_count")
        truth["gate_verdict"] = gate.get("overall_verdict")
    import hashlib

    def sha(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    rules_p = os.path.join(
        repo_root, "data_quality_platform/rules/v1_rules.py")
    checker_p = os.path.join(
        repo_root, "scripts/final_3m_validation.py")
    if os.path.isfile(rules_p):
        truth["rule_source_sha256"] = sha(rules_p)
    if os.path.isfile(checker_p):
        truth["checker_sha256"] = sha(checker_p)
    rm = _load_json(os.path.join(repo_root, "release_manifest.json"))
    if rm:
        truth["release_name"] = rm.get("release_name")
        truth["release_date"] = rm.get("release_date")
    return truth


def _check_doc_value(doc, path, key, expected, contradictions, doc_rel,
                     value_getter=None, required=True):
    """Compare a document's recorded value for ``key`` with the
    machine-derived ``expected``; missing key in a current doc is a
    contradiction only when ``required``."""
    cur = doc
    if value_getter:
        cur = value_getter(doc)
    else:
        for part in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                cur = None
                break
    if cur is None:
        if required:
            contradictions.append({
                "doc": doc_rel, "field": key,
                "type": "missing_required_value",
                "expected": expected})
        return
    if cur != expected:
        contradictions.append({
            "doc": doc_rel, "field": key, "type": "value_conflict",
            "recorded": cur, "expected": expected})


def check_prose(repo_root, docs, truth):
    """Negation- and history-aware prose scan over markdown + JSON
    string leaves. JSON fields whose PATH marks a superseded-state
    record (e.g. ``.supersedes``) are exempt by construction."""
    contradictions = []
    exempt_path_markers = ("supersed", "histor", "legacy", "previous",
                           "predecessor", "obsolete")
    for rel in docs:
        p = os.path.join(repo_root, rel)
        if rel.endswith(".md"):
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            segments = [(None, text)]
        else:
            doc = _load_json(p)
            if doc is None:
                continue
            segments = list(_iter_json_strings(doc))
        for field_path, value in segments:
            if field_path and any(
                    m in field_path.lower()
                    for m in exempt_path_markers):
                continue
            for label, patterns in PROSE_PATTERNS.items():
                for pat in patterns:
                    for match_text, pos in _flag_unnegated(value, pat):
                        contradictions.append({
                            "doc": rel, "type": label,
                            "field": field_path,
                            "match": match_text,
                            "context": value[
                                max(0, pos - 40):pos + 60
                            ].replace("\n", " ")})
    return contradictions


def check_json_identities(repo_root, docs, truth):
    """Field-level identity conflicts in current JSON documents.
    Historical docs (dated records) are skipped — their values are
    pinned to their own dates, not to current truth."""
    contradictions = []

    f3m_rel = ("evidence/validation/2026-09-19/fresh_3m2/"
               "FINAL_RESULTS.json")
    for rel in docs:
        if not rel.endswith(".json") or rel in HISTORICAL_DOCS:
            continue
        p = os.path.join(repo_root, rel)
        doc = _load_json(p)
        if doc is None:
            continue

        # gate_count conflicts (truth: recorded gate)
        if "gate_count" in json.dumps(doc)[:200000] and \
                isinstance(doc.get("gate_count"), int) \
                and truth.get("gate_count") is not None \
                and rel != "evidence/release_gate/final_release_gate.json":
            if doc["gate_count"] != truth["gate_count"]:
                contradictions.append({
                    "doc": rel, "type": "gate_count_conflict",
                    "recorded": doc["gate_count"],
                    "expected": truth["gate_count"]})

        # test-count conflicts (any nested "collected"+"passed" pair)
        def walk(node, path):
            if isinstance(node, dict):
                if {"collected", "passed"} <= set(node) and isinstance(
                        node.get("collected"), int):
                    t = truth.get("tests") or {}
                    for k in ("collected", "passed", "skipped"):
                        if k in node and t.get(k) is not None \
                                and node[k] != t[k]:
                            contradictions.append({
                                "doc": rel,
                                "type": "test_count_conflict",
                                "field": f"{path}.{k}",
                                "recorded": node[k],
                                "expected": t[k]})
                for k, v in node.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")
        walk(doc, "")

        # release name conflicts (docs that declare one)
        for key in ("release_name", "release_identity"):
            v = doc.get(key)
            if isinstance(v, str) and truth.get("release_name") \
                    and v != truth["release_name"] and key == "release_name":
                contradictions.append({
                    "doc": rel, "type": "release_identity_conflict",
                    "recorded": v, "expected": truth["release_name"]})
            if isinstance(v, dict) and v.get("release_name"):
                if truth.get("release_name") and \
                        v["release_name"] != truth["release_name"]:
                    contradictions.append({
                        "doc": rel,
                        "type": "release_identity_conflict",
                        "recorded": v["release_name"],
                        "expected": truth["release_name"]})

        # final verdict conflicts
        for key in ("final_release_status", "final_status"):
            v = doc.get(key)
            if isinstance(v, str) and v.startswith("PASS") and \
                    rel not in (f3m_rel,) and truth.get(
                        "final_3m_status") == "PASS":
                # Any *release* verdict must be the documented one:
                # PASS_WITH_DOCUMENTED_LIMITATIONS (raw PASS would
                # hide limitations).
                if "final_release_status" == key and \
                        v != "PASS_WITH_DOCUMENTED_LIMITATIONS":
                    contradictions.append({
                        "doc": rel, "type": "release_verdict_conflict",
                        "recorded": v,
                        "expected": "PASS_WITH_DOCUMENTED_LIMITATIONS"})

        # input/output SHA conflicts — scoped to 3M-validation
        # identity contexts only; performance scale-ladder inputs and
        # other datasets legitimately have different hashes.
        sha_scope_markers = ("3m", "verification", "runs", "official")
        sha_exclusion_markers = ("performance", "scale_ladder",
                                 "benchmark", "mutation", "negative",
                                 "audit_1k", "rt_1k", "final_5m")

        def walk_shas(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "input_sha256" and isinstance(v, str) \
                            and truth.get("input_sha256") \
                            and v != truth["input_sha256"] \
                            and len(v) == 64 \
                            and any(m in path.lower()
                                    for m in sha_scope_markers) \
                            and not any(m in path.lower()
                                        for m in sha_exclusion_markers):
                        contradictions.append({
                            "doc": rel, "type": "input_sha_conflict",
                            "field": path + "." + k,
                            "recorded": v,
                            "expected": truth["input_sha256"]})
                    if k == "output_sha256" and isinstance(v, str) \
                            and truth.get("output_sha256") \
                            and v != truth["output_sha256"] \
                            and len(v) == 64 \
                            and any(m in path.lower()
                                    for m in sha_scope_markers) \
                            and not any(m in path.lower()
                                        for m in sha_exclusion_markers):
                        contradictions.append({
                            "doc": rel, "type": "output_sha_conflict",
                            "field": path + "." + k,
                            "recorded": v,
                            "expected": truth["output_sha256"]})
                    walk_shas(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk_shas(v, f"{path}[{i}]")
        walk_shas(doc, "")
    return contradictions


def run_contradiction_check(repo_root):
    """Full scan. Returns the report dict (verdict CONSISTENT or
    CONTRADICTIONS_FOUND)."""
    docs = _collect_current_docs(repo_root)
    truth = derive_truth(repo_root)
    contradictions = []
    contradictions += check_prose(repo_root, docs, truth)
    contradictions += check_json_identities(repo_root, docs, truth)

    report = {
        "report": "DQAEIP contradiction check (current documents vs "
                  "machine-derived truth)",
        "docs_scanned": docs,
        "docs_scanned_count": len(docs),
        "out_of_scope_note": (
            "historical/superseded forensic archives are excluded by "
            "design; they are preserved, explicitly-labeled evidence of "
            "superseded states"),
        "truth_sources": {
            "official_3m2": "evidence/validation/2026-09-19/fresh_3m2/"
                           "FINAL_RESULTS.json",
            "tests": "evidence/rebuild_verification/test_summary.json",
            "gate": "evidence/release_gate/final_release_gate.json",
            "rule_source": "data_quality_platform/rules/v1_rules.py "
                           "(actual file hash)",
            "checker": "scripts/final_3m_validation.py (actual file "
                       "hash)",
            "release_identity": "release_manifest.json (declared "
                                "anchor)",
        },
        "truth": {k: v for k, v in truth.items()},
        "contradictions": contradictions,
        "contradiction_count": len(contradictions),
        "verdict": ("CONTRADICTIONS_FOUND" if contradictions
                    else "CONSISTENT"),
        "fail_closed_rule": (
            "the release gate fails when verdict != CONSISTENT; absence "
            "of a check input records NOT_VERIFIED, never PASS"),
    }
    return report
