# Enterprise Source 1: ISW (Institute for the Study of War) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing ISW loader into a leakage-safe, timestamped daily source, and show whether it adds any signal to the weekly forecast. The MVP deliverable (trailing four-week mean, 8.52% weekly WAPE) changes only if a candidate beats it on the same backtest.

**Architecture:** `IswLoader` in `src/ingestion/batch_loaders.py` is the only code to change. It gets a publication-date parser that replaces the scrape-time stamp. Records carry an `available_at` time. The weekly feature join keeps only records with `available_at` on or before the forecast origin. A frozen HTML snapshot under `tests/fixtures/` makes the parser testable offline.

**Tech Stack:** Python 3.10+, pandas, requests, pytest. No new dependencies. Existing venv and `requirements.txt` pins.

---

> **STATUS: DISMISSED 2026-10-12.** ISW's Fair Use & Attribution Policy does not permit
> scraping, dataset incorporation or redistribution without written permission. The owner
> dismissed ISW. The next enterprise source is ACLED; see `docs/enterprise/acled_access.md`.

## Starting point (verified 2026-10-12)

- `src/ingestion/batch_loaders.py:500-640`: `IswLoader` exists. Its docstring says "mock implementation", which is stale: `load()` makes a real `requests.get`.
- **Defect 1, fabricated timestamps.** `_extract_threat_assessments` sets `event_date = datetime.utcnow()`. Every record is stamped with the scrape time, not the date the assessment was published. This violates CLAUDE.md non-negotiables 1 and 3.
- **Defect 2, heuristic labels.** Threat levels come from a regex over a 200-character window after a region name (`[^.]*?`). Nothing has been checked against the real page. The docstring calls the extractor "simplified".
- **Defect 3, no offline test data.** The tests in `tests/test_batch_loaders.py:273-330` use hand-written strings, not a real page.
- ACLED (`AcledLoader`) is the other candidate. It needs an API key, which is not in `.env`, so it is not the first source.

## Scope and non-goals

- In scope: ISW as an optional weekly feature, validated with the existing backtest.
- Not in scope: ISW as a target, Telegram, Oryx, ACLED, Kaggle missile data, Texty. Each is a later plan.
- Not in scope: a new model family. CLAUDE.md says to add no neural networks and to use models only after EDA supports them.
- Success for this plan means a correct, leakage-safe source plus an honest backtest result. It does not require ISW to beat the baseline.

## File Structure

- Modify: `src/ingestion/batch_loaders.py` (IswLoader only, lines ~500-640). Add `_extract_publication_date` and `available_at`. Replace the scrape-time stamp.
- Create: `tests/fixtures/isw_snapshot_YYYY-MM-DD.html` (one real page, saved once, with its SHA-256 recorded in `tests/fixtures/README.md`).
- Create: `docs/enterprise/isw_source_check.md` (licence, robots.txt, and ToS findings with access date).
- Modify: `tests/test_batch_loaders.py` (replace the ISW tests at lines 273-330 with snapshot-based tests).
- Create: `src/forecasting/isw_features.py` (one function: weekly ISW features joined on `available_at <= origin`).
- Create: `tests/test_isw_features.py` (leakage tests).
- Modify: `run_pipeline.py` only to report the ISW comparison, behind a flag. The MVP path stays unchanged.
- Modify: `docs/enterprise/isw_result.md` (created in Task 5) and `AI_INTERACTION_LOG.txt`.

---

### Task 0: Source gate (licence and access)

This is a blocker check, like the CLAUDE.md blockers. Do it before writing code.

**Files:**
- Create: `docs/enterprise/isw_source_check.md`

- [ ] **Step 1: Read ISW's terms and robots file**

Run (PowerShell or Git Bash):
```bash
curl -sS https://www.understandingwar.org/robots.txt
```
Expected: the file is returned. Note any `Disallow` rule that matches `/backgrounder` or the assessment paths.

- [ ] **Step 2: Read the site's terms of use**

Open `https://www.understandingwar.org/terms-of-use` (or the footer link on the homepage) and record the clause on reuse and automated access.

