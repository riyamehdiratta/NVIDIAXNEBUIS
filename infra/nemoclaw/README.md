# NemoClaw, OpenShell, and Hermes runtime notes

This runbook documents the runtime verified in this workspace. OpenShell 0.1.6 and its user gateway are installed in Ubuntu WSL; Docker Desktop 28.5.1 is connected; `openshell doctor check` passes; and a synthetic sandbox demonstrated a permitted and a denied destination. WSL2 + Docker Desktop is an experimental OpenShell host combination, so use a native Linux VM for a judged or personal-data deployment.

## Intended boundaries

- Threadline's import directory and SQLite database are the only writable application data paths.
- The agent does not receive credentials for email, calendar, payments, or arbitrary web browsing.
- The sandbox receives only the inference provider route. Inference egress is mediated by OpenShell; use its managed credential/provider mechanism and do not pass a raw key in the image.
- Threadline's UI policy and OpenShell runtime policy are separate controls. The first controls permitted local app actions; the second constrains sandbox filesystem and network access.

## Local container

`docker compose up --build` runs the app on `127.0.0.1:8000` and persists its data at `./data`. This is the quickest local MVP path, but Docker Compose alone is not an OpenShell sandbox.

## OpenShell policy

`threadline-policy.yaml` is the starting policy for placing the Threadline container in an OpenShell sandbox. It grants writes only to `/var/lib/threadline` and `/tmp`, and permits model traffic only through `inference.local`. The `/bin` tree is included read-only for basic process startup. A disposable Alpine sandbox accepted this policy and blocked an unlisted destination. See [iteration 12](../../docs/iterations/iteration-12.md) for the allow/deny evidence and [the verification policy](../openshell/verification-policy.yaml) for a reproducible network-boundary check. The app needs a real persistent volume for `/var/lib/threadline`; keep that volume host-owned and protected.

The current app API accepts OpenAI-compatible chat completion requests. To mediate the API key outside the sandbox, configure the OpenShell/NemoClaw provider to route the app's inference calls to `https://inference.local/v1` and store the Nebius Token Factory credential in host-managed provider state. The sandbox-side app can use a non-secret placeholder API key because the inference router strips the placeholder and supplies the configured provider credential.

## Local WSL gateway

On this Docker Desktop/WSL setup, the gateway uses bridge networking for the sandbox supervisor. The setting is in `~/.config/openshell/gateway.toml` inside Ubuntu WSL:

```toml
[openshell]
version = 2

[openshell.gateway]
name = 'openshell'
compute_driver = 'docker'

[openshell.drivers.docker]
supervisor_network_mode = 'bridge'
```

The `openshell-gateway` user service is enabled and started. Check it with `systemctl --user status openshell-gateway`, then run `openshell status` and `openshell doctor check`. In this environment, the default supervisor host networking did not reach the gateway; bridge mode selected `host.docker.internal` and allowed the supervisor to fetch policy and connect back. See NVIDIA's [Linux installation guide](https://docs.nvidia.com/openshell/latest/about/installation/) and [Docker runtime reference](https://docs.nvidia.com/openshell/latest/reference/sandbox-compute-drivers) for the supported configuration options.

## Hermes/NemoClaw setup target

1. On a supported Linux host, install OpenShell and NemoClaw from their official installers and configure the Docker compute driver.
2. Create a custom OpenAI-compatible provider in the NemoClaw/OpenShell gateway for the Nebius Token Factory base URL; store the Token Factory key in provider-managed credentials.
3. Use the NemoClaw Hermes workflow (`nemohermes onboard`) to install/configure Hermes with that managed compatible inference endpoint. Hermes accepts an OpenAI-compatible API endpoint.
4. Build the Threadline image, run it in a policy-restricted sandbox with its persistent data volume, and route app inference to `https://inference.local/v1`.
5. Verify with synthetic data: successful Nemotron extraction, blocked arbitrary egress, request receipt matching the minimized source payload, and persistence after a sandbox restart.

The Token Factory provider route is still pending because no Nebius API key is configured in `.env`; no live inference call is claimed. Refer to the current [NVIDIA OpenShell policy docs](https://docs.nvidia.com/openshell/latest/how-it-works/policies/overview), [NemoClaw compatible endpoint guide](https://docs.nvidia.com/nemoclaw/user-guide/hermes/inference/custom-endpoints/set-up-openai-compatible-endpoint), [Hermes provider docs](https://hermes-agent.nousresearch.com/docs/integrations/providers), and the current [Nebius Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference). Provider and CLI commands can change; validate live setup rather than copying assumptions from this note.
