# Ukrainian Air Raid Alerts: Weekly Forecast Pipeline

A reproducible pipeline that downloads public siren-alert records, checks them, and produces a
one-week-ahead forecast of national alert counts, with a backtest against the baseline.

## Map of this repository

### Start here

**What this project is.** An open analysis of published, historical records of air-raid alerts in
Ukraine. It describes when and where alerts were recorded, how far two public records agree, and
how well simple methods forecast weekly alert counts.

**What it is not.** It is not a warning system, not an official source, and not live. It does not
say what caused an alert, what was hit, or how much warning anyone had. For safety instructions
and live warnings, use the official channels: the Air Force of the Armed Forces of Ukraine, the
State Emergency Service, and your local authorities.

**Where to read safely.**

| If you want to... | Read |
|---|---|
| Know what this project will not publish, and why | [Safety boundaries](docs/SAFETY.md) |
| Understand the words used (alert, wave, match, WAPE) | [Glossary](docs/GLOSSARY.md) |
| Read the findings in plain language | [The chapters](docs/chapters/README.md) |
| Find your way around every folder and file | [Navigation guide](docs/NAVIGATION.md) |
| See the main open problems and limits | [Project summary](docs/PROJECT_SUMMARY.md) |

### The chapters

Each chapter answers one question, lists what it cannot tell you, and can be rerun from its
script. The full list, including planned chapters, is in [docs/chapters/README.md](docs/chapters/README.md).

| # | Chapter | What it covers |
|---|---|---|
| 1 | [Timing and rhythms](docs/chapters/01-timing-and-rhythms.md) | How long alerts last, when they start, and what that means for nights and routines |
| 2 | [Where sirens sound](docs/chapters/02-regional-spread.md) | Which oblasts have the most recorded alerts, how long they last there, and how this changed |
| 3 | [Waves and clusters](docs/chapters/03-waves-and-clusters.md) | How alerts group into waves, how long waves last, and how many oblasts they touch |
| 4 | [Feed reliability](docs/chapters/04-feed-reliability.md) | How well the volunteer and official records agree, by oblast and over time |
| 5 | [Long alerts](docs/chapters/05-long-alerts.md) | The longest records, where they are, and whether they look real or like recording errors |
| 6 | [Granularity and the official feed](docs/chapters/06-granularity-and-official-feed.md) | How the official record changed from regions to districts, and what that does to comparisons |
| 7 | [Data provenance and quality](docs/chapters/07-provenance-and-quality.md) | What is in each file, how duplicates were handled, and what is missing |
| 8 | [Reporting patterns](docs/chapters/08-reporting-patterns.md) | Where the two records agree and disagree, by group of oblasts and year, and what is not known about why |

### Gate and status documents

The project moved through decision points ("gates"). These record what was decided and why.

| Document | What it records |
|---|---|
| [Gate 3 results](docs/gate3_results.md) | The forecast backtest, the chosen baseline, and the known limits |
| [Gate 4 status](docs/gate4_status.md) | Which success criteria were met, missed or descoped |
| [Enterprise status](docs/enterprise/STATUS.md) | Why the extra data sources were dismissed or blocked |

### Methods and provenance

| Document or folder | What it covers |
|---|---|
| [Gate 1 data inspection](docs/data_inspection_gate1.md) | First look at the two source files: columns, duplicates, inferred end times |
| [Gate 2 decisions](docs/gate2_decisions.md) and [Gate 2 EDA](docs/eda_gate2.md) | Exploratory analysis and the rulings on metrics and models |
| [Per-oblast EDA](docs/eda_per_oblast.md) and [Gate 3 day 1 findings](docs/gate3_day1_findings.md) | Weekly counts by oblast; checks on the volunteer record |
| [Alert waves](docs/analysis/alert_waves.md) | How waves change with the gap used to define them |
| [Wave anatomy](docs/analysis/wave_anatomy.md) | Which oblasts take part in waves, and which alert together |
| [Feed integrity](docs/analysis/feed_integrity.md) | Agreement between the volunteer and official records |
| [Western cluster check](docs/analysis/western_cluster_check.md) | Whether the western cluster also appears in the official record |
| [Kirovohrad–Poltava gap](docs/analysis/kirovohrad_poltava_gap.md) | Why two oblasts are often recorded at the same minute |
| [Alert-record profiles](docs/analysis/defensive_profiles.md) | Duration, night share, lag and long alerts by oblast |
| [News sources research](docs/analysis/news_sources_research.md) and [terms review](docs/sources/news_sources_review.md) | Why news data was tested and dropped |

Scripts in [`scripts/`](scripts/), by purpose:

| Purpose | Scripts |
|---|---|
| Download and first inspection | `inspect_vadimkin.py` |
| Exploratory analysis | `eda_daily.py`, `eda_per_oblast.py` |
| Forecast backtest | `gate3_backtest.py` |
| Chapters (one per chapter) | `chapter01_timing.py` to `chapter08_reporting.py` |
| Supporting analyses | `alert_waves.py`, `wave_anatomy.py`, `feed_integrity.py`, `western_cluster_check.py`, `pair_gap_investigation.py`, `defensive_profiles.py` |
| Developer tool (not analysis) | `build_telegram_forms.py` |

### Safety and glossary

- [Safety boundaries](docs/SAFETY.md): what the project will not publish, and the rules every
  public number must follow.
- [Glossary](docs/GLOSSARY.md): plain definitions of the terms used across the repository.

### Future plans

- [Future plans and parked items](docs/FUTURE_PLANS.md): paused, blocked and planned work, with
  what would unblock each item.
- [Master plan](docs/MASTER_PLAN.md): the phased roadmap (a draft for owner approval).

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