- [ ] **Step 3: Record the findings**

Create `docs/enterprise/isw_source_check.md` with: access date, robots.txt rules that matter, the ToS clause quoted verbatim, and a decision line.

Decision rules:
- If automated access is prohibited, stop. Mark ISW as blocked and tell the owner. Do not scrape.
- If it is allowed with attribution, record the attribution text. Go to Task 1.
- If the terms are unclear, ask the owner before Task 1.

- [ ] **Step 4: Commit**

```bash
git add docs/enterprise/isw_source_check.md
git commit -m "docs: ISW source licence and access check"
```

---

### Task 1: Save a real page snapshot

The parser cannot be tested against guesses. Save one real page, once.

**Files:**
- Create: `tests/fixtures/isw_snapshot_<YYYY-MM-DD>.html`
- Create: `tests/fixtures/README.md`

- [ ] **Step 1: Fetch one assessment page**

Find one current daily assessment URL on the ISW site, then:
```bash
curl -sS -A "AlertsResearch/1.0 (academic; contact owner)" -o tests/fixtures/isw_snapshot_2026-10-12.html "<assessment-url>"
```
Expected: a non-empty HTML file. Confirm with `grep -c "<html" tests/fixtures/isw_snapshot_2026-10-12.html`, which should print at least `1`.

- [ ] **Step 2: Record provenance**

Add to `tests/fixtures/README.md`:
```markdown
- isw_snapshot_2026-10-12.html: fetched <UTC time> from <url>; SHA-256 <hash from sha256sum>.
```
Get the hash with `sha256sum tests/fixtures/isw_snapshot_2026-10-12.html`.

- [ ] **Step 3: Find the publication date in the page**

Run:
```bash
grep -oiE '(published|updated|datetime)[^<]{0,80}' tests/fixtures/isw_snapshot_2026-10-12.html | head -20
grep -oE '<meta[^>]*(date|time)[^>]*>' tests/fixtures/isw_snapshot_2026-10-12.html | head -10
```
Record the exact element or attribute that holds the publication date (for example `<meta property="article:published_time" ...>` or a visible "Published" line). This is the value Task 2 will parse. Write it into `tests/fixtures/README.md`.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/isw_snapshot_2026-10-12.html tests/fixtures/README.md
git commit -m "test: save ISW assessment snapshot with provenance"
```

---

### Task 2: Parse the publication date (fixes Defect 1)

**Files:**
- Modify: `src/ingestion/batch_loaders.py` (`IswLoader`, around line 544 and line 605)
- Test: `tests/test_batch_loaders.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_batch_loaders.py` inside `TestIswLoader`:
```python
    def test_publication_date_comes_from_page_not_scrape_time(self, loader):
        """The record date must be the page's publication date, never datetime.utcnow()."""
        from pathlib import Path
        html = Path("tests/fixtures/isw_snapshot_2026-10-12.html").read_text(encoding="utf-8")
        published = loader._extract_publication_date(html)
        assert published is not None
        assert published.date().isoformat() == "2026-10-12"
```
Replace `2026-10-12` with the date recorded in Task 1 if the page is for a different day.

- [ ] **Step 2: Run it to verify it fails**

Run: `./venv/Scripts/python.exe -m pytest tests/test_batch_loaders.py::TestIswLoader::test_publication_date_comes_from_page_not_scrape_time -v`
Expected: FAIL with `AttributeError: 'IswLoader' object has no attribute '_extract_publication_date'`.

- [ ] **Step 3: Implement the parser**

In `IswLoader` add a method. The selector comes from Task 1 Step 3. This template uses a `<meta>` tag. Replace the pattern if Task 1 found something else:
```python
    def _extract_publication_date(self, html_text: str) -> Optional[datetime]:
        """Return the publication time stated on the page, or None if absent.

        Scrape time is never used as a fallback: a missing date means the record is dropped.
        """
        match = re.search(
            r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
            html_text,
            re.IGNORECASE,
        )
        if not match:
            return None
        return datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
