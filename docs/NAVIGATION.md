# Navigation guide

How this repository is organised, which files are current, which are kept only for the record,
and what to read first depending on who you are.

Checked against the repository on 2026-10-12. Nothing has been moved or deleted. Suggested moves
are listed at the end for the owner to decide.

---

## How the repository is organised

| Place | What is in it | In git? |
|---|---|---|
| Root folder | The main page (`README.md`), the entry point (`run_pipeline.py`), requirements, Docker and test settings, and many planning files from the first sessions | Yes |
| `docs/chapters/` | The plain-language chapters, their figures, and the chapter list | Yes |
| `docs/analysis/` | Supporting analyses that the chapters build on | Yes |
| `docs/` (top level) | Gate records, safety rules, glossary, plans, and this guide | Yes |
| `docs/enterprise/` | Checks on extra data sources, all closed or blocked | Yes |
| `docs/sources/` | Terms review for news sources | Yes |
| `docs/superpowers/plans/` | One working plan for a data source that was later dismissed (ISW) | Yes |
| `scripts/` | One script per chapter or analysis; each reproduces its numbers and figures | Yes |
| `src/` | The forecast code, the data loader, and real-time parts that are built and tested but not used by the pipeline | Yes |
| `tests/` | Automated tests | Yes |
| `data/` | Downloaded source files (`data/raw/`) | No (ignored) |
| `output/` | Results written by the pipeline and the scripts | No (ignored) |
| `notebooks/` | Empty | No |

Because `data/` and `output/` are not in git, you get them by running the pipeline or a script.
Every number in the chapters points to the script that produces it.

---

## Which files are current

These are the files to trust for the present state of the project:

- `README.md`: the main page and map.
- `docs/chapters/`: the findings, written for a general reader.
- `docs/SAFETY.md` and `docs/GLOSSARY.md`: the rules and the words.
- `docs/gate3_results.md` and `docs/gate4_status.md`: the forecast result and the success criteria.
- `docs/enterprise/STATUS.md`: why other data sources are not used.
- `docs/FUTURE_PLANS.md` and `docs/MASTER_PLAN.md`: what comes next (the master plan is a draft).
- `docs/PROJECT_SUMMARY.md`: the main open problems.
- `docs/analysis/`, `docs/data_inspection_gate1.md`, `docs/eda_gate2.md`, `docs/eda_per_oblast.md`,
  `docs/gate2_decisions.md`, `docs/gate3_day1_findings.md`: methods and earlier decisions. Some
  figures in them were later corrected; the correction is written in the file or in the chapter
  that replaced it.

---

## Root-level files, one by one

Each file is marked **current**, **historical (kept for the record)**, or **internal log**.
Historical files describe plans or research from 11–12 October 2026 that were later replaced.
Their numbers and claims are not the project's current position. Internal logs are records of
working sessions.

### Planning and research files

| File | Mark | Reason |
|---|---|---|
| `README.md` | current | The main page. |
| `CLAUDE.md` | current | Working instructions for AI assistants; its success criteria are updated, but its header ("Research Complete — Ready for Implementation") and source notes are from 11 October. |
| `AI_INTERACTION_LOG.txt` | internal log | Running record of requests and decisions across sessions; still being added to. |
| `AIR_ALERTS_IMPLEMENTATION_PLAN.md` | historical (kept for the record) | Architecture plan for a "prediction system"; replaced by the weekly baseline and `docs/MASTER_PLAN.md`. |
| `ARBITRATION_SUMMARY.md` | historical (kept for the record) | Rulings from a research-phase debate between AI agents before any data was downloaded. |
| `COMPLETE_SOURCE_INVENTORY.md` | historical (kept for the record) | List of sources consulted during research; current source decisions are in `docs/enterprise/STATUS.md` and `docs/FUTURE_PLANS.md`. |
| `COMPRESSION_READY.md` | internal log | Status note written before a session's context was compressed. |
| `CONVERSATION_SUMMARY.md` | internal log | Summary of the first research conversation. |
| `IMPLEMENTATION_CHECKLIST.md` | historical (kept for the record) | Pre-implementation checklist built on the v2.0 research document; its blockers were resolved or dropped. |
| `MILESTONE_1_WORK_ORDERS.md` | historical (kept for the record) | Work orders for the real-time infrastructure milestone, which is not part of the pipeline. |
| `ORCHESTRATOR_REVIEW_LOG.md` | internal log | Review log of those work orders. |
| `RESEARCH_FINDINGS_MASTER.md` | historical (kept for the record) | Research-phase audit; lists sources (Kaggle, alerts.in.ua) that are not used now. |
| `RESEARCH_METHODOLOGY_AND_PROVENANCE_AUDIT.md` | historical (kept for the record) | How the research phase was run; useful for provenance, not for current findings. |
| `SESSION_COMPLETION_SUMMARY.md` | internal log | End-of-session summary from 11–12 October. |
| `SESSION_CONTINUATION_LOG.md` | internal log | Session log for the infrastructure milestone. |
| `STRESS_TEST_CONSOLIDATED_FINDINGS.md` | historical (kept for the record) | Research-phase stress test with viability and cost estimates made before any data was checked. |
| `UKRAINIAN_AIR_RAID_ALERTS_RESEARCH_v2.0.md` | historical (kept for the record) | Research brief marked "Authoritative" in its header, but replaced by the gate records and chapters. |
| `air_raid_prediction_architecture.html` | historical (kept for the record) | Architecture diagram for the replaced prediction-system plan. |
| `DATA_SOURCES_REFERENCE.json` | historical (kept for the record) | Research-phase source metadata. Not in git: `.gitignore` ignores all `*.json`, so readers of the public repository cannot see it, although `CLAUDE.md` lists it. |

