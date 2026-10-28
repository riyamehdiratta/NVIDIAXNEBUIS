# Iteration 06 - local scam triage

**Date:** 2026-10-28 | **SRS:** 0.4

## Changes

- Added deterministic local indicators for authority threats, urgency, credentials, payment requests, remote-access instructions, secrecy pressure, and shortened links.
- Added a Scam Check workspace with matched indicators, next-step guidance, digest-only history, and deletion controls.
- Added trusted-contact profiles with PBKDF2 salted phrase hashes, verification results, deletion, and local audit events. The phrase itself is never returned or written to logs.
- Added schema v4 and JSON export for digest-only scam receipts. Message content is never stored or sent to an inference provider by these routes.
- Added docs explaining that the score is a heuristic signal score, not a probability or verdict. The checker does not fetch links or inspect attachments.

## Acceptance evidence

- `npm run build` and Python compilation passed.
- Isolated API scenario classified synthetic government-impersonation text at 100/100 with seven matched signals; verified correct and incorrect family phrases; confirmed neither raw text nor phrase appeared in SQLite dumps or export; confirmed zero model egress.
- Scam checks and family profiles were created in an isolated ignored data directory.

## Decisions and limits

- Public FTC guidance supports checking unexpected government/payment demands through independently located contact details and never sharing verification codes. See [FTC government impersonation guidance](https://consumer.ftc.gov/articles/how-avoid-government-impersonation-scam) and [FTC verification-code guidance](https://consumer.ftc.gov/consumer-alerts/2024/03/whats-verification-code-why-would-someone-ask-me-it).
- Pattern matches can miss scams or flag legitimate messages. The displayed score is not a probability.
- Family phrases are static in this iteration; there is no rotating challenge protocol, automatic family notification, susceptibility profile, or link sandbox.
- SQLite is unencrypted by the application. A salted hash is safer than storing the phrase in plain text, but device encryption remains important.
