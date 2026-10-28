# Iteration 05 - earned autonomy core

**Date:** 2026-10-28 | **SRS:** 0.3

## Changes

- Added SQLite schema v3 for action levels, shadow evidence, caps, global autonomy setting, execution mode, undo deadline, and inverse receipt.
- Added L0-L4 per-action controls and life-area metadata. Only reminders and unsent drafts are eligible for automatic execution. Calendar exports remain L1 approval-only.
- Added shadow mode using a transparent majority of prior explicit decisions. It abstains until five choices exist, records agreement on the user's next decision, and hides the prediction from pending-action UI/API responses.
- Added a 95% Wilson lower bound, 40-sample minimum, and 0.80 bound threshold as a promotion recommendation. Policy never changes automatically.
- Added a global pause switch, daily per-tool caps, ten-minute undo for reminders/drafts, and one-level demotion following undo.
- Added a Permissions UI for the switch, levels, life areas, shadow mode, confidence display, caps, undo receipts, and irreversible-tool limits.
- Extended portability export to include the action/undo ledger, reminders, activity, egress receipts, and global autonomy setting. Pending shadow predictions are omitted from the export.

## Acceptance evidence

- `npm run build` and Python compilation passed.
- Fresh-database API acceptance passed: migration to schema 3; global pause blocked auto-run; L2 ran a local reminder and undo deleted it/demoted to L1; calendar L2 was rejected; 40/40 shadow agreements produced a 0.912 Wilson lower bound and a promotion recommendation; L4 cap held the second reminder for review; zero model egress occurred.
- Test actions and sources were created in an isolated ignored data directory, not the user's live workspace.
- Repeated application startup/shutdown passed, and an undone automatic action still consumed that day's cap.
- Pending shadow predictions stayed hidden in the action API and portability export; export included policies, actions/undo data, reminders, egress receipts, activity, and global switch state.

## Decisions and limits

- The initial shadow predictor is an explainable majority-choice baseline, not a model's intent prediction. This keeps the mode usable without cloud access and prevents claims of model accuracy without measurement.
- L3 adds an activity report record; L4 enforces the configured daily cap. Both stay within the same local tool allowlist as L2.
- Undo is limited to a reminder row or an unsent draft stored by Threadline. Downloaded calendar files and external side effects cannot be recalled.
- The global switch pauses autonomous execution; it does not block a direct human approval.
- The application checks policy before executing its own handlers. OS-level isolation still requires a configured OpenShell/NemoClaw host.
