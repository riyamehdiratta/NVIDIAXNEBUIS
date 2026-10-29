# Iteration 13 - OpenShell-managed Nebius inference

**Date:** 2026-10-29 | **SRS:** 1.3

## Changes

- Added an endpoint-bearing OpenShell provider profile for `api.tokenfactory.nebius.com`, scoped to `/v1/**` and Threadline's Python executable paths. The actual key is imported into the OpenShell gateway provider store; the app only sees an opaque placeholder.
- Replaced the unconfigured `inference.local` route in Threadline's policy with an enforced Token Factory host/path allow rule. OpenShell blocks unlisted network destinations.
- Added a two-step synthetic `preview` / `confirm` utility and a minimal provider smoke test.
- Set Nemotron `chat_template_kwargs.enable_thinking=false` in extraction requests. The initial smoke request showed Lightning spending a 64-token completion budget on reasoning text (`finish_reason=length`); with reasoning disabled the same model returned valid JSON (`finish_reason=stop`).
- Updated the runbook to use the direct endpoint-bound OpenShell provider path supported by the installed 0.1.6 CLI.

## Acceptance evidence

- Token Factory `/v1/models` returned both configured model IDs: `nvidia/Nemotron-3_5-Lightning` and `nvidia/nemotron-3-super-120b-a12b`.
- A synthetic preview showed the exact payload, selected model, source IDs, and email/phone redaction counts before confirmation. The calendar sample was kept local because its `10:30` time is incorrectly classified as a phone number by the current redactor.
- Confirmed Threadline scan returned HTTP 200 through the OpenShell-managed provider: 3 synthetic sources, model `nvidia/Nemotron-3_5-Lightning`, 5 candidate commitments, 3.26 seconds end-to-end. Egress status is `sent`, with 2 redaction replacements, 1,861 payload characters, receipt ID `1c4742bb-3e2e-4069-b610-7ce5ee377628`, SHA-256 `57fc2dd2a7ac6c9b4531154641cc092b757c53b4800aedaba31b351774fd0c6a`.
- OpenShell logged `ALLOWED /usr/local/bin/python3.12 -> api.tokenfactory.nebius.com:443` and `ALLOWED POST https://api.tokenfactory.nebius.com/v1/chat/completions`. A same-sandbox request to `example.org:443` logged `DENIED` with `transparent_tcp_policy_denied`.
- Full egress receipt, including the exact minimized request body, is saved in [nebius-tokenfactory-receipt.json](../evidence/nebius-tokenfactory-receipt.json). The evidence contains only generated sample records and redaction placeholders.

## Decisions and limits

- The installed OpenShell 0.1.6 CLI does not expose the newer `openshell inference` route command. The tested configuration uses an endpoint-bound provider profile and direct Token Factory host policy instead; the key is still substituted outside the sandbox.
- This proves live Token Factory inference through OpenShell, not a public deployment or a production Linux VM. WSL2 + Docker Desktop remains experimental.
- The local app currently treats the clock text `10:30` as a phone number. It was excluded from this inference sample and remains a follow-up redaction fix.
- The successful receipt and demo database exist in the local sandbox; the public repository contains the synthetic receipt snapshot, not the gateway credential.
