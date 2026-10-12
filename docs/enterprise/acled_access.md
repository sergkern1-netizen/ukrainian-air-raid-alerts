# ACLED API access (enterprise source, replaces ISW)

Checked: 2026-10-12. Sources: https://acleddata.com/myacled-faqs (access FAQ, fetched);
https://developer.acleddata.com/rehd/cms/views/acled_api/documents/FAQs_ACLED-Registration-and-Access-Model_11.2021.pdf (older FAQ, search result only).

## Status: BLOCKED on account type

- The API requires a **Research, Partner or Enterprise** access level. It is not available at the
  **Open** level.
- Registration uses an **institutional email**. Personal or generic addresses (for example
  gmail.com) receive **Open** access only.
- The project account is `sergkern1@gmail.com`, so the current account gets Open access.
- Result: the API is not reachable from this account. An institutional email, or an ACLED
  decision to grant Research access for this project, is required.

## Authentication (changed)

- ACLED is moving away from key-based access. Existing keys worked until 2025-09-15, and no new
  keys were issued during the transition.
- Current options per the FAQ: cookie-based access (browser or tool use) or OAuth token-based
  access (programmatic). The exact setup is in ACLED's API authentication guide. The API getting-
  started page could not be read in this check, so the parameter names are unconfirmed.
- Older guidance used `key` and `email` query parameters. Do not rely on that for new code until
  the current guide is checked.

## Terms relevant to this project

- ACLED may limit access for organizations "monetizing products created using ACLED's data."
  This project is non-commercial research, but the terms must be read in full before use.
- Accepting the terms is part of registration. The myACLED terms cover data use, acknowledgement
  and citation. Read them before the first download.
- The non-commercial free-use statement is from an older (2021–2022) guide. The current terms
  text was not found in this check.

## Data currency (CLAUDE.md blocker 2)

- Per `docs/data_inspection_gate1.md`, the Ukraine Conflict Monitor lists weekly updates through
  26 Sep to 2 Oct 2026. This resolves "beyond May 2025" for the monitor page.
- The API data currency for Ukraine is not confirmed. Confirm it after access is granted.

## Next steps (owner)

1. Decide whether to register with an institutional email, or request Research access from
   ACLED (access@acleddata.com). Do not register with a personal account and assume API access.
2. Read the myACLED terms before registering.
3. Once access is granted, the API guide must be read for the current auth method. Then we
   confirm the Ukraine filter and the row limit.
