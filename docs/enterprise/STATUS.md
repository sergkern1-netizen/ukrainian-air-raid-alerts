# Enterprise track status (closed 2026-10-12)

Decision (owner): the enterprise track stops at the Kaggle missile dataset, used for descriptive
reporting only. No enterprise source feeds the forecast.

| Source | Outcome | Record |
|---|---|---|
| ISW | Dismissed. Terms do not permit scraping, dataset incorporation or redistribution without written permission. | `isw_source_check.md` |
| ACLED | Dismissed. The API is not available on this account (Open tier). | `acled_access.md` |
| Telegram @kpszsu | Blocked. API terms prohibit aggregating Telegram-derived data for ML. Not pursued. | `candidates_review.md` |
| Oryx | Blocked. No reuse rights found. Not pursued. | `candidates_review.md` |
| Texty.org.ua | Reference only (CLAUDE.md). CC BY 4.0. | `candidates_review.md` |
| Kaggle missile attacks | Descriptive use only. Telegram-derived provenance accepted by owner. | `kaggle_missile_profile.md`, `kaggle_missile_descriptive.md` |

Future work, when the owner chooses to reopen: the alerts.in.ua real-time poller (needs a token),
and any of the blocked sources after written permission.

## News track (added 2026-10-12)

GDELT was tested for wave attribution and dropped by owner decision. See
`docs/analysis/news_sources_research.md`, sections 5–8. Ukrainian outlets (Suspilne, Ukrainska
Pravda, LIGA.net, RBC-Ukraine) and the State Emergency Service were not pursued: their reuse terms
do not permit dataset use. The Air Force channel remains blocked by the Telegram terms.
