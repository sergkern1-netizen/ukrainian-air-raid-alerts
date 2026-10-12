# Chapter 10: Method and reproducibility

*How to rerun every number in this project, what each step reads and writes, and what a rerun does and does not prove.*

Checked on 2026-10-12 on Windows, Python 3.11.9, from the repository root.

---

## The short version

- The analysis reads **two files**: the official and the volunteer alert records, both from one public GitHub dataset. A small manifest file records their size and a checksum, so you can confirm you have the same files.
- Each chapter has **one script**. The script writes its figures and its numbers. The chapter text is written by hand from those numbers; no script writes the chapter text.
- In the audit, **all 16 runs exited cleanly** (the nine chapter scripts, six supporting analyses and the offline pipeline), each taking about 4.5 to 12 seconds. The test suite gave **106 passed, 3 skipped**.
- **One warning:** four supporting scripts write documents into `docs/analysis/`. Rerunning them replaces those documents. Check the diff before you commit (section 6).

---

## 1. The data

The project uses two CSV files from the public Vadimkin siren dataset on GitHub (MIT licence):

| File | What it is |
|---|---|
| `official_data_en.csv` | The official-feed alert record. It ends on 2026-09-07. |
| `volunteer_data_en.csv` | The volunteer alert record. It is the main series and has no ground truth. |