```

- [ ] **Step 4: Run it to verify it passes**

Run: the same pytest command as Step 2.
Expected: PASS.

- [ ] **Step 5: Replace the scrape-time stamp**

In `_extract_threat_assessments`, replace `"event_date": datetime.utcnow().strftime("%d %b %Y")` with the publication date. Pass `published = self._extract_publication_date(html_text)` in at the top of the method. Return an empty list if `published` is None, and log a warning. Also add an `available_at` column in `transform` (UTC timestamp taken from `event_date`), since Task 4 joins on it. Then run `./venv/Scripts/python.exe -m pytest tests/test_batch_loaders.py -v` and expect the ISW tests that did not depend on the old date to pass. Fix any that did.

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/batch_loaders.py tests/test_batch_loaders.py
git commit -m "fix: ISW records take publication date from page, not scrape time"
```

---

### Task 3: Make threat labels checkable (fixes Defect 2)

The regex labels are not validated. This task makes the labels reproducible and auditable. It does not claim they are correct.

**Files:**
- Modify: `src/ingestion/batch_loaders.py` (`_extract_threat_assessments`)
- Test: `tests/test_batch_loaders.py`

- [ ] **Step 1: Write a golden-output test**

Use the snapshot. Record the extractor's current output as the expected value, then review it by hand.
```python
def test_isw_extraction_matches_reviewed_golden(loader):
    from pathlib import Path
    import json
    html = Path("tests/fixtures/isw_snapshot_2026-10-12.html").read_text(encoding="utf-8")
    records = loader._extract_threat_assessments(html)
    golden = json.loads(Path("tests/fixtures/isw_golden_2026-10-12.json").read_text(encoding="utf-8"))
    assert records == golden
```

- [ ] **Step 2: Create the golden file by hand review**

Run the extractor once, print its records, and compare each region and level against the page text. Save only the records a person has verified to `tests/fixtures/isw_golden_2026-10-12.json`. Record in `tests/fixtures/README.md` who checked it and when. Expected: every record in the golden file has a matching sentence in the snapshot.

- [ ] **Step 3: Run the test**

Run: `./venv/Scripts/python.exe -m pytest tests/test_batch_loaders.py::test_isw_extraction_matches_reviewed_golden -v`
Expected: PASS. If it fails, the extractor changed. Investigate before updating the golden file.

- [ ] **Step 4: Commit**

```bash
git add tests/test_batch_loaders.py tests/fixtures/isw_golden_2026-10-12.json tests/fixtures/README.md
git commit -m "test: pin ISW extraction against a hand-checked golden file"
```

---

### Task 4: Leakage-safe weekly join

**Files:**
- Create: `src/forecasting/isw_features.py`
- Create: `tests/test_isw_features.py`

- [ ] **Step 1: Write the leakage test first**

```python
# tests/test_isw_features.py
import pandas as pd
from src.forecasting.isw_features import weekly_isw_features


def _records():
    return pd.DataFrame({
        "available_at": pd.to_datetime(["2026-09-01T12:00Z", "2026-09-10T12:00Z"]),
        "ops_intensity_index": [0.66, 1.0],
    })


def test_record_published_after_origin_is_excluded():
    origin = pd.Timestamp("2026-09-05T00:00Z")
    feats = weekly_isw_features(_records(), origin=origin, weeks=2)
    # The 2026-09-10 record is after the origin and must not contribute.
    assert feats["isw_intensity_sum"].sum() == 0.66


def test_no_records_yields_zero_features_not_error():
    feats = weekly_isw_features(_records().iloc[0:0], origin=pd.Timestamp("2026-09-05T00:00Z"), weeks=2)
    assert (feats["isw_intensity_sum"] == 0).all()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `./venv/Scripts/python.exe -m pytest tests/test_isw_features.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.forecasting.isw_features'`.

- [ ] **Step 3: Implement the join**

