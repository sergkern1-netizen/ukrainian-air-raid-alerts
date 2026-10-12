# Ukrainian air-alert records: an open, checked analysis

This project looks at the public record of air-raid alerts in Ukraine, from February 2022 to
October 2026. It asks what the record can show, how far it can be trusted, and what it cannot show.

It is not a warning system, a forecast you can act on, or a live feed. Nothing here says where an
attack will happen or what anyone should do. For warnings and shelter guidance, use the official
channels of the Air Force of the Armed Forces of Ukraine and the civil-protection authorities.

## Start here

1. **Navigation:** [`docs/NAVIGATION.md`](docs/NAVIGATION.md) explains how the repository is laid out
   and which files are current.
2. **Chapters:** [`docs/chapters/README.md`](docs/chapters/README.md) lists the ten chapters. Each
   answers one question and lists what it cannot tell you. Start with chapter 1.
3. **Limits:** [`docs/SAFETY.md`](docs/SAFETY.md) lists what this project will never claim, and
   [`docs/GLOSSARY.md`](docs/GLOSSARY.md) defines the terms used.

## Two things to know before you read the numbers

- **Counts are not danger.** The record counts alerts that were logged. It has no launch times,
  no impact times and no threat types, so it cannot show how much warning anyone had.
- **Agreement is not accuracy.** The volunteer record and the official record can be compared, but
  neither is a verified, complete account of what happened.

## Status in one line

The project shipped its baseline (a four-week average, which no model beat) with documented misses,
and the enterprise track is closed. See [`docs/gate4_status.md`](docs/gate4_status.md) and
[`docs/enterprise/STATUS.md`](docs/enterprise/STATUS.md).

---

## Project status

**Current result:** the trailing four-week mean is the deliverable. No more complex model beat
it in a 52-origin backtest, or in shorter sensitivity windows. The decision and its limits are in
[`docs/gate3_results.md`](docs/gate3_results.md).

**Status:** MVP shipped 2026-10-12 with documented misses. Weekly WAPE and interval coverage
missed their criteria, and real-time monitoring was descoped. See
[`docs/gate4_status.md`](docs/gate4_status.md).

Enterprise sources: the track is closed for now. See [`docs/enterprise/STATUS.md`](docs/enterprise/STATUS.md).
Parked and planned items are in [`docs/FUTURE_PLANS.md`](docs/FUTURE_PLANS.md).

## What it does

`python run_pipeline.py` runs these stages, each logged with a UTC timestamp:

1. **Acquire.** Downloads the two Vadimkin CSV files into `data/raw/` (git-ignored) and records
   their SHA-256 and download time in `data/raw/MANIFEST.json`.
2. **Validate and preprocess.** Checks required columns and non-empty files. Drops rows that are
   identical in every column (the official file has 38% such copies; see
   [`docs/data_inspection_gate1.md`](docs/data_inspection_gate1.md)).
3. **Weekly target.** Counts volunteer-feed alerts per Monday-start week. Partial first and last
   weeks are dropped.
4. **Checks (fail fast).** Stops if a complete week has zero alerts (possible collection stall),
   if there are too few weeks, or if the newest record is more than 14 days older than the
   `--as-of` date.
5. **Backtest.** 52 one-week-ahead origins. Each origin refits only on earlier weeks. Compares the
   baseline with a negative-binomial regression and ARIMA(1,1,0) on log-scale weekly totals.
6. **Forecast.** The baseline's point forecast for the next week. Its intervals are quantiles of
   in-sample backtest residuals. Their coverage was never checked against the approved bands, so
   they are optimistic (see limits below).
7. **Report.** Writes `output/forecast_results.csv` and `output/pipeline_report.json`.

## Data sources

| Source | Used for | Coverage | Notes |
|---|---|---|---|
| [Vadimkin/ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) `volunteer_data_en.csv` | Target series | 2022-02-25 onward, oblast level | Manually posted by volunteers; 5% of end times are inferred (`naive`). The repository's root licence is MIT; the licence of the data files is not confirmed. Credit: eTryvoga volunteer channel. |
| Same repository, `official_data_en.csv` | Cross-check | 2022-03-15 to 2026-09-07 | Ends with the official Telegram feed. Gradually changed from mostly region-level to district-level records during 2025 (see Chapter 6). |

Not used: the Kaggle missile-attack dataset (parked: Telegram-derived; see `docs/FUTURE_PLANS.md`),
the Kaggle p0stscriptum air-raid dataset, alerts.in.ua and UkraineAlarm (no credentials
available), ISW (terms do not permit dataset use), Oryx (no reuse rights found), ACLED (no API access
on the project account), GDELT (no timing alignment with alerts). Other GitHub projects on this data
are not independent sources.

