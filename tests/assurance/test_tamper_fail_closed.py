"""Fail-closed tamper tests for the DQAEIP zero-assumption rebuild
assurance layer (Phase 4G).

Every scenario mutates a SYNTHETIC evidence tree (tmp_path — never the
protected official evidence) and asserts the mutated state can NEVER
produce PASS / VERIFIED. The ten required scenarios:

    1. modified evidence          -> TAMPERED (hash mismatch)
    2. wrong SHA                   -> claim verification fails
    3. wrong rule hash            -> claim verification fails
    4. missing run                -> derivation NOT_VERIFIED (None)
    5. stale checker               -> STALE classification
    6. fake PASS                  -> unsupported value never verifies
    7. wrong row count            -> claim verification fails
    8. wrong schema               -> TAMPERED via run-manifest hash
    9. modified output            -> TAMPERED via output hash
   10. modified manifest          -> artifact-manifest verify fails

Additional invariants:
    - claim ids are stable and timestamp-free
    - untrusted classes can never yield a PASS-able screening verdict
    - the reproducibility fingerprint is deterministic
"""

import hashlib
import json
import os
import shutil
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from data_quality_platform.assurance.claims import (
    DERIVATIONS, make_claim, not_verified_claim, verify_claims,
    _stable_claim_id,
)
from data_quality_platform.assurance.evidence_quarantine import (
    EvidenceQuarantine, REJECTED_CLASSES,
)

# ----------------------------------------------------------------------
# Synthetic evidence tree helpers (never touch protected evidence)
# ----------------------------------------------------------------------

F3M_REL = ("evidence/validation/2026-09-19/fresh_3m2/"
           "FINAL_RESULTS.json")
RULES_REL = "data_quality_platform/rules/v1_rules.py"
RP_REL = "evidence/rebuild_verification/run_pair_verification.json"
TS_REL = "evidence/rebuild_verification/test_summary.json"
LIM_REL = "evidence/release/limitation_registry.json"
V1INV_REL = "evidence/rebuild_baseline/v1_rule_inventory.json"

CHECKER_SHA = "0ef7c10c14a1df317c23cb0dfc73b3a60c2257c064b35080d694e5fe8bc50d84"
INPUT_SHA = "59624a53c72f908f1dde673ceecf59e0662ae721bb8f9af7e165acba5318d153"
OUTPUT_SHA = "b72adc235160a86e0b99a08f988dd0bb5f2cff82bbe5b5d28ea07c5a5719329a"
V1_SHA = "daef1ded54c7d3c79898a1ba253be2acd5b6120e18b16b09009fdd7be9fc2276"


def _write(root, rel, doc):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    return path


