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

`threadline-policy.yaml` is the starting policy for placing the Threadline container in an OpenShell sandbox. It grants writes only to `/var/lib/threadline` and `/tmp`, and permits model traffic only to `api.tokenfactory.nebius.com` under `/v1/**` from Python. The `/bin` tree is included read-only for basic process startup. A disposable sandbox allowed the listed host and blocked an unlisted destination. See [iteration 12](../../docs/iterations/iteration-12.md) for the generic allow/deny evidence, [iteration 13](../../docs/iterations/iteration-13.md) for the real Token Factory call, and [the verification policy](../openshell/verification-policy.yaml) for a reproducible network-boundary check. The app needs a real persistent volume for `/var/lib/threadline`; keep that volume host-owned and protected.

The app API accepts OpenAI-compatible chat completion requests. Import [the Nebius provider profile](../openshell/nebius-tokenfactory-profile.yaml), create a provider from the `NEBIUS_API_KEY` environment variable, and attach it to the Threadline sandbox. The app calls `https://api.tokenfactory.nebius.com/v1`; `NEBIUS_API_KEY` inside the sandbox is only an OpenShell placeholder. The gateway substitutes the stored secret only for the declared Token Factory host/path. Do not pass the secret as a sandbox environment value or command-line argument. The smoke requests verified `nvidia/Nemotron-3_5-Lightning` and `nvidia/nemotron-3-super-120b-a12b` in the account's model list.

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

## Add the Nebius credential safely

1. Import the profile: `openshell provider profile import --file infra/openshell/nebius-tokenfactory-profile.yaml`.
2. Load `NEBIUS_API_KEY` into the current shell from your local `.env` without printing it, then create the provider by variable name: `openshell provider create --name nebius-tokenfactory --type nebius-tokenfactory --credential NEBIUS_API_KEY`.
3. Unset the shell variable after provider creation. The key is held by the gateway provider store; the sandbox receives only a placeholder.

For the Windows workspace used during verification, load the CRLF `.env` from WSL with `source <(sed 's/\r$//' /mnt/c/Users/<user>/OneDrive/Desktop/nvidia/.env)`. Never use `--credential NEBIUS_API_KEY=<actual-key>`, `--env NEBIUS_API_KEY=<actual-key>`, or print the key in a command.

## Hermes/NemoClaw setup target

1. On a supported Linux host, install OpenShell and NemoClaw from their official installers and configure the Docker compute driver.
2. Import `infra/openshell/nebius-tokenfactory-profile.yaml`; create provider `nebius-tokenfactory` from `NEBIUS_API_KEY` using `--credential NEBIUS_API_KEY` so the value is read from the shell environment, not process arguments.
3. Build the Threadline image and create a sandbox with `--provider nebius-tokenfactory`, `threadline-policy.yaml`, and `NEBIUS_TOKEN_FACTORY_BASE_URL=https://api.tokenfactory.nebius.com/v1`.
4. Confirm inference with the synthetic preview-and-scan flow. Reuse `infra/openshell/provider-smoke.py` for a minimal provider check.
5. Verify the policy still blocks arbitrary egress and that the local egress receipt matches the minimized request.

This verified OpenShell 0.1.6 workflow uses direct endpoint-bound credentials, not `inference.local` (that command is not present in the installed CLI version). Refer to NVIDIA's [OpenShell provider profiles](https://docs.nvidia.com/openshell/latest/how-it-works/providers/profiles), [inference routing](https://docs.nvidia.com/openshell/latest/sandboxes/inference-routing), [Hermes provider docs](https://hermes-agent.nousresearch.com/docs/integrations/providers), and the [Nebius Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference). Provider and CLI commands can change; validate live setup rather than copying assumptions from this note.