### Code, configuration and setup files

| File | Mark | Reason |
|---|---|---|
| `run_pipeline.py` | current | The single entry point for the forecast pipeline. |
| `requirements.txt` | current | Pinned packages for the pipeline and `src/`. |
| `requirements-dev.txt` | current | Test, lint and chart packages. |
| `requirements-gazetteer.txt` | current | Only for regenerating the Telegram word lists; not used at runtime. |
| `pytest.ini` | current | Test settings. |
| `.env.example` | current | Template for local settings; holds no real keys. |
| `.gitignore` | current | Keeps data, outputs and local settings out of git. |
| `docker-compose.yml` | current | The seven-service stack for the real-time parts (not used by the pipeline). |
| `init-redis.conf` | current | Redis settings for that stack. |
| `init-timescale.sql` | current | Database set-up for that stack. |
| `verify-docker-compose.py` | current | Static check of the Docker file; `docs/gate4_status.md` warns it does not catch runtime faults. |

---

## What to read, in order

### If you live in Ukraine and want to understand the alerts

1. [Safety boundaries](SAFETY.md): what this project cannot tell you. For warnings, use official
   channels only.
2. [Glossary](GLOSSARY.md): the words used.
3. [Chapter 1](chapters/01-timing-and-rhythms.md): how long alerts last and when they happen.
4. [Chapter 2](chapters/02-regional-spread.md): your oblast compared with others.
5. [Chapter 4](chapters/04-feed-reliability.md): how far the record can be trusted.

### If you are a journalist

1. [Safety boundaries](SAFETY.md): what may not be claimed (no warning times, no threat types, no
   "most attacked" framing).
2. [Glossary](GLOSSARY.md).
3. [Chapter 4](chapters/04-feed-reliability.md) and [Chapter 7](chapters/07-provenance-and-quality.md):
   where the data comes from and its limits.
4. [Chapters 1 to 3](chapters/README.md): the main patterns.
5. [Project summary](PROJECT_SUMMARY.md): the open problems, before you quote a number.

### If you are an analyst

1. [Chapter 7](chapters/07-provenance-and-quality.md) and [Gate 1 data inspection](data_inspection_gate1.md):
   the two source files.
2. [Chapter 6](chapters/06-granularity-and-official-feed.md): the December 2025 change in the
   official record. Read it before comparing any counts across that date.
3. [Chapter 4](chapters/04-feed-reliability.md) and [feed integrity](analysis/feed_integrity.md).
4. [Gate 2 decisions](gate2_decisions.md), then [Gate 3 results](gate3_results.md): how the
   forecast was chosen and tested.
5. The other files in [`analysis/`](analysis/), and the scripts in `scripts/` that produce them.
6. [Project summary](PROJECT_SUMMARY.md).

### If you are a developer

1. [`README.md`](../README.md): install, run, tests and layout.
2. `run_pipeline.py`, then `src/forecasting/` and `src/ingestion/vadimkin.py`.
3. [Gate 4 status](gate4_status.md): what was tested, the Docker fixes, and the descoped
   real-time path.
4. `tests/`: run `pytest` (live tests are skipped unless `RUN_LOAD_TESTS=1`).
5. [Future plans](FUTURE_PLANS.md): what is blocked and what would unblock it.
6. Historical files only if you need the reasoning behind the real-time parts in `src/ingestion/`:
   `MILESTONE_1_WORK_ORDERS.md`, then `AIR_ALERTS_IMPLEMENTATION_PLAN.md`.

---

## Suggested moves (for the owner to decide; nothing has been moved)

1. Move the eleven historical files and the six internal logs from the root into
   `docs/archive/research/` and `docs/archive/logs/`, keeping the names. The root would then
   hold only the README, `CLAUDE.md`, the entry point, and set-up files.
2. Add a one-line note at the top of each historical file: "Historical. Not the project's
   current position. See README.md."
3. Decide whether `AI_INTERACTION_LOG.txt` should stay public. It is pushed to GitHub and names
   the owner's personal email address.
4. Decide what to do with `DATA_SOURCES_REFERENCE.json`: add it to git with an exception in
   `.gitignore`, or remove the references to it in `CLAUDE.md`.
5. Move `docs/gate*.md`, `docs/eda_*.md` and `docs/data_inspection_gate1.md` into `docs/gates/`.
   Links in the README, the chapters and the gate files would need updating in the same commit.
6. Move `docs/superpowers/plans/` into the archive; it is a plan for a source that was dismissed.
