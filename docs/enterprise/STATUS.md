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
