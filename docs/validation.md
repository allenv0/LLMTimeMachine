# Validation

Manual real-model validation record for protocol `local-v1`. Fill rows after each hardware run. Do not conceal failures.

## Automated coverage (CI / local `pytest`)

| Area | Status | Notes |
|---|---|---|
| Registry validation | done | unit tests |
| Adapter rendering | done | unit tests |
| Manifest serialization | done | unit tests |
| Atomic store / delete | done | unit tests |
| Export isolation | done | unit tests |
| Preflight reporting | done | unit tests with fakes |
| Trip orchestration (fake runner) | done | partial/failed/cancelled/complete |
| Blind mapping stability | done | unit tests |
| UI service contracts | done | service-layer tests |

## Per-model manual matrix

For every real cohort model, complete:

1. Source revision, license, and local checksum verified.
2. Short prompt; audit input matches runner input exactly.
3. Cold load time, warm load time, generation time, peak memory (if available), output length.
4. Same prompt twice with frozen seed; record determinism.
5. `unload()` frees enough memory for the next model.
6. Intentional failure preserves partial trip.

| Model id | Rev/license/checksum | Audit match | Timings | Determinism | Unload | Failure path | Reviewer | Date |
|---|---|---|---|---|---|---|---|---|
| gpt2-xl-2019 | pending | pending | pending | pending | pending | pending | | |
| gpt-j-6b-2021 | pending | pending | pending | pending | pending | pending | | |
| flan-t5-xl-2022 | pending | pending | pending | pending | pending | pending | | |
| mistral-7b-instruct-2023 | pending | pending | pending | pending | pending | pending | | |
| qwen25-7b-instruct-2024 | pending | pending | pending | pending | pending | pending | | |

## Complete-cohort checks

| Check | Status | Notes |
|---|---|---|
| Network disabled after cache | pending | |
| Five distinct prompts (incl. one without dramatic progress) | pending | |
| Ten consecutive trips, no restart | pending | |
| Delete/export on a real trip | pending | |
| Independent audit-drawer + manifest trace | pending | |

## Hardware profiles exercised

| Host | Profile | Cohort | Full-trip wall time | Date |
|---|---|---|---|---|
| | | | | |

## Acceptance metrics (product decision, not marketing)

Record observations from non-builders when available:

| Metric | Result |
|---|---|
| ≥5 non-builders complete a trip with their own prompt | |
| ≥3 run a second prompt or open the audit drawer | |
| Users can explain the cohort limitation after use | |
| Run→final latency measured per hardware profile | |
| Stable across 10 consecutive local trips after weights cached | |
