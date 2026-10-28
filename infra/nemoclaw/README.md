# NemoClaw, OpenShell, and Hermes runtime notes

This is a runbook for the planned secure runtime. It is **not verified as deployed** from this Windows workspace: the OpenShell/NemoClaw CLIs, Linux sandbox host, Docker daemon, and Nebius key are not available here. OpenShell supports Linux as a supported host; Windows via WSL2 + Docker Desktop is experimental. For a judged run, use a Linux host/VM with a Docker driver, such as a provisioned Nebius AI Cloud VM.

## Intended boundaries

- Threadline's import directory and SQLite database are the only writable application data paths.
- The agent does not receive credentials for email, calendar, payments, or arbitrary web browsing.
- The sandbox receives only the inference provider route. Inference egress is mediated by OpenShell; use its managed credential/provider mechanism and do not pass a raw key in the image.
- Threadline's UI policy and OpenShell runtime policy are separate controls. The first controls permitted local app actions; the second constrains sandbox filesystem and network access.

## Local container

`docker compose up --build` runs the app on `127.0.0.1:8000` and persists its data at `./data`. This is the quickest local MVP path, but Docker Compose alone is not an OpenShell sandbox.

## OpenShell policy

`threadline-policy.yaml` is a starting policy for placing the Threadline container in an OpenShell sandbox. It grants writes only to `/var/lib/threadline` and `/tmp`, and permits model traffic only through `inference.local`. Review and validate it against the exact OpenShell/NemoClaw version, image paths, and provider configuration before using personal data. The app needs a real persistent volume for `/var/lib/threadline`; keep that volume host-owned and protected.

The current app API accepts OpenAI-compatible chat completion requests. To mediate the API key outside the sandbox, configure the OpenShell/NemoClaw provider to route the app's inference calls to `https://inference.local/v1` and store the Nebius Token Factory credential in host-managed provider state. The sandbox-side app can use a non-secret placeholder API key because the inference router strips the placeholder and supplies the configured provider credential.

## Hermes/NemoClaw setup target

1. On a supported Linux host, install OpenShell and NemoClaw from their official installers and configure the Docker compute driver.
2. Create a custom OpenAI-compatible provider in the NemoClaw/OpenShell gateway for the Nebius Token Factory base URL; store the Token Factory key in provider-managed credentials.
3. Use the NemoClaw Hermes workflow (`nemohermes onboard`) to install/configure Hermes with that managed compatible inference endpoint. Hermes accepts an OpenAI-compatible API endpoint.
4. Build the Threadline image, run it in a policy-restricted sandbox with its persistent data volume, and route app inference to `https://inference.local/v1`.
5. Verify with synthetic data: successful Nemotron extraction, blocked arbitrary egress, request receipt matching the minimized source payload, and persistence after a sandbox restart.

Refer to the current [NVIDIA OpenShell policy docs](https://docs.nvidia.com/openshell/latest/sandboxes/policies), [NemoClaw compatible endpoint guide](https://docs.nvidia.com/nemoclaw/user-guide/hermes/inference/custom-endpoints/set-up-openai-compatible-endpoint), [Hermes provider docs](https://hermes-agent.nousresearch.com/docs/integrations/providers), and the current [Nebius Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference). Provider and CLI commands can change; validate live setup rather than copying assumptions from this note.
