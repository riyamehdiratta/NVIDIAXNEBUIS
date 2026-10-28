# Iteration 08 - interface text repair and feature guide

**Date:** 2026-10-28 | **SRS:** 0.6

## Changes

- Repaired mojibake punctuation and replacement characters in the React interface, including the dashboard's “You're up to date” state and common separators.
- Replaced the ambiguous `~1 min` caption with “Takes about a minute.”
- Changed “You approve every action” to “Approvals follow your per-action policy,” which remains accurate when the user opts into local automation.
- Corrected policy-level labels that displayed question-mark separators.
- Added a current feature guide and linked it from the README.

## Acceptance evidence

- `npm run build` passed after the copy corrections.
- Source scan found no remaining replacement characters or common garbled UTF-8 sequences in the React source.
- Local app serves the rebuilt frontend bundle at `http://127.0.0.1:8000/`.

## Decisions and limits

- Use simple ASCII punctuation in functional UI labels where it avoids encoding ambiguity; intentional typography remains where valid.
- This iteration changes copy only; it does not change application behavior or permission enforcement.
- The “about a minute” label describes the review estimate, not a guaranteed processing time.
