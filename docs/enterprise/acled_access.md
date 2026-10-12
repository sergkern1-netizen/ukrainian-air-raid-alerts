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

## Account check (2026-10-12, after login and consent)

- Login works. The consent page (privacy policy and Terms and Conditions) was completed by the
  owner.
- The profile page (`/user/edit`) shows no access level.
- A minimal read-only request to `https://acleddata.com/api/acled/read?_format=json&country=Ukraine&limit=1`
  with the owner's browser session returned `{"message":"Access denied"}`.
- Likely cause: the account is still at Open level, because the email domain is personal
  (gmail.com). The cause is not confirmed. The API docs page could not be read from this session
  (site permission denied), so the current auth method is still unconfirmed.

Next: confirm the access level in the myACLED area. If it is Open, request Research access from
access@acleddata.com with the project description, or register with an institutional email.