## Results (52 origins, weekly WAPE)

| Model | Weekly WAPE | vs baseline (Diebold–Mariano) |
|---|---|---|
| **Trailing 4-week mean (deliverable)** | **8.52%** | — |
| Negative binomial (lags, 4-week mean, regime) | 12.40% | worse, p = 0.027 |
| ARIMA(1,1,0) on log1p | 8.55% | no difference, p = 0.97 |

Shorter windows (26 and 13 origins) give the same ranking. See `docs/gate3_results.md`.

## Install

Requires Python 3.11 (tested on Windows).

```bash
python -m venv venv
venv\Scripts\activate            # Windows; on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: tests and lint
```

`requirements-gazetteer.txt` is only needed to regenerate the Telegram keyword lists
(`scripts/build_telegram_forms.py`). It is not used at runtime.

## Run

```bash
python run_pipeline.py                      # download if needed, then run
python run_pipeline.py --offline            # use files already in data/raw/
python run_pipeline.py --as-of 2026-10-12   # fix the freshness reference date (reproducible runs)
python run_pipeline.py --origins 26         # shorter backtest window
```

Exit code is 0 on success and 1 if a check fails. Outputs go to `output/` (git-ignored).

## Tests

```bash
pytest                          # offline suite; live tests are skipped
RUN_LOAD_TESTS=1 pytest         # also runs live tests (needs the Docker stack and .env)
```

## Repository layout

```
run_pipeline.py              entry point: acquire -> validate -> weekly -> backtest -> forecast
src/forecasting/             weekly target, backtest, metrics
src/ingestion/vadimkin.py    download, manifest, schema checks, loading
src/ingestion/alert_dedupe.py exact-duplicate ingest rule
src/ingestion/              real-time and batch components (see below)
src/schemas/                Avro schemas
scripts/                     inspection, EDA, backtest CLI, gazetteer generator
docs/                        decisions, data inspection, EDA, Gate 3 results
tests/                       offline unit and pipeline tests
```

### Components not wired into the pipeline

`src/ingestion/` also contains a real-time alerts poller, a Telegram consumer, a weather
loader, batch loaders for other sources, a Redis-backed cache with in-memory fallback, and
Confluent wire-format publishing. They are tested in isolation. `run_pipeline.py` does not call
them. The Docker stack (`docker compose up -d`) runs all seven services, and the live Redis and
Kafka tests pass against it (2026-10-12). The Telegram path has not been run end to end. The
real-time alerts poller needs an alerts.in.ua API token and is future work.

## Limitations

Full list: [`docs/gate3_results.md`](docs/gate3_results.md). The main ones:

- **Alert types are not in the data.** Yellow alerts, red alerts and drone threats cannot be
  separated from these files, so the series counts whatever the dataset records.
- **One volunteer channel, no ground truth.** Coverage depends on volunteer staffing. The feed
  reports more alerts than the official feed in some western oblasts, and this is documented,
  not corrected.
- **Intervals are empirical and optimistic.** The baseline's intervals come from residual
  quantiles of the same backtest, so their coverage is not an out-of-sample check.
- **Weekly granularity only.** The weekly forecast does not support daily alerting.
- **Short post-break window.** About 40 weeks since the December 2025 change in the official
  feed. Little data to judge regime-specific behaviour.

## Decisions and provenance

- [`docs/gate2_decisions.md`](docs/gate2_decisions.md): deliberation, rulings, and the approval of
  the success metrics
- [`docs/gate3_day1_findings.md`](docs/gate3_day1_findings.md): volunteer-feed checks
- [`docs/gate3_results.md`](docs/gate3_results.md): backtest results, validation and limitations
- [`docs/eda_gate2.md`](docs/eda_gate2.md): exploratory analysis of the daily counts

## Success criteria (approved)

Replaces the RMSE < 5 target in CLAUDE.md, approved by the project owner.

- [x] Weekly WAPE is the primary metric (criterion 1, beating the baseline, is not met; see Gate 4)
- [x] Daily WAPE is reported as a secondary metric
- [ ] 80% and 95% interval coverage within the bands (80%: 77–83%, 95%: 93–97%). The baseline
      has no model-based intervals and was not checked against this band; no candidate met it.
- [x] `python run_pipeline.py` runs from the repository root on the stated data
- [x] Requirements pinned to the versions the tests were run against
- [ ] Real-time monitoring latency below 5 minutes: descoped from the MVP by the project owner
      (2026-10-12). Not measured. It needs the alerts.in.ua API token, which is not yet available.

## Disclaimer

This is an analysis of published, historical alert records. It is not an operational warning
system and must not be used for safety decisions.
