# News sources for Ukraine: terms review (2026-10-12)

Purpose: an independent news signal to triangulate the volunteer alert feed (feed-integrity work),
not a forecasting input. Checked against the outlets' own pages, not search summaries.

| Source | Terms (verified) | Verdict |
|---|---|---|
| **GDELT Project** (gdeltproject.org/about.html) | "all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee." Redistribution allowed; "a citation to the GDELT Project and a link to this website" required. Page states "daily updates". | **Best candidate.** Open licence with attribution. Machine-coded news events, so noisy: must be validated before use. |
| **Ukrinform** (ukrinform.net) | Footer: "© 2015-2026 Ukrinform. All rights reserved." Citing online requires a link to ukrinform.net "not lower than the first paragraph." No RSS or scraping statement found. Offline/app reuse needs rights-holder consent (reported, not on the site). | **Not usable as a dataset** without written permission. Citation only. |
| **Kyiv Independent** (kyivindependent.com/terms-of-use/) | Page returned HTTP 404. No terms found. | **Unverified.** Re-check the site footer or contact the outlet. |

## Recommendation

Use GDELT as the independent news signal for feed integrity. Its events are coded by machine from
news articles, so precision is unknown. Before any result is reported, check its Ukraine
air-attack events against the volunteer feed on a sample of known periods.

Steps that need the owner's approval:
1. Download one sample day of GDELT event exports (file size to be stated before download).
2. Filter to Ukraine and attack-related event codes, then compare with the volunteer feed.
