# Iteration 10 - simulated-week evidence and extraction evaluation

**Date:** 2026-10-28 | **SRS:** 0.8

## Changes

- Added a seven-day, 49-decision synthetic replay in Permissions. It calls the production shadow prediction and Wilson summary helpers, displays confidence-bound movement, and shows a low-evidence action that remains at L1.
- The replay is non-persistent: it changes no policies, actions, or user history.
- Centralized the reversible-action execution gate so production action proposals and the simulation use the same rule.
- Added a 60-source synthetic extraction corpus and local/Nemotron CLI evaluator. The remote mode requires the user to type `SEND`, logs exact synthetic requests in the egress ledger, and records batch latency.
- Added aggregate egress totals to Privacy & Activity: source attachments, attempts, successful responses, regex redaction matches, local-only scans, and payload character count.

## Acceptance evidence

- Local evaluation: 60 sources (30 positive / 30 hard negative), TP=30, FP=30, FN=0; precision 0.500, recall 1.000, F1 0.667. Results are in [evaluation-results.json](../evaluation-results.json); the limitations and runner are in [evaluation.md](../evaluation.md).
- Seven-day simulation returned 7 day summaries and 49 synthetic events, suggested promotion only after 44 shadow samples with a qualifying Wilson lower bound, and left the example policy at L1. Database row counts did not change during replay.
- Demo-mode API acceptance denied both text and file imports with HTTP 403.
- Local-only scan acceptance incremented the local scan count while remote attempts, payload characters, and uploaded file attachments stayed at zero.
- Frontend production build and Python compilation passed.
- Nemotron comparison remains pending a configured Nebius key. No performance result has been invented.

## Decisions and limits

- The sample corpus is intentionally small and generated with its labels by the same script; its numbers are proof the evaluator runs, not general product quality claims.
- Promotion evidence is a Wilson 95% lower bound plus a minimum of 40 shadow samples. The user still changes the action level; simulation does not alter real settings.
- Egress `redaction_matches` are pattern replacements and cannot prove that all raw personal information was removed. The exact request receipt remains necessary.
