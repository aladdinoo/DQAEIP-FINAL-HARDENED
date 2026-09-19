# DQAEIP Release Notes — Operational Hardening 2026-09-19

Product: **Data Quality Assurance & Evidence Integrity Platform (DQAEIP)**
Technical package: `data_quality_platform` (unchanged for compatibility)
Release identity: `DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19`
Supersedes: `DQAEIP-FINAL-CLEAN-REBUILD-RELEASE-2026-09-18`
(certified baseline preserved byte-for-byte and re-verified; not modified)
Final verdict: **PASS_WITH_DOCUMENTED_LIMITATIONS**
(regression checker verdict: **PASS**; full test suite: 1089 passed / 9 skipped / 0 failed)

Current validation fingerprints (2026-09-19 fresh dual-run regression):

- Input SHA-256: `59624a53c72f908f1dde673ceecf59e0662ae721bb8f9af7e165acba5318d153`
- Output SHA-256: `b72adc235160a86e0b99a08f988dd0bb5f2cff82bbe5b5d28ea07c5a5719329a`
- Frozen checker SHA-256: `0ef7c10c14a1df317c23cb0dfc73b3a60c2257c064b35080d694e5fe8bc50d84`
- Frozen V1 rule source SHA-256: `daef1ded54c7d3c79898a1ba253be2acd5b6120e18b16b09009fdd7be9fc2276`
- Run 1 ID: `final_3m_pass1`; Run 2 ID: `final_3m_pass2` (Run 1 + Run 2)

## What changed (this release — operational hardening, additive only)

