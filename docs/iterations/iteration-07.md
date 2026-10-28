# Iteration 07 - quiet-hours precommitments

**Date:** 2026-10-28 | **SRS:** 0.5

## Changes

- Added a bounded quiet-hours rule compiler and boundary test report.
- Added SQLite schema v5 with persistent precommitment definitions and action linkage/override receipts.
- Added APIs to list, compile/save, and delete contracts.
- Enforced contracts at proposal time (prevents automatic execution) and again at approval time (requires a typed override reason during an active window).
- Added a Precommitments workspace for authoring rules, viewing compiler boundary results, and removing rules.
- Rules use the local clock of the Threadline host. Supported scopes are all automatic local actions, reminders, reply drafts, and calendar exports.

## Acceptance evidence

- `npm run build` passed; Python compilation passed.
- Fresh isolated database migrated to schema v5.
- Unit-style boundary checks passed for overnight quiet hours and invalid/missing ranges.
- Isolated FastAPI scenario saved a rule covering the current local time, enabled L2 for reminders, and confirmed proposal stayed pending. Approval without reason returned 409; a valid reason succeeded and appeared in the action receipt.
- The rule's `at_start`, `inside`, `before_end`, `at_end`, and `after_end` red-team results were returned and validated.

## Decisions and limits

- This is a narrow parser for a blocker statement, supported scope, and one 24-hour range; it is not unrestricted natural-language policy understanding.
- Manual override remains available after the user types a reason of at least 20 characters. It provides friction and an audit record, not an unbreakable lock.
- This is local FastAPI enforcement; it does not configure or prove OpenShell/NemoClaw policy enforcement.
- Additional Ulysses capabilities such as encrypted/precommitted schedules, risk classification, and irreversible action refusal remain future work.
