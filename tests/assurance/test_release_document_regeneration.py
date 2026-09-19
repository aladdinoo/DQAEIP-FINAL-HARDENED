"""Live-tree regression tests for the 2026-09-19 release-document
regeneration contracts (builder/source fixes, Phase 1).

These tests enforce, on the LIVE repository tree, the contracts that
were previously only checked by final_verification (which is not part
of the suite): the regenerated release documents must be
schema-conforming, mutually consistent, claim-fresh, and free of the
stale identities that previously failed the contradiction checker.

Mid-transition honesty: while the terminal gate round has not yet
landed its PASS artifact, the gate-derived assertions (gate verdict
PASS) are skipped with an explicit reason — exactly like the other
mid-transition skips in this battery (never a guessed PASS).
"""

import hashlib
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from data_quality_platform.assurance import (  # noqa: E402
    limitation_registry, release_schema)


def _load(rel):
    with open(os.path.join(REPO_ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def _gate_exists():
    return os.path.isfile(os.path.join(
        REPO_ROOT, "evidence", "release_gate",
        "final_release_gate.json"))


class TestEvidenceBuilderDependencyDirection:
    """Phase 3 bootstrap-circularity fix: the evidence builder CONSUMES
    the canonical test summary (fresh execution by
    scripts/capture_test_summary.py) and must NEVER run the full suite
    in-process — the full suite includes these very document tests,
    which read the release documents generated DOWNSTREAM of the
    evidence namespace:

        fresh test execution -> canonical test_summary
            -> evidence namespace -> release documents
            -> release gate -> observability -> final verification
    """

    BUILDER = "scripts/hardening_evidence_builder.py"
    NS_SUITE = ("evidence/FINAL_HARDENED_RELEASE_2026-09-19/test_suite/"
                "test_suite_results.json")
    LEGACY_JUNIT = ("evidence/FINAL_HARDENED_RELEASE_2026-09-19/"
                    "test_suite/_junit_full.xml")

    def test_builder_never_runs_full_suite_in_process(self):
        src = open(os.path.join(REPO_ROOT, self.BUILDER),
                   encoding="utf-8").read()
        # the removed circular mechanism: an in-process full-suite run
        # whose results depend on the documents this namespace builds
        assert 'run_pytest_junit(["tests/"])' not in src, (
            "circularity regressed: evidence builder runs the full "
            "suite in-process (its document tests read the downstream "
            "release documents)")
        # the battery run is NOT circular (no release-document reads)
        # and stays a fresh in-process run
        assert 'run_pytest_junit(["tests/hardening/"], xml)' in src

    def test_ns_suite_record_consumes_canonical_summary(self):
        if not os.path.isfile(os.path.join(REPO_ROOT, self.NS_SUITE)):
            pytest.skip("evidence namespace not built yet")
        ns_suite = _load(self.NS_SUITE)
        ts = _load("evidence/rebuild_verification/test_summary.json")
        assert ns_suite["source"] == (
            "evidence/rebuild_verification/test_summary.json")
        assert ns_suite["source_sha256"] == hashlib.sha256(
            open(os.path.join(
                REPO_ROOT, "evidence", "rebuild_verification",
                "test_summary.json"), "rb").read()).hexdigest()
        for key in ("collected", "passed", "skipped", "failed",
                    "errors"):
            assert ns_suite["stats"][key] == ts[key], key

    def test_ns_legacy_in_process_junit_artifact_absent(self):
        # the removed mechanism's artifact must not exist (the builder
        # deletes any legacy copy at build time; the canonical capture
        # is the authoritative record)
        if not os.path.isdir(os.path.dirname(os.path.join(
                REPO_ROOT, self.NS_SUITE))):
            pytest.skip("evidence namespace not built yet")
        assert not os.path.isfile(os.path.join(REPO_ROOT,
                                               self.LEGACY_JUNIT))

    def test_builder_fails_closed_on_missing_canonical_summary(
            self, tmp_path, monkeypatch):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "heb_under_test", os.path.join(REPO_ROOT, self.BUILDER))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(mod, "CANON_TEST_SUMMARY",
                            tmp_path / "absent.json")
        with pytest.raises(SystemExit, match="FAIL-CLOSED"):
            mod.build_test_suite()

    def test_builder_fails_closed_on_red_canonical_summary(
            self, tmp_path, monkeypatch):
        import importlib.util
        red = tmp_path / "test_summary.json"
        red.write_text(json.dumps({
            "collected": 10, "passed": 8, "skipped": 1, "failed": 1,
            "errors": 0, "all_green": False}), encoding="utf-8")
        spec = importlib.util.spec_from_file_location(
            "heb_under_test", os.path.join(REPO_ROOT, self.BUILDER))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(mod, "CANON_TEST_SUMMARY", red)
        with pytest.raises(SystemExit, match="FAIL-CLOSED"):
            mod.build_test_suite()


class TestLiveReleaseDocumentSchema:
    """Gap 1/2 regression: FINAL_RESULTS + release_manifest conform to
    the certified release schema after the hardening builders run."""

    def test_live_final_results_schema_valid(self):
        problems, _ = release_schema.validate_document(
            os.path.join(REPO_ROOT, "FINAL_RESULTS.json"),
            "final_results")
        assert not problems, problems

    def test_live_final_result_mirror_schema_valid(self):
        problems, _ = release_schema.validate_document(
            os.path.join(REPO_ROOT, "final_result.json"),
            "final_results")
        assert not problems, problems

    def test_live_release_manifest_schema_valid(self):
        problems, _ = release_schema.validate_document(
            os.path.join(REPO_ROOT, "release_manifest.json"),
            "release_manifest")
        assert not problems, problems

    def test_live_final_results_identity_blocks_present(self):
        fr = _load("FINAL_RESULTS.json")
        for key in ("release_identity", "project_identity",
                    "rule_identity", "runs", "test_identity"):
            assert key in fr, f"FINAL_RESULTS missing {key}"
        assert fr["release_identity"]["release_name"] == (
            "DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19")
        assert fr["runs"]["run_1"]["run_id"] == "final_3m_pass1"
        assert fr["runs"]["run_2"]["run_id"] == "final_3m_pass2"

    def test_live_release_manifest_validation_and_environment(self):
        rm = _load("release_manifest.json")
        assert "validation" in rm and isinstance(rm["validation"], dict)
        assert "environment" in rm and isinstance(rm["environment"],
                                                   dict)
        assert rm["validation"].get("tests", {}).get("passed") is not None

    def test_live_doc_heads_agree(self):
        fr = _load("FINAL_RESULTS.json")
        rm = _load("release_manifest.json")
        assert fr["git_identity"]["head"] == rm["git"]["head"]


class TestLiveClaimsFreshness:
    """Gap 3/4 regression: every value-bearing claim in the live
    FINAL_RESULTS re-derives from the current evidence tree."""

    def test_live_claims_rederive(self):
        from data_quality_platform.assurance import claims as claims_mod
        fr = _load("FINAL_RESULTS.json")
        report = claims_mod.verify_claims(fr.get("claims", []), REPO_ROOT)
        assert report["recheck_passed"], [
            r for r in report["results"] if not r["ok"]]

    def test_live_limitation_registry_is_deduplicated_16(self):
        entries, problems = limitation_registry.load_registry(REPO_ROOT)
        assert not problems, problems
        ids = [e.get("id") for e in entries]
        assert len(ids) == 16, f"expected 16 unique limitations, " \
                               f"got {len(ids)}"
        assert len(set(ids)) == 16, "duplicate limitation ids present"
        assert sorted(ids) == [f"LIM-{i:03d}" for i in range(1, 17)]

    def test_live_final_results_limitation_count_matches_registry(self):
        fr = _load("FINAL_RESULTS.json")
        entries, _ = limitation_registry.load_registry(REPO_ROOT)
        assert len(fr["limitations"]) == len(entries)
        claim = next(c for c in fr["claims"]
                     if c.get("derivation") == "limitation_count")
        assert claim["value"] == len(entries)


class TestLiveReleaseModelArtifacts:
    """Regression for the three evidence/release model artifacts that
    previously carried the stale 2026-09-18 identity and stale test
    counts (contradiction-checker scope)."""

    def test_live_release_evidence_model_is_current(self):
        model = _load("evidence/release/release_evidence_model.json")
        assert model["release_identity"]["release_name"] == (
            "DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19")
        ts = _load("evidence/rebuild_verification/test_summary.json")
        assert model["test_identity"]["collected"] == ts["collected"]
        assert model["test_identity"]["passed"] == ts["passed"]
        assert model["test_identity"]["skipped"] == ts["skipped"]

    def test_live_reproducibility_manifest_is_current(self):
        repro = _load("evidence/release/reproducibility_manifest.json")
        assert repro["release_identity"]["release_name"] == (
            "DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19")
        problems = release_schema.validate_reproducibility_manifest(repro)
        assert not problems, problems

    def test_live_golden_snapshot_identity_is_current(self):
        snap = _load("evidence/release/golden_release_snapshot.json")
        assert snap["release_identity"] == (
            "DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19")


class TestLiveContradictionCheck:
    """The full contradiction checker (gate 21 scope) must be
    CONSISTENT on the live tree after document regeneration."""

    def test_live_contradiction_check_consistent(self):
        from data_quality_platform.assurance import contradiction_checker
        report = contradiction_checker.run_contradiction_check(REPO_ROOT)
        assert report["verdict"] == "CONSISTENT", \
            report["contradictions"][:10]


class TestLiveDocumentFingerprints:
    """Gap 4/5 regression: RELEASE_NOTES carries the current I/O hash
    fingerprints; README carries the evidence-derived values the §10
    checker requires."""

    def test_release_notes_carry_io_fingerprints(self):
        fr = _load("FINAL_RESULTS.json")
        notes = open(os.path.join(REPO_ROOT, "RELEASE_NOTES.md"),
                     encoding="utf-8").read()
        inp = fr["verification"]["input_sha256"]
        out = fr["verification"]["output_sha256"]
        assert inp[:16] in notes, "RELEASE_NOTES missing input " \
                                  "fingerprint"
        assert out[:16] in notes, "RELEASE_NOTES missing output " \
                                  "fingerprint"

    def test_readme_carry_io_fingerprints(self):
        fr = _load("FINAL_RESULTS.json")
        readme = open(os.path.join(REPO_ROOT, "README.md"),
                      encoding="utf-8").read()
        assert fr["verification"]["input_sha256"][:16] in readme
        assert fr["verification"]["output_sha256"][:16] in readme

    def test_readme_only_authoritative_full_shas(self):
        """The README consistency checker rejects any full 64-hex SHA
        that is not one of the four authoritative hashes (input /
        output / checker / frozen V1)."""
        import re
        readme = open(os.path.join(REPO_ROOT, "README.md"),
                      encoding="utf-8").read()
        fr = _load("FINAL_RESULTS.json")
        rp = _load("evidence/rebuild_verification/"
                   "run_pair_verification.json")
        import hashlib
        v1_sha = hashlib.sha256(open(
            os.path.join(REPO_ROOT, "data_quality_platform", "rules",
                         "v1_rules.py"), "rb").read()).hexdigest()
        authoritative = {
            fr["verification"]["input_sha256"],
            fr["verification"]["output_sha256"],
            rp.get("checker_script_sha256_actual"),
            v1_sha,
        }
        found = set(re.findall(r"\b[0-9a-f]{64}\b", readme))
        stale = found - authoritative
        assert not stale, f"stale/unknown full SHAs in README: " \
                          f"{[s[:12] for s in stale]}"

    def test_readme_consistency_check_live(self):
        # the §10 checker derives its required values from the live
        # evidence — including the release-gate artifact; mid-transition
        # (terminal gate round pending) it honestly reports the missing
        # gate source, so the full CONSISTENT verdict is asserted only
        # once the gate artifact exists (same discipline as the other
        # mid-transition skips; never a guessed PASS)
        if not _gate_exists():
            pytest.skip("live release-gate artifact absent (mid-"
                        "transition): the §10 checker honestly reports "
                        "the gate source missing — CONSISTENT is "
                        "asserted once the terminal gate round lands "
                        "its artifact")
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        import readme_consistency_check as rcc
        result = rcc.run_check(REPO_ROOT)
        assert result["verdict"] == "CONSISTENT", result["problems"][:10]


class TestLiveGateDocumentState:
    """The documents' gate verdict claims must match the live gate
    artifact state (never a premature PASS; PASS claimed only from the
    live artifact)."""

    def test_gate_verdict_claims_match_live_artifact(self):
        fr = _load("FINAL_RESULTS.json")
        claimed = fr["verification"].get("release_gate_verdict")
        rm = _load("release_manifest.json")
        rm_claimed = rm["validation"].get("release_gate_verdict")
        if not _gate_exists():
            assert claimed in (None, "NOT_VERIFIED")
            assert rm_claimed in (None, "NOT_VERIFIED")
        else:
            gate = _load("evidence/release_gate/"
                         "final_release_gate.json")
            live = gate.get("overall_verdict")
            if live == "PASS":
                # terminal state: the documents MUST carry the live
                # PASS (a stale NOT_VERIFIED after the gate lands is
                # caught here)
                assert claimed == "PASS"
                assert rm_claimed == "PASS"
            else:
                # two-stage build discipline (the same semantics
                # release_chain encodes on the root_to_gate edge): a
                # live FAIL round is a NON-terminal state — the
                # documents must stay pending. Claiming PASS here
                # would be an overclaim (caught); claiming FAIL is
                # forbidden by the chain's gate_to_results edge
                # (only PASS or pending are valid document claims).
                assert claimed in (None, "NOT_VERIFIED")
                assert rm_claimed in (None, "NOT_VERIFIED")

    def test_readme_gate_claim_matches_live_artifact(self):
        readme = open(os.path.join(REPO_ROOT, "README.md"),
                      encoding="utf-8").read()
        if _gate_exists():
            gate = _load("evidence/release_gate/"
                         "final_release_gate.json")
            n = gate.get("gate_count")
            # the gate-count identity strings are required whenever a
            # live gate artifact exists (verdict-independent: the
            # count is a structural property of the gate; a pending
            # README row carries them too)
            assert f"{n} fail-closed gates" in readme
            assert f"{n}-gate" in readme
            if gate.get("overall_verdict") == "PASS":
                # terminal PASS is claimed from the live artifact only
                assert f"PASS — {n}/{n} fail-closed gates" in readme
        else:
            assert "PASS — 22/22 fail-closed gates" not in readme, \
                "README claims a gate PASS without the live artifact"