Built on the certified 2026-09-18 clean-room baseline. **No business
semantics changed; Frozen V1 remains byte-identical** to the immutable
baseline (`daef1ded…` for `v1_rules.py` — re-verified by test, by the
evidence builder, and by the release gate's frozen checks). The
certified baseline ZIP was re-hash-verified (`4ecbfc16da7ddaa1…`)
and is referenced as history only.

This round adds an **operational security hardening bundle** — eight
additive layers wrapping the certified core (plus a pipeline
orchestrator), a 17-scenario negative battery, and a full re-validation:

| # | Change | Type | Files |
|---|---|---|---|
| H1 | **Layer A — Input Contract Firewall**: input SHA-256 pin, size/row caps, strict UTF-8, NUL scan, exact header contract, sampled type contract; rejected input never executes | HARDENING (new) | `data_quality_platform/hardening/input_contract.py` |
| H2 | **Layer B — Execution Authorization Gate**: binds input SHA + schema fingerprint + V1 rule-set SHA + reference-data fingerprint + config fingerprint + execution mode + software identity; single-field divergence fails closed | HARDENING (new) | `data_quality_platform/hardening/authorization.py` |
| H3 | **Layer C — Idempotency / Duplicate-Run Protection**: deterministic execution identity + atomic execution ledger; committed entries immutable; tamper/hash-drift detection | HARDENING (new) | `data_quality_platform/hardening/idempotency.py` |
| H4 | **Layer D — Atomic Output Commit**: staging-with-PARTIAL-manifest → verify → hash → single atomic rename; partial always distinguishable from committed | HARDENING (new) | `data_quality_platform/hardening/atomic_commit.py` |
| H5 | **Layer E — Checkpoint/Safe-Resume Contract**: contract-only by documented design; resume refused (4 risks); fresh full re-run is the safe equivalent | HARDENING (contract) | `data_quality_platform/hardening/checkpoint_contract.py` |
| H6 | **Layer F — Schema Evolution Guard**: COMPATIBLE / INCOMPATIBLE / REQUIRES_AUTHORIZATION classification (deletion, reorder, rename, insertion, type, nullability) | HARDENING (new) | `data_quality_platform/hardening/schema_guard.py` |
| H7 | **Layer G — Reference-Data Versioning**: content-addressed (SHA-256) reference artifacts; no external authority claimed (documented limitation) | HARDENING (new) | `data_quality_platform/hardening/reference_data.py` |
| H8 | **Layer H — Resource/Execution Guard**: input/output ceilings, runtime wall-time + peak-RSS monitor thread, SIGKILL on breach, fail-closed | HARDENING (new) | `data_quality_platform/hardening/resource_guard.py` |
| H9 | Hardened execution orchestrator wiring A→F→G→B→C→H→engine→H→D→C with machine-readable execution reports | HARDENING (new) | `data_quality_platform/hardening/pipeline.py` |
| H10 | 17-scenario negative battery + positive controls (21 tests, all passing): wrong hash/schema/type/rule-set/config/reference, duplicate execution, authorization mismatch, partial output, interrupted run, stale/cross-input checkpoint, resource limits, unknown schema, tampered manifest/output, malformed ledger | TESTS (new) | `tests/hardening/test_hardening_negative_battery.py` |
| H11 | Full 3.2M dual-run regression re-executed via the FROZEN checker (byte-identical harness): every certified fact reproduced exactly — input SHA `59624a53…`, output SHA `b72adc23…`, 25,600,000 oracle comparisons per pass, 0 mismatches, byte-identical outputs, runtime safety PASS, SP1 PASS | VALIDATION (fresh) | `evidence/validation/2026-09-19/fresh_3m2/` |
| H12 | Performance ladder with hardening-overhead measurement: 1K–3.2M engine-only vs hardened pipeline (overhead 7.9% at 3.2M, dominated by full-content hashing + atomic commit) | EVIDENCE (new) | `scripts/hardening_performance_ladder.py`, `evidence/FINAL_HARDENED_RELEASE_2026-09-19/performance/` |
| H13 | Clean evidence namespace for the release (identity, frozen-core verification, layer registry, regression, battery, suite, performance, limitations, claims with source/SHA/derivation/verifier, integrity, path forensics) | EVIDENCE (new) | `evidence/FINAL_HARDENED_RELEASE_2026-09-19/` |
| H14 | README fully regenerated from evidence (15-section structure, consistency-checked); FINAL_RESULTS fully rebuilt to the certified release schema (release/project/rule identity, run_1/run_2, limitation list) distinguishing BASELINE VERIFIED / NEW HARDENING VERIFIED / PRODUCTION-INTEGRATION NOT YET VERIFIED | DOCUMENTS (new) | `README.md`, `FINAL_RESULTS.json`, `final_result.json` |
| H15 | Assurance layer re-pointed to the 2026-09-19 regression evidence; live observability record regenerated (five-dimension separation preserved); release gate re-run against the new release identity with the hardening files in the authorized delta | ASSURANCE | `scripts/build_observability_status.py`, `scripts/release_gate.py` |

## What did NOT change

- **Frozen V1 rules** (`data_quality_platform/rules/v1_rules.py`,
  SHA-256 `daef1ded54c7d3c79898a1ba253be2acd5b6120e18b16b09009fdd7be9fc2276`):
  byte-identical; any hardening that would touch V1 is out of scope.
- **The frozen validation checker**
  (`scripts/final_3m_validation.py`, SHA-256
  `0ef7c10c14a1df317c23cb0dfc73b3a60c2257c064b35080d694e5fe8bc50d84`):
  byte-identical to the harness that produced the certified baseline.
- **The certified 2026-09-18 baseline evidence tree and ZIP**: untouched;
  referenced as BASELINE_CERTIFIED_HISTORICAL.
- **Engine execution semantics**: the hardening layers wrap the canonical
  CLI invocation; the engine command is unchanged.

## Verification summary

| Check | Result |
|---|---|
| 3.2M dual-run regression | PASS — exact certified-baseline reproduction |
| Oracle | 51,200,000 comparisons, 0 mismatches |
| Determinism | byte-identical outputs (filecmp at finalize) |
| Runtime safety | PASS both runs (audit-hook measured) |
| SP1 frozen verification | PASS both runs |
| Full test suite | 1089 passed / 9 skipped / 0 failed |
| Hardening battery | 21/21 (17 mandated negative scenarios + positive controls) |
| Run-pair verification | 95/95 checks (Run 1 + Run 2) |
| Performance overhead | 2.01% (1K) → 7.9% (3.2M) |
| Release gate | **PASS — 22/22 fail-closed gates** (terminal round on the committed release tree) |
| Layer count | 9 modules (8 implemented + 1 contract-only) |

## Known limitations

11 inherited from the certified baseline (O(N) memory
profile; ClickHouse and Airflow not executed in any certified run;
authoritative DL fixture unavailable; SP1 validation-only; E1 not
implemented or authorized; pinned oracle reference truth; 3.2M-row
validation scale; bulk staging CSVs reclaimed after the byte-proof;
ZIP 733xx / TX geography expectations under review; runtime safety is
cooperative instrumentation; and the O(N)-proven fresh regression
re-proof) plus 5 new hardening limitations (Layer E
checkpoint/resume contract-only; reference-data provenance is
content-addressed only; peak-RSS monitoring is sampled at 250 ms;
authorization is not a kernel sandbox; atomic commit is
single-filesystem) — **16 unique registered limitations**
(`LIM-001`..`LIM-016`, deduplicated canonical registry at
`evidence/release/limitation_registry.json`).
Production integration remains **NOT YET VERIFIED**. Full registry:
`evidence/FINAL_HARDENED_RELEASE_2026-09-19/limitations/limitation_registry.json`.

<!--
generated-utc: 2026-09-19T13:24:34Z
generated_utc_stamp: machine-stabilized document; regenerated by
scripts/hardening_release_notes_builder.py from the current evidence
tree (fixed-point write discipline).
-->