def _write_text(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def build_good_tree(tmp_path):
    """A minimal but internally consistent synthetic evidence tree."""
    root = str(tmp_path)
    _write_text(root, RULES_REL, "# synthetic frozen v1 rules source\n")
    _write(root, F3M_REL, {
        "rows": 3200000,
        "input_sha256": INPUT_SHA,
        "output_sha256": OUTPUT_SHA,
        "final_status": "PASS",
        "seed": 20260918,
        "determinism_status":
            "PASS (byte-identical across two complete runs)",
        "oracle_comparisons": 51200000,
        "comparison_count": {
            "run_1": 25600000, "run_2": 25600000,
            "combined_total": 51200000,
        },
        "oracle_mismatches": {
            "run_1": 0, "run_2": 0, "combined_total": 0,
        },
        "runs": {
            "run_1": {
                "dataset": {"input_sha256": INPUT_SHA},
                "output": {"sha256": OUTPUT_SHA},
                "oracle": {
                    "comparisons": 25600000,
                    "mismatches": 0,
                    "mismatches_by_rule": {},
                },
            },
            "run_2": {
                "dataset": {"input_sha256": INPUT_SHA},
                "output": {"sha256": OUTPUT_SHA},
                "oracle": {
                    "comparisons": 25600000,
                    "mismatches": 0,
                    "mismatches_by_rule": {},
                },
            },
        },
    })
    _write(root, RP_REL, {"verdict": "PASS", "checks_total": 95,
                         "checks_failed": 0})
    _write(root, TS_REL, {
        "collected": 100, "passed": 95, "skipped": 5,
        "failed": 0, "errors": 0, "all_green": True,
    })
    _write(root, LIM_REL, {"limitations": [
        {"id": "LIM-001", "title": "O(N) memory profile",
         "description": "memory grows with row count"},
        {"id": "LIM-002", "title": "ClickHouse runtime not executed"},
        {"id": "LIM-003", "title": "Airflow runtime not executed"},
    ]})
    _write(root, V1INV_REL, {
        "rules": [{"rule_id": f"rule_{i}"} for i in range(8)],
    })
    return root


def good_claims(root):
    """Claims whose values match the good synthetic tree."""
    return [
        make_claim("3.2M validation rows", 3200000, F3M_REL,
                   "final_3m_rows", root, True),
        make_claim("3M input SHA-256", INPUT_SHA, F3M_REL,
                   "final_3m_input_sha256", root, True),
        make_claim("exactly two complete 3M runs", 2, F3M_REL,
                   "final_3m_run_count", root, True),
        make_claim("byte-identical outputs across runs", True, F3M_REL,
                   "final_3m_determinism_gate", root, True),
        make_claim("Frozen V1 rule count", 8, V1INV_REL,
                   "v1_rule_count", root, True),
    ]


# ----------------------------------------------------------------------
# 1/2/3/7: modified evidence, wrong SHA, wrong rule hash, wrong rows
# ----------------------------------------------------------------------

class TestClaimVerificationFailClosed:

    def test_good_claims_verify(self, tmp_path):
        root = build_good_tree(tmp_path)
        report = verify_claims(good_claims(root), root)
        assert report["recheck_passed"] is True
        assert all(r["ok"] for r in report["results"])

    def _assert_claim_fails(self, tmp_path, claim_index, mutate):
        root = build_good_tree(tmp_path)
        mutate(root)
        claims = good_claims(root)
        report = verify_claims(claims, root)
        assert report["recheck_passed"] is False
        return report, claims

    def test_modified_evidence_rejects_row_claim(self, tmp_path):
        def mutate(root):
            doc = json.load(open(os.path.join(root, F3M_REL)))
            doc["rows"] = 3199999
            _write(root, F3M_REL, doc)
        report, _ = self._assert_claim_fails(tmp_path, 0, mutate)
        assert any(r["claim"] == "3.2M validation rows" and not r["ok"]
                   for r in report["results"])

    def test_wrong_sha_fails_verification(self, tmp_path):
        def mutate(root):
            doc = json.load(open(os.path.join(root, F3M_REL)))
            doc["input_sha256"] = "f" * 64
            _write(root, F3M_REL, doc)
        report, _ = self._assert_claim_fails(tmp_path, 1, mutate)
        assert any("input SHA" in r["claim"] and not r["ok"]
                   for r in report["results"])

    def test_wrong_rule_hash_fails_verification(self, tmp_path):
        root = build_good_tree(tmp_path)
        claims = [make_claim("V1 rule source SHA-256", V1_SHA,
                             RULES_REL, "v1_rule_source_sha256",
                             root, True)]
        # Tamper the rule source after the claim recorded its hash.
        _write_text(root, RULES_REL,
                    "# tampered rule source — unauthorized change\n")
        report = verify_claims(claims, root)
        assert report["recheck_passed"] is False

    def test_missing_run_count_not_verified(self, tmp_path):
        root = build_good_tree(tmp_path)
        doc = json.load(open(os.path.join(root, F3M_REL)))
        del doc["runs"]["run_2"]
        _write(root, F3M_REL, doc)
        claims = [make_claim("exactly two complete 3M runs", 2,
                             F3M_REL, "final_3m_run_count", root, True)]
        report = verify_claims(claims, root)
        assert report["recheck_passed"] is False

    def test_missing_evidence_file_not_verified(self, tmp_path):
        root = build_good_tree(tmp_path)
        os.remove(os.path.join(root, F3M_REL))
        claims = good_claims(root)
        report = verify_claims(claims, root)
        # Missing source => every claim anchored to that source is
        # recorded NOT_VERIFIED (the V1-inventory claim keeps its own,
        # still-present source — dimensions are independent).
        f3m_claims = [c for c in claims if c["source_artifact"] == F3M_REL]
        assert len(f3m_claims) == 4
        assert all(c["status"] == "NOT_VERIFIED" and not c["verified"]
                   for c in f3m_claims)
        # NOT_VERIFIED claims never become PASS.
        for res, c in zip(report["results"], claims):
            if c["source_artifact"] == F3M_REL:
                assert res["verified"] is False

    def test_fake_pass_value_never_verifies(self, tmp_path):
        """A claim that asserts PASS for something the evidence does
        not support must fail verification — never PASS."""
        root = build_good_tree(tmp_path)
        doc = json.load(open(os.path.join(root, F3M_REL)))
        doc["final_status"] = "FAIL"
        doc["oracle_mismatches"] = {
            "run_1": 3, "run_2": 0, "combined_total": 3}
        _write(root, F3M_REL, doc)
        claims = [
            make_claim("oracle mismatches (combined)", 0, F3M_REL,
                       "oracle_mismatches_combined", root, True),
        ]
        report = verify_claims(claims, root)
        assert report["recheck_passed"] is False
        assert any("mismatches" in r["claim"] and not r["ok"]
                   for r in report["results"])

    def test_not_verified_claim_can_never_become_pass(self):
        c = not_verified_claim("release gate verdict", "pending")
        assert c["status"] == "NOT_VERIFIED"
        assert c["verified"] is False
        assert c["value"] is None

    def test_claim_ids_stable_and_deterministic(self):
        a = _stable_claim_id("3M validation rows")
        b = _stable_claim_id("3M validation rows")
        c = _stable_claim_id("different claim")
        assert a == b and a != c
        assert "CLAIM-" in a

    def test_make_claim_missing_source_is_not_verified(self, tmp_path):
        root = build_good_tree(tmp_path)
        os.remove(os.path.join(root, F3M_REL))
        claim = make_claim("3.2M validation rows", 3200000, F3M_REL,
                           "final_3m_rows", root, True)
        assert claim["status"] == "NOT_VERIFIED"
        assert claim["verified"] is False


# ----------------------------------------------------------------------
# 5/8/9/10 + 1: quarantine classification scenarios
# ----------------------------------------------------------------------

class TestEvidenceQuarantineFailClosed:

    def _quarantine(self, root, expected_overrides=None,
                    current_identities=None):
        f3m_path = os.path.join(root, F3M_REL)
        expected = {
            F3M_REL: hashlib.sha256(
                open(f3m_path, "rb").read()).hexdigest(),
            RP_REL: hashlib.sha256(
                open(os.path.join(root, RP_REL), "rb").read()).hexdigest(),
        }
        expected.update(expected_overrides or {})
        return EvidenceQuarantine(
            expected, trusted_set=[F3M_REL],
            current_identities=current_identities or {})

    def test_good_tree_screens_clean(self, tmp_path):
        root = build_good_tree(tmp_path)
        report = self._quarantine(root).screen(root)
        assert report["verdict"] == "CLEAN"
        assert report["classification_counts"]["TRUSTED"] == 1
        assert report["classification_counts"]["VERIFIED"] == 1

    def test_modified_evidence_is_tampered(self, tmp_path):
        root = build_good_tree(tmp_path)
        q = self._quarantine(root)
        doc = json.load(open(os.path.join(root, F3M_REL)))
        doc["rows"] = 100  # scenario 7 at the screening layer too
        _write(root, F3M_REL, doc)
        rec = q.classify(root, F3M_REL)
        assert rec["classification"] == "TAMPERED"

    def test_modified_output_is_tampered(self, tmp_path):
        """Scenario 9: output hash field changed -> the pinned hash no
        longer matches -> TAMPERED (never PASS)."""
        root = build_good_tree(tmp_path)
        q = self._quarantine(root)
        doc = json.load(open(os.path.join(root, F3M_REL)))
        doc["output_sha256"] = "a" * 64
        _write(root, F3M_REL, doc)
        rec = q.classify(root, F3M_REL)
        assert rec["classification"] == "TAMPERED"

    def test_wrong_schema_is_tampered_via_manifest(self, tmp_path):
        """Scenario 8: a run manifest's schema hash is altered -> the
        manifest file hash no longer matches its pin -> TAMPERED."""
        root = build_good_tree(tmp_path)
        mrel = ("evidence/validation/2026-09-19/fresh_3m2/"
                "pass1_engine/manifest.json")
        _write(root, mrel, {"schema_hash": "4" * 64, "run_id": "run_1"})
        expected = {
            mrel: hashlib.sha256(
                open(os.path.join(root, mrel), "rb").read()).hexdigest(),
        }
        q = EvidenceQuarantine(expected)
        # Tamper the schema hash afterwards.
        _write(root, mrel, {"schema_hash": "5" * 64, "run_id": "run_1"})
        rec = q.classify(root, mrel)
        assert rec["classification"] == "TAMPERED"

    def test_missing_evidence_is_not_verified(self, tmp_path):
        root = build_good_tree(tmp_path)
        q = self._quarantine(root)
        os.remove(os.path.join(root, RP_REL))
        rec = q.classify(root, RP_REL)
        assert rec["classification"] == "NOT_VERIFIED"

    def test_unexpected_foreign_evidence(self, tmp_path):
        root = build_good_tree(tmp_path)
        foreign = "evidence/unknown_dir/foreign.json"
        _write(root, foreign, {"verdict": "PASS"})
        q = self._quarantine(root)
        rec = q.classify(root, foreign)
        assert rec["classification"] == "FOREIGN"

    def test_stale_checker_is_stale(self, tmp_path):
        """Scenario 5: evidence pinned to an older checker identity
        than the current authoritative one -> STALE (not PASS)."""
        root = build_good_tree(tmp_path)
        q = self._quarantine(root, current_identities={
            "checker_sha256": CHECKER_SHA})
        doc = json.load(open(os.path.join(root, F3M_REL)))
        doc["provenance"] = {"script_sha256": "0" * 64}
        _write(root, F3M_REL, doc)
        # Rebuild quarantine with pins matching the NEW file content.
        q2 = self._quarantine(root, current_identities={
            "checker_sha256": CHECKER_SHA})
        rec = q2.classify(root, F3M_REL)
        assert rec["classification"] == "STALE"
        assert "checker" in rec["reason"]

    def test_stale_gate_count_is_stale(self, tmp_path):
        root = build_good_tree(tmp_path)
        _write(root, RP_REL, {"verdict": "PASS", "checks_total": 95,
                              "checks_failed": 0, "gate_count": 16})
        q = self._quarantine(root, current_identities={
            "gate_count": 21})
        rec = q.classify(root, RP_REL)
        assert rec["classification"] == "STALE"

    def test_malformed_evidence_is_quarantined(self, tmp_path):
        root = build_good_tree(tmp_path)
        q = self._quarantine(root)
        path = os.path.join(root, RP_REL)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not json at all")
        # Re-pin to the malformed content so parse failure is reached.
        expected = {
            RP_REL: hashlib.sha256(open(path, "rb").read()).hexdigest(),
        }
        q2 = EvidenceQuarantine(expected)
        rec = q2.classify(root, RP_REL)
        assert rec["classification"] == "QUARANTINED"

    def test_screening_with_rejected_never_clean(self, tmp_path):
        root = build_good_tree(tmp_path)
        q = self._quarantine(root)
        doc = json.load(open(os.path.join(root, F3M_REL)))
        doc["rows"] = 1
        _write(root, F3M_REL, doc)
        report = q.screen(root)
        assert report["verdict"] == "EVIDENCE_REJECTED"
        assert report["rejected_count"] >= 1

    def test_rejected_classes_never_include_pass(self):
        for cls in ("STALE", "FOREIGN", "TAMPERED", "QUARANTINED"):
            assert cls in REJECTED_CLASSES
        assert "PASS" not in REJECTED_CLASSES
        assert "VERIFIED" not in REJECTED_CLASSES

    def test_unanchored_evidence_stays_not_verified(self, tmp_path):
        root = build_good_tree(tmp_path)
        q = EvidenceQuarantine({RP_REL: None})
        rec = q.classify(root, RP_REL)
        assert rec["classification"] == "NOT_VERIFIED"
        assert "cannot verify" in rec["reason"]


# ----------------------------------------------------------------------
# 10: modified release-artifact manifest (uses the real repo scanner)
# ----------------------------------------------------------------------

class TestReleaseArtifactManifestTamper:

    def test_tampered_artifact_fails_verify(self, tmp_path, monkeypatch):
        import scripts.build_release_artifact_manifest as bam
        # Build a tiny manifest over the tmp tree, then tamper.
        art = os.path.join(str(tmp_path), "a.json")
        with open(art, "w", encoding="utf-8") as f:
            json.dump({"x": 1}, f)
        entry = {
            "path": "a.json",
            "sha256": hashlib.sha256(
                open(art, "rb").read()).hexdigest(),
            "size_bytes": os.path.getsize(art),
        }
        manifest = {"artifacts": [entry]}
        monkeypatch.setattr(bam, "REPO_ROOT", str(tmp_path))
        monkeypatch.setattr(bam, "ARTIFACT_TABLE",
                            (("a.json", None, None, "pre_zip"),))
        assert bam.verify(manifest, require_complete=False) == []
        # Tamper the artifact; verify must now report the drift.
        with open(art, "w", encoding="utf-8") as f:
            json.dump({"x": 2}, f)
        problems = bam.verify(manifest, require_complete=False)
        assert problems, "hash drift must be detected"
        assert any("hash drift" in p for p in problems)

    def test_modified_manifest_fails_on_missing_artifact(
            self, tmp_path, monkeypatch):
        import scripts.build_release_artifact_manifest as bam
        art = os.path.join(str(tmp_path), "a.json")
        with open(art, "w", encoding="utf-8") as f:
            json.dump({"x": 1}, f)
        manifest = {"artifacts": [{
            "path": "a.json",
            "sha256": hashlib.sha256(
                open(art, "rb").read()).hexdigest(),
            "size_bytes": os.path.getsize(art),
        }]}
        monkeypatch.setattr(bam, "REPO_ROOT", str(tmp_path))
        monkeypatch.setattr(bam, "ARTIFACT_TABLE",
                            (("a.json", None, None, "pre_zip"),))
        os.remove(art)  # manifest now references a deleted artifact
        problems = bam.verify(manifest, require_complete=False)
        assert any("missing artifact" in p for p in problems)


# ----------------------------------------------------------------------
# Fingerprint determinism (Phase 4F invariants)
# ----------------------------------------------------------------------

class TestReproducibilityFingerprint:

    def test_fingerprint_file_matches_its_components(self):
        path = os.path.join(
            REPO_ROOT, "evidence/release/reproducibility_fingerprint.json")
        if not os.path.isfile(path):
            pytest.skip("fingerprint not yet built in this checkout")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        recomputed = hashlib.sha256(json.dumps(
            doc["components"], sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        assert recomputed == doc["reproducibility_fingerprint_sha256"]

    def test_fingerprint_excludes_timestamps(self):
        path = os.path.join(
            REPO_ROOT, "evidence/release/reproducibility_fingerprint.json")
        if not os.path.isfile(path):
            pytest.skip("fingerprint not yet built in this checkout")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        blob = json.dumps(doc["components"])
        for forbidden in ("generated_utc", "recorded_utc", "timestamp",
                          "duration"):
            assert forbidden not in blob, (
                f"nondeterministic field {forbidden} leaked into the "
                "cryptographic identity")

    def test_component_identities_present(self):
        path = os.path.join(
            REPO_ROOT, "evidence/release/reproducibility_fingerprint.json")
        if not os.path.isfile(path):
            pytest.skip("fingerprint not yet built in this checkout")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        comps = doc["components"]
        for key in ("code_identity", "rule_set_identity",
                    "schema_identity", "checker_identity",
                    "test_identity", "environment_identity"):
            assert key in comps
        # Rule-set identity must still be the frozen V1 source hash.
        assert comps["rule_set_identity"]["sha256"] == V1_SHA


# ----------------------------------------------------------------------
# Rule impact graph invariants (Phase 4E)
# ----------------------------------------------------------------------

class TestRuleImpactGraph:

    def test_graph_covers_exactly_v1(self):
        path = os.path.join(
            REPO_ROOT, "evidence/release/rule_impact_graph.json")
        if not os.path.isfile(path):
            pytest.skip("impact graph not yet built in this checkout")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        assert doc["rule_set"]["rule_count"] == 8
        assert doc["rule_set"]["registry_exactly_v1"] is True
        assert doc["problems"] == []
        for rid, node in doc["rules"].items():
            assert node["schema_dependencies"], (
                f"{rid}: schema deps must be machine-derived and non-empty")
            assert node["implementation"]["rule_version"] == "1.0.0"
            assert "affected_evidence_if_changed" in node


# ----------------------------------------------------------------------
# Contradiction checker (Phase 6) — detection and exemption calibration
# ----------------------------------------------------------------------

class TestContradictionChecker:

    def _cc(self):
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)
        from data_quality_platform.assurance import contradiction_checker
        return contradiction_checker

    def test_honest_negations_are_not_flagged(self):
        cc = self._cc()
        for text in [
            "ClickHouse runtime not executed; static SQL only.",
            "Airflow | statically verified DAG, runtime not installed",
            "no 100M/800M scalability claim is made",
            "no Run 3 was created; the official pair is Run 1 + Run 2",
            "synthetic data; never described as real rows",
            "production data mutation: NONE",
            # scope-exclusion boundary statements (README section 13
            # pattern): documented out-of-scope items are not overclaims
            "Out of scope: production ClickHouse/Airflow integration "
            "(unverified); 100M/800M-row certification; changes to "
            "Frozen V1 semantics; kernel sandboxing.",
            "100M/800M-row certification is out-of-scope for this "
            "release.",
        ]:
            hits = []
            for patterns in cc.PROSE_PATTERNS.values():
                for pat in patterns:
                    hits += cc._flag_unnegated(text, pat)
            assert hits == [], f"false positive on: {text!r} -> {hits}"

    def test_positive_overclaims_are_flagged(self):
        cc = self._cc()
        cases = [
            ("the platform was validated on ClickHouse",
             "clickhouse_execution_claim"),
            ("the pipeline ran on Airflow in production",
             "airflow_execution_claim"),
            ("validated at 100M rows per run",
             "scalability_overclaim"),
            # scope-adjacent TRUE overclaims must still fire (the
            # scope-exclusion exemption must not be abusable): a
            # positive execution claim stays a positive claim even
            # when other scope words appear in the same document
            ("in-scope validation included 100M rows per run",
             "scalability_overclaim"),
            ("800M certification completed within the approved "
             "validation plan",
             "scalability_overclaim"),
            ("the system is production ready",
             "readiness_overclaim"),
            ("3,200,000 real rows per run",
             "real_rows_terminology"),
            ("bounded memory execution",
             "bounded_memory_claim"),
            ("the release gate is 16 gates",
             "stale_gate_count"),
            ("715 passed tests",
             "stale_test_counts"),
            ("Run 3 completed successfully",
             "run3_positive_claim"),
        ]
        for text, expected_type in cases:
            flagged = set()
            for label, patterns in cc.PROSE_PATTERNS.items():
                for pat in patterns:
                    if cc._flag_unnegated(text, pat):
                        flagged.add(label)
            assert expected_type in flagged, (
                f"{text!r} not flagged as {expected_type}")

    def test_historical_context_is_exempt(self):
        cc = self._cc()
        for text in [
            "Supersedes: DQAVP-Enterprise-Hardened-Validation-Release",
            "stale 16-gate references were corrected",
            "superseded values (715 passed) fail the check",
        ]:
            hits = []
            for patterns in cc.PROSE_PATTERNS.values():
                for pat in patterns:
                    hits += cc._flag_unnegated(text, pat)
            assert hits == [], f"historical context flagged: {text!r}"

    def test_checker_fails_on_current_doc_contradiction(self, tmp_path):
        """A current doc carrying a wrong gate count must produce
        CONTRADICTIONS_FOUND (fail-closed), and the report must carry
        the conflicting value."""
        cc = self._cc()
        root = str(tmp_path)
        # Minimal doc set: a release manifest declaring the release
        # name, and a "current" doc with a wrong gate count.
        _write(root, "release_manifest.json", {
            "release_name": "DQAEIP-Test-Release",
            "release_date": "2026-09-17",
        })
        _write(root, "evidence/release_gate/final_release_gate.json", {
            "gate_count": 21, "overall_verdict": "PASS",
        })
        _write(root, "evidence/release/bad_doc.json", {
            "gate_count": 16,
        })
        report = cc.run_contradiction_check(root)
        assert report["verdict"] == "CONTRADICTIONS_FOUND"
        assert any(c["type"] == "gate_count_conflict"
                   and c["doc"] == "evidence/release/bad_doc.json"
                   for c in report["contradictions"])

    def test_checker_clean_minimal_tree_consistent(self, tmp_path):
        cc = self._cc()
        root = str(tmp_path)
        _write(root, "release_manifest.json", {
            "release_name": "DQAEIP-Test-Release",
            "release_date": "2026-09-17",
        })
        _write(root, "evidence/release_gate/final_release_gate.json", {
            "gate_count": 21, "overall_verdict": "PASS",
        })
        _write(root, "evidence/release/ok_doc.json", {
            "note": "honest note; ClickHouse runtime not executed",
        })
        report = cc.run_contradiction_check(root)
        assert report["verdict"] == "CONSISTENT"

    def test_self_output_excluded_from_scan(self, tmp_path):
        """The checker must not scan its own output (self-reference)."""
        cc = self._cc()
        root = str(tmp_path)
        _write(root, "evidence/release/contradiction_check.json", {
            "contradictions": [
                {"type": "real_rows_terminology",
                 "context": "3,200,000 real rows per run"},
            ],
        })
        report = cc.run_contradiction_check(root)
        assert "evidence/release/contradiction_check.json" \
            not in report["docs_scanned"]
