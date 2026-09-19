# Data Quality Assurance & Evidence Integrity Platform

**DQAEIP** — evidence-driven data quality validation with a full
clean-room evidence integrity layer, now wrapped in an additive
operational-hardening bundle (layers A–H).

[![Status](https://img.shields.io/badge/status-PASS_WITH_DOCUMENTED_LIMITATIONS-yellow)](#15-final-release)
[![Release](https://img.shields.io/badge/release-HARDENED%202026--09--19-blue)](#1-release-identity)
[![Baseline](https://img.shields.io/badge/certified%20baseline-2026--09--18%20%C2%B7%204ecbfc16-lightgrey)](#2-certified-baseline-2026-09-18)
[![Validation](https://img.shields.io/badge/validation-3200000%20rows%20%C3%97%202%20runs-brightgreen)](#3-current-validation--regression-2026-09-19)
[![Oracle](https://img.shields.io/badge/oracle-51%2C200%2C000%20comparisons%20%7C%200%20mismatches-brightgreen)](#3-current-validation--regression-2026-09-19)
[![Determinism](https://img.shields.io/badge/determinism-byte--identical-brightgreen)](#4-validation-evidence)
[![Frozen V1](https://img.shields.io/badge/frozen%20V1-8%20rules%20%C2%B7%20daef1ded-blue)](#5-frozen-v1-rule-set)
[![Hardening](https://img.shields.io/badge/hardening-8%20layers%20A%E2%80%93H%20%C2%B7%2017%20negative%20scenarios-brightgreen)](#6-hardening-layers-a-h)
[![Tests](https://img.shields.io/badge/tests-1089%20passed%20%2B%209%20skipped-brightgreen)](#10-release-gates)
[![Safety](https://img.shields.io/badge/runtime%20safety-audit--hook%20measured-blue)](#12-security--runtime-safety)

<!-- generated-utc-stamp: 2026-09-19T13:24:34Z -->

> **Executive summary.** This release is the **2026-09-19 hardened
> release**: the same certified DQAEIP core (Frozen V1, byte-identical),
> wrapped in eight additive operational-security layers (input contract
> firewall, execution authorization, idempotency, atomic commit,
> checkpoint contract, schema guard, reference-data versioning, resource
> guard). The certified 2026-09-18 baseline is preserved byte-for-byte
> and referenced as history. The full 3,200,000-row dual-run validation
> was re-executed on 2026-09-19 through the frozen checker and
> reproduced every certified fact exactly: 51,200,000 oracle
> comparisons, **0 mismatches**, byte-identical outputs. All release
> claims below are machine-derived from the current evidence tree and
> re-derivable on demand; documentation is never a second source of
> truth.

---

## 1. Release Identity

| Property | Value |
|---|---|
| Release ID | `DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19` |
| Release date | 2026-09-19 |
| Release kind | **Operational hardening, additive only** — no change to Frozen V1, no change to the certified baseline |
| Project | Data Quality Assurance & Evidence Integrity Platform (DQAEIP) |
| Technical package | `data_quality_platform` (Python, unchanged for compatibility) |
| Hardening bundle | `data_quality_platform/hardening/` (layers A–H + orchestrator, version 1.0.0) |
| Build head | `970b57f7894253340e3f7789f886b0402f9f363a` (branch `main`; local only, nothing pushed) |
| Final verdict | **PASS_WITH_DOCUMENTED_LIMITATIONS** |

## 2. Certified Baseline — 2026-09-18

> **Historical reference (BASELINE_CERTIFIED_HISTORICAL).** The
> following identifies the certified prior release. It is preserved
> byte-for-byte and is NOT modified, weakened, or reinterpreted by this
> release.

| Property | Value |
|---|---|
| Baseline release ID | `DQAEIP-FINAL-CLEAN-REBUILD-RELEASE-2026-09-18` |
| Baseline date | 2026-09-18 |
| Baseline status | PASS_WITH_DOCUMENTED_LIMITATIONS |
| Baseline ZIP SHA-256 | `4ecbfc16da7ddaa1…` (full hash pinned in `evidence/FINAL_HARDENED_RELEASE_2026-09-19/release_identity/RELEASE_IDENTITY.json` and the sidecar; presented here as a prefix by the release-document hash policy) |
| Baseline ZIP members | 460 (2,001,588 bytes) |
| Recovery | byte-recoverable at git HEAD `fb4df92` (nested repo) and via the certified ZIP + sidecar |
| Relationship to this release | additive hardening only; the baseline evidence tree and its ZIP were re-hash-verified (unmodified) at this release's build |

## 3. Current Validation — Regression 2026-09-19

The 3,200,000-row dual-run regression (Run 1 + Run 2) re-executed on
2026-09-19 through the frozen checker:

| Property | Value |
|---|---|
| Rows per run | **3,200,000** |
| Complete runs | **2** (Run 1 + Run 2) |
| Oracle comparisons | **25,600,000 per run · 51,200,000 combined** |
| Oracle mismatches | **0** (both runs) |
| Outputs | **byte-identical** across both runs (`filecmp.cmp`, shallow=False, executed at finalize) |
| Runtime safety | **PASS** on both runs (audit-hook measured) |
| SP1 frozen verification | **PASS** — exactly the 8 frozen V1 rules executed in both runs |
| Baseline reproduction | every certified fact reproduced exactly (input/output hashes, comparison counts, zero mismatches, determinism) |
| Checker identity | `scripts/final_3m_validation.py` · SHA-256 `0ef7c10c14a1df317c23cb0dfc73b3a60c2257c064b35080d694e5fe8bc50d84` (byte-identical to the harness that produced the certified 2026-09-18 evidence) |

Final 3M checker verdict: PASS (fail-closed verdict gate; both runs
participate in every check — a passing Run 1 can never hide a failing
Run 2). Every run passed all 16 required verification dimensions
(schema, row/column counts and order, row identity and ordering,
source-value preservation, output shape, flag domain, independent
oracle).

## 4. Validation Evidence

| Evidence | Value |
|---|---|
| Input SHA-256 | `59624a53c72f908f1dde673ceecf59e0662ae721bb8f9af7e165acba5318d153` |
| Output SHA-256 | `b72adc235160a86e0b99a08f988dd0bb5f2cff82bbe5b5d28ea07c5a5719329a` |
| Dataset dimensions | 33 input columns → 41 output columns (8 flag columns) |
| Input size | 783,406,620 bytes per run |
| Output size | 834,606,817 bytes per run |
| Total staged runtime | 620.586 s (generation + validation + verification, both runs) |
| Peak RSS | 2365.29 MB (engine, RUSAGE_CHILDREN) |
| Determinism | `True` — byte-identical, proven at finalize |
| Evidence namespace | `evidence/validation/2026-09-19/fresh_3m2/` |

| Run | Run ID | Rows | Status | Stage runtime (gen/validate/verify) | Safety | SP1 |
|---|---|---|---|---|---|---|
| Run 1 | `final_3m_pass1` | 3,200,000 | PASS | 86.898s / 157.005s / 67.77s | PASS | PASS |
| Run 2 | `final_3m_pass2` | 3,200,000 | PASS | 84.104s / 156.711s / 68.098s | PASS | PASS |

## 5. Frozen V1 Rule Set

Exactly **8 frozen V1 rules**; source `data_quality_platform/rules/v1_rules.py`
SHA-256 `daef1ded54c7d3c79898a1ba253be2acd5b6120e18b16b09009fdd7be9fc2276`
(byte-identical to the immutable frozen baseline — re-verified by test
and by the evidence builder at this release's build).

| Rule ID | Version | Implementation hash |
|---|---|---|
| `email_blank` | 1.0.0 | `157ccc2127334bac…` |
| `email_syntax_failure` | 1.0.0 | `5caaba13a73c90c5…` |
| `first_name_cleaning_candidate` | 1.0.0 | `575e9d4588334d36…` |
| `geography_mismatch_candidate` | 1.0.0 | `7967b59ef7a14b83…` |
| `last_name_cleaning_candidate` | 1.0.0 | `c553b7f4484b5413…` |
| `name_cleaning_candidate` | 1.0.0 | `3a128ec85d196cd3…` |
| `proposed_email_export_eligible` | 1.0.0 | `6732e6bfed6fae3c…` |
| `zip_state_assessable` | 1.0.0 | `e7730c1b848f3279…` |

The rule matrix consumed as the pinned baseline by the checker is the
certified 2026-09-18 matrix, re-verified: 8/8 rule IDs exact match, V1
source pin intact. No competing rule definitions exist; SP1 (successor
geography) remains validation-only and unregistered. **The hardening
bundle does not modify Frozen V1** — any hardening change that would
require touching V1 is out of scope and was not made.

## 6. Hardening Layers A–H

New in this release: an additive operational-security bundle wrapping
the certified core. Full module registry with SHA-256 identities lives
at `evidence/FINAL_HARDENED_RELEASE_2026-09-19/hardening_layers/layer_registry.json`.

| Layer | Name | Module | Status |
|---|---|---|---|
| A | Input Contract Firewall | `input_contract.py` | implemented |
| B | Execution Authorization Gate | `authorization.py` | implemented |
| C | Idempotency / Duplicate-Run Protection | `idempotency.py` | implemented |
| D | Atomic Output Commit | `atomic_commit.py` | implemented |
| E | Checkpoint / Safe-Resume Contract | `checkpoint_contract.py` | contract-only (by design) |
| F | Schema Evolution Guard | `schema_guard.py` | implemented |
| G | Reference-Data Versioning | `reference_data.py` | implemented |
| H | Resource / Execution Guard | `resource_guard.py` | implemented |
| ORCH | Hardened Execution Orchestrator | `pipeline.py` | implemented |

- **A — Input Contract Firewall**: input identity (full SHA-256 pin),
  size and row caps, strict UTF-8, NUL-byte scan, exact header
  (names/order/count), sampled type contract. Rejected input never
  reaches execution.
- **B — Execution Authorization Gate**: authorization binds input SHA +
  schema fingerprint + V1 rule-set SHA + reference-data fingerprint +
  config fingerprint + execution mode + software identity (10 pinned
  artifacts); any single divergence fails closed.
- **C — Idempotency / Duplicate-Run Protection**: deterministic
  execution identity + atomic execution ledger; duplicates are safely
  identified (committed outputs re-hashed) or blocked (PARTIAL /
  tampered / missing); committed entries are immutable history.
- **D — Atomic Output Commit**: staging directories carry a
  PARTIAL_MANIFEST marker; every member is independently verified and
  hashed before a single atomic rename finalizes the release directory
  with a COMMITTED_MANIFEST. Partial artifacts are always
  distinguishable from committed ones.
- **E — Checkpoint / Safe-Resume Contract**: **contract-only by
  design** — resume is refused (4 documented risks); interrupted runs
  re-execute from scratch. Determinism makes the fresh full run the
  safe equivalent.
- **F — Schema Evolution Guard**: classifies observed vs authorized
  schema as SCHEMA_COMPATIBLE / SCHEMA_INCOMPATIBLE (deletion,
  reorder, rename, insertion, type or nullability drift) /
  REQUIRES_AUTHORIZATION (strictly trailing additive columns).
- **G — Reference-Data Versioning**: content-addressed (SHA-256)
  versioning of reference artifacts; no external authority is claimed
  for the state/ZIP prefix table (documented limitation).
- **H — Resource / Execution Guard**: input size/row ceilings, runtime
  wall-time and peak-RSS monitor thread (SIGKILL on breach), output
  size ceiling — all fail-closed.

The orchestrator (`hardening.pipeline.run_hardened_execution`) wires
A → F → G → B → C → H → engine subprocess → H → D → C and emits a
machine-readable execution report; the engine command is identical to
the canonical CLI invocation.

## 7. Negative Scenario Battery

17 mandated negative scenarios plus positive controls —
**21 tests, all passing**:
wrong input hash, wrong/missing/reordered/retyped schema, changed V1
rule-set hash, changed config, changed reference fingerprint, duplicate
execution (idempotent — engine proven not re-executed), authorization
mismatch (missing/wrong grant, software drift, unknown mode), partial
output, interrupted run (PARTIAL ledger + Layer E refusal), stale
checkpoint, cross-input checkpoint, resource limits, unknown schema,
tampered manifest/output (hash-drift detection), malformed ledger.
Details: `evidence/FINAL_HARDENED_RELEASE_2026-09-19/negative_battery/`.

## 8. Independent Verification

The independent oracle is a from-scratch reimplementation of the 8
frozen V1 predicates (zero imports from the production package),
executed by the frozen checker over both runs: 25,600,000 comparisons
per run, 0 mismatches. Determinism is proven by actual byte comparison
of both outputs at finalize. The checker itself is pinned by SHA-256
and was byte-identical to the harness that produced the certified
baseline evidence. SP1 frozen verification confirms exactly the 8
frozen rules executed in both runs. The run-pair verification report
re-checks 95/95 identity and determinism checks (Run 1 +
Run 2) directly against the run artifacts.

## 9. Performance and Hardening Overhead

Measured on the identical engine command: engine-only subprocess vs
the full layers A–H hardened pipeline.

| Rung | Rows | Engine-only | Hardened | Overhead | Rows/s (hardened) |
|---|---|---|---|---|---|
| 1K | 1,000 | 0.199s | 0.203s | 0.004s (2.01%) | 4,926.1 |
| 10K | 10,000 | 0.604s | 0.649s | 0.045s (7.45%) | 15,408.3 |
| 100K | 100,000 | 4.825s | 5.228s | 0.403s (8.35%) | 19,127.8 |
| 1M | 1,000,000 | 49.897s | 54.0s | 4.103s (8.22%) | 18,518.5 |
| 3.2M | 3,200,000 | 157.005s | 169.414s | 12.409s (7.9%) | 18,888.6 |

Overhead at scale is dominated by full-content SHA-256 hashing of the
input and output plus atomic-commit manifest writing — the certified
3.2M engine run (157.0 s) plus 12.4 s of hardening. Method details:
`evidence/FINAL_HARDENED_RELEASE_2026-09-19/performance/`.

## 10. Release Gates

The 22-gate fail-closed release gate (repository integrity, test categories, differential validation, mutation, replay, evidence validation, provenance, references, safety, PII scan, performance, production integrity, assurance battery, path firewall, negative gate, claim provenance, consistency matrix, absolute-path gate) runs on the committed release tree; the terminal round verdict is **PASS — 22/22 fail-closed gates**, claimed from the live artifact only.

| Gate | Result |
|---|---|
| Full test suite | **1098 collected — 1089 passed / 9 skipped / 0 failed** (fresh run; includes the 21 hardening-battery tests) |
| Hardening negative battery | **21/21** (17 mandated scenarios + positive controls) |
| Regression baseline reproduction | **exact** (all certified facts matched; fail-closed assertions in the evidence builder) |
| Frozen V1 immutability | verified (hash + test + evidence builder) |
| Baseline ZIP integrity | re-verified (hash + sidecar) |
| Business mutation testing | **17/17** mutants detected, source restored byte-exactly |
| Assurance mutation battery | **14/14** controlled assurance failures rejected, restoration verified |
| Run-pair verification | **95/95** checks (Run 1 + Run 2) |
| Evidence namespace integrity | 9 claims, every claim carries source + SHA-256 + derivation + verifier |
| Release gate verdict | **PASS — 22/22 fail-closed gates** (terminal round on the committed tree; live artifact `evidence/release_gate/final_release_gate.json`) |

## 11. Provenance and Reproducibility

- Evidence tree regenerated for 2026-09-19; every JSON in the namespace
  is hashed in `integrity/integrity_report.json`.
- The dataset is deterministic (seed 20260918, 3,200,000 rows): both
  passes regenerate the identical input (SHA
  `59624a53…8d153`) and the engine reproduces the identical output
  (SHA `b72adc23…1929a`).
- The 2026-09-18 certified baseline is referenced as history only
  (ZIP + sidecar + git HEAD `fb4df92`), never as current evidence.
- Historical evidence (2026-09-15 era and earlier) exists exclusively
  in git history; it was deliberately removed from the working tree by
  the 2026-09-18 clean-room rebuild and is not part of this release.

## 12. Security / Runtime Safety

- Runtime safety is audit-hook measured per run (frozen wrapper):
  0 socket events, 0 process-exec events, 6 filesystem mutations all
  within the repository root — **PASS on both runs**. Audit hooks are
  cooperative CPython instrumentation (observability), not a kernel
  sandbox; no kernel-sandbox claim is made.
- ClickHouse and Airflow are not executed in any certified run;
  observability evidence for those systems is simulated.
- The hardening bundle adds authorization, atomicity, and fail-closed
  resource enforcement at the orchestration layer; it does not change
  engine execution semantics.

## 13. Current Scope

- In scope: deterministic validation of 33-column consumer records
  against the 8 frozen V1 rules; evidence integrity; operational
  hardening of the execution envelope (this release).
- Out of scope: production ClickHouse/Airflow integration (unverified);
  certification at design-target scales beyond the executed 3.2M-row
  validation (the larger row-count scenarios of the original project
  brief remain uncertified here); changes to Frozen V1 semantics;
  kernel sandboxing.

## 14. Non-Blocking Limitations

**Inherited from the certified baseline (unchanged):**
- **LIM-001 — O(N) memory profile** (VERIFIED_LOCALLY): The engine materializes the full dataset in memory; peak RSS measured 2365.7 MB at 3,200,000 rows (fresh 2026-09-18 run). Memory scales linearly with row count. A bounded-memory design exists as a future design document only; it is intentionally NOT implemented because business-equivalence is unproven. Re-proven by the 2026-09-19 hardened-release regression (fresh dual-run, peak RSS 2365.29 MB, pass2 bulk CSVs reclaimed after the byte-identity proof).
- **LIM-002 — ClickHouse runtime not executed** (NOT_EXECUTED): The ClickHouse storage integration is import-verified only; no ClickHouse server is connected or executed. Client code contains no live connection path (verified boundary check).
- **LIM-003 — Airflow runtime not executed** (NOT_EXECUTED): The Airflow DAG is statically validated only; the Airflow scheduler/executor runtime is not installed or run in this environment.
- **LIM-004 — Authoritative DL fixture unavailable** (NOT_VERIFIED): The authoritative DL001-DL015 geography acceptance table was not supplied by the repo owner; 7 golden tests are skipped with that explicit reason. The fixture is never reconstructed from existing fixtures (anti-fabrication).
- **LIM-005 — SP1 validation-only** (VERIFIED_LOCALLY): The SP1 successor geography layer is implemented for validation only; it is NOT registered in the production rule registry and NOT activated. The fresh 3.2M validation pinned the frozen V1 rule set (regenerated from the frozen source) and verified SP1 absence in BOTH executed run manifests.
- **LIM-006 — E1 not implemented / not authorized** (NOT_AUTHORIZED): E1 is neither implemented nor authorized. Zero E1 identifiers exist in application code (tripwire-enforced boundary test). This registry entry documents that boundary; it is not an implementation plan.
- **LIM-007 — Oracle reference truth is pinned, not independently sourced** (VERIFIED_LOCALLY): The independent oracle re-implements the frozen V1 contract; it is a pinned reference truth, not independently sourced business truth. Perfect engine-vs-oracle agreement (51,200,000 comparisons, 0 mismatches) proves engine-to-contract fidelity, not contract-to-business fidelity.
- **LIM-008 — 3.2M-row validation scale** (VERIFIED_LOCALLY): Production validation executed at 3,200,000 rows (two complete runs, seed 20260918). No claim is made about 100M/800M production scalability from this evidence; performance comparability is limited to the measured host class. Re-proven by the 2026-09-19 hardened-release regression (fresh dual-run, peak RSS 2365.29 MB, pass2 bulk CSVs reclaimed after the byte-identity proof).
- **LIM-009 — Bulk staging CSVs removed after byte-proof** (VERIFIED_LOCALLY): The bulk input/output CSVs of BOTH passes under data/generated/ (gitignored staging) were removed after the byte-identical proof and after the release-verification chain was complete; their SHA-256 values are hash-anchored in the harness evidence. The dataset is deterministically re-derivable from seed 20260918 (generation ~85s per pass). The release gate's evidence-validation documents the by-design staging absence (determinism proven + manifest output SHA equals the byte-proven SHA). Re-proven by the 2026-09-19 hardened-release regression (fresh dual-run, peak RSS 2365.29 MB, pass2 bulk CSVs reclaimed after the byte-identity proof).
- **LIM-010 — ZIP 733xx / TX geography expectations under review** (REVIEW_REQUIRED): Three golden-corpus cases record real-world expectations (mismatch=0) that conflict with the frozen V1 prefix map (73->OK only). The frozen V1 behavior is preserved and the cases are pinned REVIEW_REQUIRED with an exact allowlist; any new drift fails the suite.
- **LIM-011 — Runtime safety is cooperative instrumentation** (VERIFIED_LOCALLY): Runtime safety (0 sockets, 0 exec, in-repo writes only) is measured via CPython audit hooks inside the production CLI subprocess — cooperative observation, not a kernel sandbox.

**New hardening limitations (documented, non-blocking):**
- **LIM-012 — Checkpoint/safe-resume is contract-only**: Layer E ships the checkpoint binding contract but NO resume implementation: resume is refused (partial-write duplication, oracle prefix ambiguity, ledger-state conflation, determinism makes fresh re-run the safe equivalent).
- **LIM-013 — Reference-data provenance is content-addressed only**: Layer G versions reference artifacts by SHA-256 content hash; no external authoritative source exists for the state/ZIP prefix table, so provenance beyond content is not claimed.
- **LIM-014 — Peak-RSS monitoring is sampled**: Layer H samples /proc/<pid>/status VmRSS at 250 ms intervals; sub-interval memory spikes between samples can be missed (wall-time enforcement is exact).
- **LIM-015 — Authorization is not a kernel sandbox**: Layer B binds software identity by file hash at execution time and fails closed on divergence; it does not provide kernel-level sandboxing. Audit hooks remain cooperative CPython instrumentation (as in LIM-011).
- **LIM-016 — Atomic commit is single-filesystem**: Layer D atomicity relies on a single os.rename of the staging directory onto the final directory on one filesystem; cross-filesystem staging requires operator co-location of work and final directories.

**Registry total:** 16 unique registered limitations
(`LIM-001`..`LIM-016`, canonical deduplicated registry at
`evidence/release/limitation_registry.json`).

**Production integration status:** NOT YET VERIFIED — this release
certifies the hardened pipeline in the repository environment;
production ClickHouse/Airflow integration remains unverified
(inherited limitation).

## 15. Reproduction

```bash
# 1. regenerate the deterministic 3.2M dataset (seed 20260918)
.venv/bin/python scripts/final_3m_validation.py --phase generate \
  --pass-no 1 --rows 3200000 --seed 20260918 \
  --data-dir data/generated/fresh_3m2_regression \
  --evidence-dir evidence/validation/2026-09-19/fresh_3m2

# 2. run the production engine (validate + verify, both passes)
.venv/bin/python scripts/final_3m_validation.py --phase validate --pass-no 1 \
  --rows 3200000 --seed 20260918 \
  --data-dir data/generated/fresh_3m2_regression \
  --evidence-dir evidence/validation/2026-09-19/fresh_3m2
.venv/bin/python scripts/final_3m_validation.py --phase verify --pass-no 1 \
  --rows 3200000 --seed 20260918 \
  --data-dir data/generated/fresh_3m2_regression \
  --evidence-dir evidence/validation/2026-09-19/fresh_3m2
#    (repeat with --pass-no 2)

# 3. fail-closed final verdict
.venv/bin/python scripts/final_3m_validation.py --phase finalize \
  --rows 3200000 --seed 20260918 \
  --data-dir data/generated/fresh_3m2_regression \
  --evidence-dir evidence/validation/2026-09-19/fresh_3m2

# 4. hardening battery (17 negative scenarios + positive controls)
.venv/bin/python -m pytest tests/hardening/ -q
```

**Repository structure (release-relevant):**

```
data_quality_platform/hardening/   layers A–H + orchestrator (NEW)
data_quality_platform/rules/       frozen V1 rules (IMMUTABLE)
scripts/final_3m_validation.py     frozen certified checker
scripts/hardening_*.py             this release's build tooling
tests/hardening/                   negative battery (NEW)
evidence/validation/2026-09-19/    fresh 3.2M regression evidence
evidence/FINAL_HARDENED_RELEASE_2026-09-19/  release evidence namespace
evidence/FINAL_CLEAN_REBUILD_RELEASE_2026-09-18/  certified baseline (historical)
```

**Final release.** Verdict: **PASS_WITH_DOCUMENTED_LIMITATIONS**. The
certified 2026-09-18 baseline is preserved byte-for-byte; this release
adds the eight hardening layers and re-validated the full 3.2M
dual-run battery with exact baseline reproduction. Deliverable:
`DQAEIP-FINAL-HARDENED-RELEASE-2026-09-19.zip` (+ `.sha256` sidecar).
