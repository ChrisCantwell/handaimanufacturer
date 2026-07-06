# Security Policy

HandAIManufacturer is intended to operate local manufacturing equipment. Treat it as safety-sensitive software.

## Supported posture

The default supported deployment is:

- Local machine only
- Bound to `127.0.0.1`
- No direct public internet exposure
- No unauthenticated remote access
- No automatic print start unless explicitly enabled

## Secrets and credentials

Do not commit:

- Moonraker API keys or printer credentials
- Camera usernames/passwords
- RTSP URLs containing credentials
- AI provider API keys
- OAuth tokens
- Local machine paths that reveal private filesystem layout unnecessarily

Use local configuration files excluded by `.gitignore`, environment variables, or the host operating system's secret storage.

## Dangerous actions

The following actions should require explicit operator confirmation by default:

- Starting a print
- Resuming a paused print
- Heating nozzle or bed outside an active print workflow
- Running arbitrary G-code
- Deleting job/library records
- Exposing the web UI beyond localhost

## Network guidance

Do not expose HandAIManufacturer directly to the public internet. If remote access is needed, use a trusted VPN, SSH tunnel, or another access-controlled private channel.

## Reporting vulnerabilities

Until a formal process exists, open a GitHub issue with non-sensitive details. Do not post secrets, private IPs, tokens, or camera credentials in public issues.

## Operator reminder

Software cannot verify that the print bed is clear, the correct filament is loaded, the nozzle is clean, or the surrounding area is safe unless appropriate sensors/cameras are configured and checked. The operator remains responsible for final confirmation.