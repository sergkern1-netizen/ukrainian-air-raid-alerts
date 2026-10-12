# Gate 4 status: MVP complete?

Checked: 2026-10-12. Criteria: CLAUDE.md, "MVP Success Criteria" and "Gate 4: MVP Complete".
Outcome: **not complete.** Three of six criteria are met or partly met, one is not met, and
one cannot be checked until a live stack and a valid API token are available.

## Criteria

| # | Criterion (CLAUDE.md) | Status | Evidence |
|---|---|---|---|
| 1 | Weekly WAPE beats the trailing four-week mean baseline (8.52%) | **Not met** | No candidate beats the baseline. Baseline accepted as the deliverable under trigger T1. `docs/gate3_results.md` |
| 2 | 80%/95% interval coverage within 77–83% / 93–97% | **Not met** | ARIMA: 94.2% / 100%. NB: 88.5% / 94.2%. Neither model is inside both bands. NB 95% is inside its band. `docs/gate3_results.md` |
| 3 | Real-time monitoring latency < 5 minutes | **Not verified (deferred)** | Live stack runs (all services healthy, 2026-10-12). Real-time latency is not measured: no alerts.in.ua API token is set in `.env` (placeholder still in place); a token request is pending with an expected wait of about 7 working days. See "Blockers". |
| 4 | Code reproducible with `python run_pipeline.py` | **Met (offline path)** | `python run_pipeline.py --offline --as-of 2026-10-12` exits 0 and reproduces the Gate 3 numbers exactly (baseline weekly WAPE 0.0852, ARIMA 0.0855, NB 0.1240). The download path (`acquire` without `--offline`) was not re-run in this check. |
| 5 | README, requirements.txt and run_pipeline.py complete | **Met** | Committed in `8df0d05`. Runtime pins match the tested venv. `requirements-dev.txt` covers tooling. |
| 6 | All external sources timestamped before the forecast point | **Partly met** | `output/pipeline_report.json` records the first and last record times for both feeds. Volunteer last record 2026-10-11T04:36:59Z is before the 2026-10-12 as-of date. The forecast is for week 2026-10-05. No live-source timestamps exist yet, because the real-time path has not run. |

Test status (2026-10-12): `pytest` gives 106 passed, 3 skipped. The 3 skipped tests are the live
checks, gated by `RUN_LOAD_TESTS=1`. Run against the live stack on 2026-10-12:
- `test_redis_latency.py`: passed.
- `test_kafka_lag.py`: passed after the listener fix (see Blocker 1). It was failing before.
- `test_load_alerts_poller.py::test_sustained_rate_and_latency_live`: it previously passed
  without measuring anything, because it swallowed every exception and recorded 401 responses
  as latency samples. It now counts failed polls and fails on any error (commit pending). With
  the placeholder token it runs the full 10-minute window and then fails on the recorded 401s. It can only pass with a real
  token. A single live probe on 2026-10-12 returned `ClientResponseError` for the placeholder.

## Gate 4 checklist (CLAUDE.md)

- [x] Pipeline end-to-end working (offline path, verified this session)
- [x] README complete (commit `8df0d05`)
- [x] requirements.txt pinned
- [ ] All success criteria met (criteria 1, 2 and 3 are not met or not verified; see above)

## Blockers

1. **Docker: resolved 2026-10-12.** Docker is running after the Windows restart (Docker 29.8.2,
   Compose v5.5.1). The stack starts and all seven services report healthy. Fixes needed to get
   there, all in the working tree and not yet committed:
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
   All seven images are pinned to digests (tag kept for readability). `timescaledb:latest-pg15`
   was the one unpinned tag; it is now fixed at the digest pulled on 2026-10-12.
   `verify-docker-compose.py` passed before these fixes, so it does not catch broker cycles,
   image path errors or listener mismatches. Do not rely on it as a runtime check.
2. **alerts.in.ua token pending (deferred by decision).** `API_TOKEN` in `.env` is still the
   placeholder from `.env.example`. A real token has been requested, and the expected wait is about
   7 working days. The project owner has decided to omit this item from the current Gate 4 pass and
   to record it here. The CLAUDE.md blocker "obtain alerts.in.ua API token" remains open. Until a
   real token is in `.env`, the real-time poller cannot be measured against the source.
   (Earlier diagnosis: the HTTP 401 `Invalid API token.` response is what the API returns for the
   placeholder. It does not mean the key was revoked.)

## Decision

Gate 4 is not passed. Criteria 1 and 2 are unmet and were recorded as such in Gate 3. Criterion 3
has no measurement, and it is deferred until the alerts.in.ua token arrives (about 7 working days)
and Docker is installed. Gate 5 (ship or expand) should wait until criterion 3 is measured with a
valid token and a running stack.
