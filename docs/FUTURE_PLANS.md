# Future plans and parked items

This file records work that is paused, blocked or planned. Nothing here is used by the current
analysis or the public-facing documents.

## Parked: Kaggle "Massive Missile Attacks on Ukraine" (Petro Ivaniuk)

- **Status:** parked. Not used in any current analysis or document. Its figures were removed from
  the repository on 2026-10-12, by owner decision.
- **Why parked:** every row of the daily file cites a Telegram channel as its source, so the file is
  an aggregation of Telegram-derived data. The Telegram API terms bar "using, accessing or
  aggregating data obtained from the Telegram platform" for machine-learning work. Publishing
  aggregated figures in a public repository is a wider exposure than internal descriptive use.
- **Licence:** CC BY-NC-SA 4.0. Any future derived data must keep that licence and credit the author.
- **To reopen, one of these must happen:** (a) written permission from Telegram that covers this
  research use, or from the dataset author on provenance; or (b) an equivalent dataset whose
  source is not Telegram.
- **Local copy:** the two CSVs are in `data/raw/kaggle_missile/` (gitignored, not in the
  repository). Delete them if the dataset will not be used.
- **History:** removing files does not remove them from git history. Earlier commits (for example
  `7e19df8`, `1986c03`) still contain the figures. Rewriting history needs a separate, explicit
  decision.

## Planned

- `docs/SAFETY.md`: what the project will not publish (time-to-impact estimates, shelter advice,
  threat-type inference, oblast rankings as danger, real-time claims).
- `docs/GLOSSARY.md`: plain definitions of alert, record, wave and match.
- README top layer rewritten for a general audience, with official warning sources linked (not
  invented).
- Population data (open source, licence to be checked) for per-capita figures.
- Shelter data: none exists in the project. Any shelter-access analysis needs a source first.

## Blocked: sources with an unlock condition

| Source | Blocked by | Unlock condition |
|---|---|---|
| ISW | Terms: no dataset use without written permission | Written permission from press@understandingwar.org |
| ACLED | API needs Research access; project account is Open | Institutional registration or Research access from ACLED |
| alerts.in.ua | No API token | Token issued; then measure real-time latency (criterion 3) |
| Oryx | No reuse rights found | Written permission |
| Telegram @kpszsu | Telegram API terms | Written view from Telegram |
| Volunteer data licence | `datasets/README.md` returned HTTP 503 | Read the dataset's own licence statement |

## Dropped

- **GDELT** for wave attribution: hourly correlation with volunteer alerts was near zero over
  672 hours (`docs/analysis/news_sources_research.md`, sections 5–8). Could be revisited only with
  event-time data and a validated coding method.

## Open analysis questions

- Whether the Kirovohrad–Poltava same-minute batching is one message covering both oblasts. This
  needs message identifiers, which the dataset does not have.
- Feed behaviour after 2026-09-07, when the official feed stops. No ground truth exists after that
  date.