They live in `data/raw/`, next to `MANIFEST.json`. For each file the manifest lists the source address, the size in bytes, the **SHA-256 checksum** (a fingerprint of the file's exact contents) and the download time (2026-10-12, 00:58 UTC). Neither the data nor the `output/` folder is stored in git; both are ignored on purpose. You get them by downloading and running.

**How to check your copy** (from the repository root; Windows PowerShell):

```powershell
Get-FileHash data\raw\official_data_en.csv -Algorithm SHA256
Get-FileHash data\raw\volunteer_data_en.csv -Algorithm SHA256
```

Compare each result, ignoring upper or lower case, with the manifest. The audit found both matched:

- `official_data_en.csv`: `b396f876...1ed20ec4`
- `volunteer_data_en.csv`: `d03747ee...7377465`

The source repository keeps being updated. A file downloaded later will be longer, will have a different checksum, and will give different numbers. The chapters describe the files fixed by this manifest, not whatever is online today.

## 2. Order of work

The scripts do not depend on each other, so the order is for reading, not for running. Every script loads both files from `data/raw/`; the Uses column says which file's rows it analyses. Figures go to `docs/chapters/figures/`. Numbers go to `output/analysis/`.

| Script | What it answers | Uses | Writes | Chapter |
|---|---|---|---|---|
| `chapter01_timing` | When alerts start, how long they last, night and day rhythm | volunteer | `ch01_*.png`; `chapter01_numbers.json` | 1 |
| `chapter02_regions` | How alerts spread across oblasts | volunteer | `ch02_*.png`; region table, numbers | 2 |
| `chapter03_waves` | How alerts group into waves | volunteer | `ch03_*.png`; waves table, numbers | 3 |
| `chapter04_reliability` | How well the two records agree | both | `ch04_*.png`; numbers, by-oblast table | 4 |
| `chapter05_long_alerts` | Whether the longest alerts look real | both | `ch05_*.png`; long-alerts table, numbers | 5 |
| `chapter06_granularity` | What the December 2025 change does to counts | both | two `ch06_*.png`; monthly levels, numbers | 6 |
| `chapter07_provenance` | What is in each file, and what is missing | both, plus `MANIFEST.json` | `ch07_coverage_by_year.png`; numbers | 7 |
| `chapter08_reporting` | Reporting patterns in the west and one oblast pair | both | three `ch08_*.png`; numbers and three tables | 8 |
| `chapter09_disruption` | Daily and weekly national alert-time coverage | volunteer | two `ch09_*.png`; numbers, daily table | 9 |
| `alert_waves` | Waves at several gap sizes | volunteer | `output/analysis/alert_waves.md` and wave tables | supports 3 |
| `feed_integrity` | Agreement over time and place | both | `output/analysis/feed_integrity.md` and tables | supports 4 |
| `wave_anatomy` | Which oblasts take part in each wave | volunteer | `docs/analysis/wave_anatomy.md`; participation table | supports 3 |
| `western_cluster_check` | Whether the western cluster shows in the official feed | both | `docs/analysis/western_cluster_check.md` | supports 8 |
| `pair_gap_investigation` | Why two oblasts alert together more in one feed | both | `docs/analysis/kirovohrad_poltava_gap.md` | supports 8 |
| `defensive_profiles` | Alert-record profiles for review | both | `docs/analysis/defensive_profiles.md`; long-alerts table | supports 5 (the long-alert register); also draws on 1, 4 and 6 |
| `run_pipeline.py` | A weekly baseline forecast, which is not an operational warning | both | `output/forecast_results.csv`, `output/pipeline_report.json` | none (see README) |

"Uses" names the file whose rows are analysed. Every script loads both files.

Five more scripts exist and were deliberately **not run** in the audit: `eda_daily`, `eda_per_oblast`, `gate3_backtest` (earlier forecast work, recorded in the gate documents), `inspect_vadimkin` (it downloads the data) and `build_telegram_forms` (it rewrites a tracked file). All 20 scripts are tracked in git.

## 3. How to rerun everything

Set up once (README has the full text):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Then, from the repository root, run each script **as a module** (`python -m scripts.NAME`). Do not add `-I`. Isolated mode removes the current directory from the import path, so the package cannot be found. The full list is in the appendix.

To get the data in the first place, run `python run_pipeline.py` (it downloads if the files are missing), or `python -m scripts.inspect_vadimkin`. Both need a network and write `data/raw/`.

## 4. Checks and tests

- **Tests.** `python -m pytest -q` gave 106 passed, 3 skipped, in about 5 seconds. The three skipped tests are the live tests (section 5). The run also printed 39 warnings, which were not investigated.
- **Pins.** All 17 pinned packages in `requirements.txt` and `requirements-dev.txt` matched the installed versions.
- **Checksums.** Section 1.
- **Idempotence.** After the runs, figures, chapter text and output tables matched the pre-run copies byte for byte. Before the generators were fixed, two tracked documents (`docs/analysis/alert_waves.md` and `docs/analysis/feed_integrity.md`) were overwritten. They now write to `output/analysis/`, so rerunning cannot change the tracked copies. After the fix the only change in a rerun is the run time in `output/pipeline_report.json`.
- **Script checks.** Each chapter script prints its counts as it runs and writes them to its numbers file. The chapters give row counts, date ranges and small-sample flags (fewer than 50 alerts) from those files. The pipeline returns a non-zero exit code on failure; its freshness check passed with `--as-of 2026-10-12`.

## 5. What is not reproducible here

- **Live tests.** Three tests need the Docker stack and a token, and run only with `RUN_LOAD_TESTS=1`. They were not run. The real-time parts are therefore untested against a live source (see `docs/SAFETY.md`).
- **The download step.** It needs network access, and the source files change over time (section 1).
- **The parked dataset.** One further dataset sits in `data/raw/` but no script reads it, and it is out of scope. Nothing in this project uses it.
- **The unrun scripts** listed in section 2.

## 6. Known caveats in the method

- **Some generators replace documents.** `wave_anatomy`, `western_cluster_check`, `pair_gap_investigation` and `defensive_profiles` write into `docs/analysis/`. Rerunning one **replaces that document**, including any hand edits. Run `git diff` and review it before committing. Before the generators were fixed, `alert_waves` and `feed_integrity` overwrote two tracked documents (`docs/analysis/alert_waves.md` and `docs/analysis/feed_integrity.md`). They now write to `output/analysis/`, so rerunning cannot change the tracked copies.
- **Time zones.** Local days and hours (Chapters 1, 9 and the like) use **Kyiv time**. The year tables use **UTC years**, so an alert near New Year can fall in a different year than a Kyiv reader expects. Chapters say which they use.
- **Matching rule.** A volunteer alert matches an official alert if one starts in the **same oblast** within **five minutes**. A match shows both feeds recorded something at about that time, not that the alert was correct.
- **Pipeline output drifts harmlessly.** `pipeline_report.json` records the run time, so it differs on each run.
- **Comparisons across the December 2025 change** in the official feed need care (Chapter 6).

## What this chapter cannot tell you

- A rerun reproduces the **numbers**. It does not show that the records are **true**. The volunteer record has no ground truth, and agreement between the two records is not accuracy.
- Matching checksums prove you have the same files, not that those files are complete.
- Passing tests show the code behaves as tested. They say nothing about whether any alert was correct, and they do not show that any forecast is usable as a warning. Nothing here is a warning or a real-time claim.
- The audit ran on one machine on one day. I did not test macOS or Linux, other Python versions, or a fresh download.
- The 39 test warnings and the 3 skips were not investigated.

---

## Method (technical appendix)

Environment: Python 3.11.9, Windows, virtual environment in `venv`. Packages pinned in `requirements.txt` (pandas 2.1.3, numpy 1.24.3, scipy 1.15.3, statsmodels 0.14.0 and others) and `requirements-dev.txt` (pytest 9.1.1, matplotlib 3.8.2 and others).

Chapter scripts (figures to `docs/chapters/figures/`; numbers to `output/analysis/`):

```powershell
python -m scripts.chapter01_timing
python -m scripts.chapter02_regions
python -m scripts.chapter03_waves
python -m scripts.chapter04_reliability
python -m scripts.chapter05_long_alerts
python -m scripts.chapter06_granularity
python -m scripts.chapter07_provenance
python -m scripts.chapter08_reporting
python -m scripts.chapter09_disruption
```

Supporting analyses. The last four overwrite files in `docs/analysis/`:

```powershell
python -m scripts.alert_waves
python -m scripts.feed_integrity
python -m scripts.wave_anatomy
python -m scripts.western_cluster_check
python -m scripts.pair_gap_investigation
python -m scripts.defensive_profiles
```

Pipeline and tests:

```powershell
python run_pipeline.py --offline --as-of 2026-10-12
python -m pytest -q
$env:RUN_LOAD_TESTS = "1"; python -m pytest -q   # live tests: needs Docker stack and .env token
```

`--offline` uses only `data/raw/`. `--as-of` fixes the freshness reference date so runs are repeatable. Exit code 0 is success; a non-zero exit code means a failure.

Verification used for this chapter: exit codes and wall times of the 16 runs (4.5 to 12.0 seconds each), `pip freeze` against the pins, SHA-256 against `MANIFEST.json`, `git check-ignore` for `data/raw/` and `output/`, `git ls-files` for `scripts/`, and a byte comparison of outputs before and after.