```python
# src/forecasting/isw_features.py
"""Weekly ISW features, joined only on records published on or before the forecast origin."""

import pandas as pd


def weekly_isw_features(records: pd.DataFrame, origin: pd.Timestamp, weeks: int) -> pd.DataFrame:
    """Sum ISW intensity per week for the `weeks` weeks before `origin`.

    A record counts only if its `available_at` is on or before `origin`. This is the
    leakage rule from CLAUDE.md: nothing published after the forecast point is used.
    """
    origin = pd.Timestamp(origin).tz_convert("UTC") if pd.Timestamp(origin).tzinfo else pd.Timestamp(origin, tz="UTC")
    usable = records[records["available_at"] <= origin] if not records.empty else records
    starts = [origin - pd.Timedelta(days=7 * (k + 1)) for k in range(weeks)][::-1]
    rows = []
    for start in starts:
        end = start + pd.Timedelta(days=7)
        in_week = usable[(usable["available_at"] > start) & (usable["available_at"] <= end)] if not usable.empty else usable
        rows.append({"week_start": start, "isw_intensity_sum": float(in_week["ops_intensity_index"].sum()) if not in_week.empty else 0.0})
    return pd.DataFrame(rows).set_index("week_start")
```

- [ ] **Step 4: Run them to verify they pass**

Run: the same pytest command as Step 2.
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/forecasting/isw_features.py tests/test_isw_features.py
git commit -m "feat: leakage-safe weekly ISW features keyed on available_at"
```

---

### Task 5: Backtest comparison and result record

The question is whether ISW features beat the deliverable on the same rolling-origin backtest. Compare, do not tune.

**Files:**
- Modify: `run_pipeline.py` (add an `--isw` flag that reports the comparison; the default path is unchanged)
- Create: `docs/enterprise/isw_result.md`

- [ ] **Step 1: Confirm the MVP path is unchanged**

Run: `./venv/Scripts/python.exe run_pipeline.py --offline --as-of 2026-10-12`
Expected: exit 0, and the baseline weekly WAPE is still `0.0852`. If it differs, stop and investigate.

- [ ] **Step 2: Add the comparison behind `--isw`**

Use the same origins, same baseline, same metric (weekly WAPE). Add the ISW candidate as an extra regressor in a candidate model. Do not change the origins. Report both numbers.

- [ ] **Step 3: Run the comparison**

Run: `./venv/Scripts/python.exe run_pipeline.py --offline --as-of 2026-10-12 --isw`
Expected: exit 0, and the report includes an ISW line next to the baseline.

- [ ] **Step 4: Write the result**

Create `docs/enterprise/isw_result.md` with: the ISW candidate's weekly WAPE, the baseline's, the Diebold–Mariano p-value (same method as `docs/gate3_results.md`), and an explicit line: "Criterion 1 is met" or "Criterion 1 is not met". Do not write any other conclusion.

- [ ] **Step 5: Commit**

```bash
git add run_pipeline.py docs/enterprise/isw_result.md
git commit -m "feat: ISW backtest comparison behind --isw flag; result recorded"
```

---

## Self-review

- **Spec coverage:** Task 0 (licence gate), Tasks 1–3 (timestamp, parser, labels), Task 4 (leakage rule), Task 5 (backtest against the deliverable). The first milestone is Tasks 0–4. Task 5 is the evaluation.
- **Placeholders:** The publication-date regex in Task 2 is a template that Task 1 Step 3 must confirm against the real page. This is intentional. The golden file in Task 3 is created from hand review, not guessed.
- **Consistency:** `_extract_publication_date` (Task 2) is used in `_extract_threat_assessments`. `available_at` (Task 4) must be set from the publication date in the loader's `transform` output. That field name is not yet in `transform`, so Task 2 Step 5 should also add it. Check that before Task 4.
- **CLAUDE.md non-negotiables:** no leakage (Task 4 test), no fabricated timestamps (Task 2 removes the scrape-time stamp), no synthetic ground truth (Task 3 golden file is hand-checked), reproducibility (fixtures and golden file are committed).

## Milestone 1 definition of done

Tasks 0–4 committed and their tests passing. The MVP path still reproduces 0.0852. Task 5 is the evaluation step and is a separate decision for the owner.
