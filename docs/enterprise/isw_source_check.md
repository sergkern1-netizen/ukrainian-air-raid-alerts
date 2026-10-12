# ISW source check (Plan Task 0)

Status: **robots.txt reviewed; terms of use pending human review.** Scraping stays blocked
until the terms-of-use section below has a decision.

## 1. robots.txt (https://understandingwar.org/robots.txt, reviewed 2026-10-12)

Rules that apply to a generic crawler (`User-agent: *`):
- `Disallow: /wp-json/`, `/?rest_route=`, `/cdn-cgi/`, `/wp-admin/`.
- None of these cover `/backgrounder` or the daily assessment paths. Assessment pages are not
  disallowed for generic clients.

Rules that name specific bots:
- `ShapBot`: `Disallow: /` (full block). Not this project.
- `Arquivo-web-crawler`: `Disallow: /` (full block). Not this project.
- `GPTBot`, `ClaudeBot`, `CCBot`, `PerplexityBot`, `Bytespider`: `Crawl-delay: 600` (10 minutes
  between requests) plus the same path disallows. The site asks AI crawlers to wait 10 minutes
  between requests.
- `SiteAuditBot`: `Crawl-delay: 2`.

Sitemap: `https://understandingwar.org/sitemap_index.xml`.

### What this means for this project

- **Our client is not on a named block list.** The loader sends `requests`' default user agent,
  and the plan's snapshot step uses `AlertsResearch/1.0`. Both fall under `*`, which allows the
  assessment pages.
- **The 600-second delay is aimed at AI crawlers.** ClaudeBot is named. The project is a
  research pipeline, not a training crawler, but the site's stated expectation for AI-related
  access is one request per 10 minutes. Treat that as the limit, not a suggestion.
- **Backfill is slow at that rate.** One request per 600 seconds is about 144 requests a day. A
  backfill of several years of daily assessments takes many days, so plan it as a background job,
  or ask ISW for a data feed.
- **Use the sitemap, not link-following.** Pull assessment URLs from the sitemap, then request
  each one at the allowed rate.

### Decisions still open (for the owner)

1. Use an honest user agent that names the project and a contact, not the default `requests`
   agent.
2. Use a 600-second delay for all ISW requests, matching the AI-crawler rule, unless ISW's terms
   allow faster access.
3. Do not commit full HTML snapshots to the public repository (see section 2).

## 2. Terms of use (reviewed 2026-10-12 via Chrome)

Source: https://understandingwar.org/fair-use-and-attribution-policy/ (footer link "Fair Use &
Attribution Policy"; last revised January 8, 2026). The policy covers all ISW Materials, including
the Critical Threats and Taiwan products.

Permitted (section 1):
- "viewing and sharing materials in their published form for non-commercial, informational or
  media purposes; and quoting or excerpting text with appropriate attribution."
- Attribution text: "Source: Institute for the Study of War".

Requires prior written permission (section 1):
- "Any modification, commercial exploitation, redistribution, or incorporation of ISW Materials
  into other datasets, mapping platforms, analytic products or systems requires prior written
  permission from ISW."

Restrictions (section 3). Users may not:
- "copy or reproduce shapefiles, developer notes, or datasets for any purpose without ISW's
  written consent"
- "redistribute ISW Materials to third parties in bulk, via API, or through automated means."

Contact for permission: press@understandingwar.org.

### Assessment against the plan

- **Plan Task 2-4 (turn assessments into a dataset feature):** this is "incorporation of ISW
  Materials into other datasets" and needs written permission. Not covered by the permitted use.
- **Plan Task 1 (commit a full page snapshot to the public repo):** this is redistribution. Not
  allowed. Do not commit ISW page content.
- **Quoting a short sentence with attribution in a document** is permitted.

**Decision: NOT ALLOWED as planned.** Scraping for an internal dataset needs ISW's written
permission first. Options for the owner:
1. Email press@understandingwar.org requesting written permission for research use, stating the
   project, the non-commercial purpose, and that no ISW content will be republished.
2. Drop ISW as an enterprise source and move to another source (ACLED needs an API key and its
   own terms check).

Task 0 stays closed as "not allowed" until permission is granted. Plan Tasks 1-5 must not start.
