# Devpost draft and demo outline

## Category

Personal AI Track

## Project description draft

**Threadline remembers what matters, then helps you move it forward.** Import a note, email, or calendar file and Threadline turns promises, deadlines, and waiting items into a persistent memory linked to the original evidence. Run reusable skills, test shadow predictions, set L0-L4 per action type, enforce caps, pause automation, and undo reversible local actions. Promotion is evidence-based and remains the user's decision. The memory stays in a local workspace; before a remote scan, Threadline shows the minimized request and waits for confirmation.

Threadline is configured for NVIDIA Nemotron 3.5 Lightning for routine extraction and Nemotron 3 Super for ambiguous or larger scans through Nebius Token Factory. A Token Factory key is not configured in this workspace, so live inference remains to be verified. The local-only path works without cloud inference. NemoClaw/OpenShell runtime setup is documented separately and should only be described as deployed after it has been tested live.

## Demo video outline (target: 2:30)

1. **0:00-0:20** Introduce the problem: commitments are scattered across messages, calendars, and notes.
2. **0:20-0:45** Load the synthetic workspace and import one email and one calendar file.
3. **0:45-1:15** Preview the minimized request, show redaction and the exact payload, then run local-only or confirmed Token Factory scan.
4. **1:15-1:45** Inspect evidence-linked loops; correct one item and mark another complete.
5. **1:45-2:10** Enable shadow mode and explain the five-choice warm-up and 40-sample promotion floor. Opt in to L2 on a reversible local action, then show its ten-minute undo and resulting demotion. Then paste a synthetic impersonation text into Scam Check and verify a demo family phrase without any message egress.
6. **2:10-2:30** Trigger global pause and show an automatic action left in the review queue; show the zero-egress receipt. Describe NemoClaw/OpenShell/Hermes only if verified for the submitted build.

## Still required before submission

- Working public demo or test-build URL: **not yet provisioned**.
- Public repository URL: **not yet published**.
- YouTube link: **not yet recorded/uploaded**.
- Nebius/NVIDIA feedback: add measured personal feedback after using the services; do not invent performance results.


## Iteration 07 demo addition

Show Precommitments: save “No automatic actions from 22:00 to 07:00,” display the boundary checks, and explain that an active quiet window blocks autonomous local actions at the API. Demonstrate that a manual override needs a typed reason and leaves an action receipt. Describe this as a narrow, local quiet-hours compiler rather than a general natural-language constitution engine.
