# Gate 4 status: MVP complete?

Checked: 2026-10-12. Criteria: CLAUDE.md, "MVP Success Criteria" and "Gate 4: MVP Complete".
Outcome: **not passed.** Criteria 1 and 2 are unmet. Criterion 3 was removed from MVP scope by
owner decision on 2026-10-12 (see "Scope change"). Criteria 4 and 5 are met. Criterion 6 is
partly met.

## Criteria

| # | Criterion (CLAUDE.md) | Status | Evidence |
|---|---|---|---|
| 1 | Weekly WAPE beats the trailing four-week mean baseline (8.52%) | **Not met** | No candidate beats the baseline. Baseline accepted as the deliverable under trigger T1. `docs/gate3_results.md` |
| 2 | 80%/95% interval coverage within 77–83% / 93–97% | **Not met** | ARIMA: 94.2% / 100%. NB: 88.5% / 94.2%. Neither model is inside both bands. NB 95% is inside its band. `docs/gate3_results.md` |
| 3 | Real-time monitoring latency < 5 minutes | **Descoped to future work (owner decision, 2026-10-12)** | Not measured. The alerts.in.ua API token is not available, and the owner removed the real-time path from the MVP. See "Scope change". |
| 4 | Code reproducible with `python run_pipeline.py` | **Met (offline path)** | `python run_pipeline.py --offline --as-of 2026-10-12` exits 0 and reproduces the Gate 3 numbers exactly (baseline weekly WAPE 0.0852, ARIMA 0.0855, NB 0.1240). The download path (`acquire` without `--offline`) was not re-run in this check. |
| 5 | README, requirements.txt and run_pipeline.py complete | **Met** | Committed in `8df0d05`. Runtime pins match the tested venv. `requirements-dev.txt` covers tooling. |
| 6 | All external sources timestamped before the forecast point | **Partly met** | `output/pipeline_report.json` records the first and last record times for both feeds. Volunteer last record 2026-10-11T04:36:59Z is before the 2026-10-12 as-of date. The forecast is for week 2026-10-05. No live-source timestamps exist, because the real-time path is descoped. |

## Scope change (owner decision, 2026-10-12)

The owner decided not to wait for the alerts.in.ua API token, which is expected in about 7 working
days, and to remove the real-time alerts path from the MVP. The owner also asked that alerts.in.ua
be recorded as future work after the project is done.

This removes criterion 3 from the MVP. It is not a measured pass. Gate 4 criterion 3 should be
read as "descoped", not "met". Any claim about real-time latency must cite a future measurement.

Future work (after MVP): alerts.in.ua real-time poller. It needs an API token, and the token
must be obtained first. Once it arrives, measure latency against the live source and run
`RUN_LOAD_TESTS=1 pytest tests/test_load_alerts_poller.py`. That test counts failed polls and
fails on any error.

## Test status (2026-10-12)

`pytest` gives 106 passed, 3 skipped. The 3 skipped tests are live checks gated by
`RUN_LOAD_TESTS=1`. They were run against the live stack on 2026-10-12:

- `test_redis_latency.py`: passed.
- `test_kafka_lag.py`: passed after the listener fix (Blocker 1). It failed before the fix.
- `test_load_alerts_poller.py::test_sustained_rate_and_latency_live`: fails with the current
  placeholder token. It used to pass without measuring anything, because it swallowed every
  exception and recorded 401 responses as latency samples. It now counts failed polls and asserts
  none occurred (commit `5d6cb41`). The result is out of scope for the MVP and is not evidence
  for criterion 3.

## Gate 4 checklist (CLAUDE.md)

- [x] Pipeline end-to-end working (offline path, verified this session)
- [x] README complete (commit `8df0d05`)
- [x] requirements.txt pinned
- [ ] All success criteria met. Criteria 1 and 2 are unmet. Criterion 3 is descoped by owner
  decision, not met.

## Blockers and resolutions

1. **Docker: resolved 2026-10-12.** Docker is running after the Windows restart (Docker 29.8.2,
   Compose v5.5.1). All seven services report healthy. Fixes, committed in `b5be6ea`:
   - `docker-compose.yml`: removed the `depends_on` cycle between `redpanda-broker-1` and
     brokers 2 and 3.
   - `docker-compose.yml`: Redpanda image path changed from `redpanda/redpanda` to
     `redpandadata/redpanda`. Console tag changed from the nonexistent `v0.20.1` to `v2.5.2`.
   - `docker-compose.yml`: broker flags rewritten as `--flag=value`. The `--default-topic-*`
     flags were removed because v24.1.1 rejects them on the node CLI. Brokers now use
     Redpanda's default topic replication (1), not 3. Revisit before any run that depends on
     replication.
   - `docker-compose.yml`: Schema Registry sets `KAFKASTORE_TOPIC_REPLICATION_FACTOR=3`.
   - `docker-compose.yml`: external Kafka listeners moved to the published host ports
     19092/19093/19094. Host clients could not resolve the advertised internal names.
     `KAFKA_BROKERS` in `.env` and `.env.example` now points at `localhost:19092,19093,19094`.
   - `init-redis.conf`: removed the invalid `role master` line and renamed `lazy-freeing-*`
     to `lazyfree-*`.
   - All seven images are pinned to digests (tag kept for readability). `timescaledb:latest-pg15`
     was the one unpinned tag.
   - `verify-docker-compose.py` passed before these fixes, so it does not catch broker cycles,
     image path errors or listener mismatches. Do not rely on it as a runtime check.
2. **alerts.in.ua token: descoped to future work.** The token is not available yet. See
   "Scope change". The 401 `Invalid API token.` response is what the API returns for the
   placeholder. It does not mean the key was revoked.

## Decision

Owner decision (2026-10-12): accept the Gate 3 results for criteria 1 and 2 as final. The
misses are documented, not fixed. The MVP closes with these misses on record:

- Criterion 1: weekly WAPE 0.0852 for the baseline; no candidate beat it.
- Criterion 2: ARIMA 94.2% / 100%, NB 88.5% / 94.2% against the 77–83% / 93–97% bands.
- Criterion 3: descoped to future work (see "Scope change").

Gate 4 is therefore closed with documented misses. The thresholds were not changed. Gate 5
(ship the MVP or expand to the enterprise scope) was decided by the owner on 2026-10-12: ship the MVP,
with the misses above recorded. The enterprise track was closed in `docs/enterprise/STATUS.md`.
