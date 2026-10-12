# Enterprise source candidates: terms review (2026-10-12)

Checked after ISW and ACLED were dismissed. Each source below was checked against its own
primary page or the Telegram API terms. Search summaries were not used as evidence.

| Source | Access | Terms (verified) | Verdict |
|---|---|---|---|
| **Kaggle: "Massive Missile Attacks on Ukraine"** (Petro Ivaniuk, `kaggle.com/datasets/piterfm/massive-missile-attacks-on-ukraine`) | Free Kaggle account to download. Two CSVs: `missile_attacks_daily.csv` (902.8 kB, daily) and `missiles_and_uavs.csv`. Updated 2 days before the check. | **License: CC BY-NC-SA 4.0** (shown on the dataset page, verified in Chrome). Non-commercial, attribution, share-alike. | **Candidate.** Usable for this non-commercial research if we attribute the author and keep derived data under CC BY-NC-SA. |
| **Telegram @kpszsu** | Needs an own `api_id` (Telegram ToS 2.1: "You must obtain your own api_id"). | Telegram API terms, clause 1.5: "you are prohibited from using, accessing or aggregating data obtained from the Telegram platform" and may not use it "to train, fine-tune or otherwise engage in the development ... of artificial intelligence, machine learning models". | **Blocked.** The clause bans aggregating Telegram data, and this pipeline is a forecasting model. Needs Telegram's written position. Also a fake-channel risk (CLAUDE.md, `RESEARCH_FINDINGS_MASTER.md`). |
| **Oryx** (`oryxspioenkop.com`) | Public web pages. | Only a footer "Copyright © Oryx". No reuse, scraping or redistribution terms found on the homepage. The contact page was not read. | **Blocked.** No licence grants reuse. Written permission is needed before using its data. |
| **Texty.org.ua** | Public articles. | CC BY 4.0 (footer). Attribution with a hyperlink in the first or second paragraph. No scraping terms found. | **Reference only**, as CLAUDE.md says. Journalism, not a structured alert or strike dataset. |

## Recommendation

The Kaggle missile-attack dataset is the only candidate that is both usable under its licence and
structured for the pipeline. Before any work:

1. Download the CSVs with the owner's Kaggle account (not automated from this session).
2. Confirm the file formats and date coverage against the Vadimkin volunteer series. Do not merge
   them without a leakage check.
3. Put the attribution and the CC BY-NC-SA 4.0 notice in the README and in any published derived
   data.

## Notes for the owner

- Telegram: ask Telegram in writing whether the aggregation clause covers a research forecasting
  model. Until then, do not collect @kpszsu.
- Oryx: a permission request needs the project description. Contact details are on the Oryx site.
