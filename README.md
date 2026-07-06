# HandAIManufacturer

HandAIManufacturer is a local-first web interface for small-scale 3D printing workflows.

The near-term goal is intentionally modest: upload an STL, slice it locally with OrcaSlicer, send the resulting G-code to a Moonraker/Klipper printer, monitor the job, and keep a useful record of what happened.

The long-term goal is more ambitious: a local manufacturing notebook with part history, print outcomes, camera monitoring, and optional AI-assisted design/revision through provider adapters such as Codex CLI.

## Project principles

- **Local-first by default.** The app should bind to `127.0.0.1` unless explicitly configured otherwise.
- **No secrets in the repo.** Printer URLs, camera credentials, AI tokens, and local paths belong in local config files or environment variables.
- **AI-ready, not AI-dependent.** Core slicing, upload, monitoring, and logging must work without any AI provider.
- **Human confirmation before hot machinery moves.** Slicing and uploading may be automated; starting a print should require explicit confirmation by default.
- **Auditable source over mystery meshes.** AI-designed parts should preserve editable CAD source, prompts, measurements, generated STL, sliced G-code, and fit notes.
- **Boring logs beat heroic memory.** Every slice/upload/print attempt should leave enough detail to diagnose failures later.

## Initial target stack

- Python backend, likely FastAPI
- Simple local web frontend
- SQLite for job/library metadata
- OrcaSlicer CLI for slicing
- Moonraker HTTP API for printer upload/status/control
- Manual RTSP camera URL support before ONVIF discovery
- Optional Codex CLI provider later for AI design assistance

## Roadmap snapshot

1. **v0.1 Local Print Dock** — upload STL, slice with Orca, save G-code, upload to Moonraker, show printer status, log everything.
2. **v0.2 Print Library** — part records, version history, fit notes, material/profile history, job folders.
3. **v0.3 Camera Monitoring** — RTSP preview, snapshots stored with jobs, ONVIF discovery later.
4. **v0.4 Safer Print Control** — start/pause/cancel, confirmation checklist, printer/camera dashboard.
5. **v0.5 AI Design Prep** — OpenSCAD/CadQuery conventions, prompt templates, source-first artifact storage.
6. **v0.6 Codex Provider** — optional Codex CLI integration for design generation and revision.

See [`docs/roadmap.md`](docs/roadmap.md) for the working roadmap.

## Status

This repository is in planning/scaffolding stage. Expect the design to evolve quickly.

## Safety note

This project is intended to control equipment that can move, heat up, and run unattended if misconfigured. Do not expose the app directly to the public internet. Auto-start printing should remain disabled unless the operator deliberately enables it.