# HandAIManufacturer Roadmap

This roadmap is intentionally staged. The project should become useful before it becomes clever.

## v0.1 — Local Print Dock

Goal: replace the Windows/Creality Print dependency for routine jobs by providing a local Linux web interface around OrcaSlicer and Moonraker.

### Scope

- Local web UI bound to localhost by default.
- Upload STL.
- Choose printer/material/process profile.
- Slice with OrcaSlicer CLI.
- Save generated G-code and slice logs.
- Upload G-code to Moonraker.
- Display printer status.
- Write detailed job metadata.

### Non-goals

- No AI design generation.
- No automatic print start by default.
- No public network exposure.
- No complex user accounts.
- No camera automation yet.

## v0.2 — Print Library

Goal: turn ad-hoc print attempts into a useful manufacturing memory.

### Scope

- Part records.
- Version history.
- Job folders.
- Fit-test notes.
- Material/profile history.
- Outcome labels: success, failed, warped, wrong dimension, poor adhesion, etc.
- Links between source CAD/STL/G-code/print result.

## v0.3 — Camera Monitoring

Goal: make the dashboard useful away from the printer.

### Scope

- Manual RTSP camera URL configuration.
- Live preview on dashboard.
- Snapshot capture into job folder.
- Bed-clear snapshot before print start.
- First-layer check snapshot.

### Later camera work

- ONVIF discovery.
- Multiple cameras.
- Snapshot comparison.
- Timelapse support.
- Failure detection hooks.

## v0.4 — Safer Print Control

Goal: controlled remote operation without pretending the machine is safe to run blindly.

### Scope

- Start/pause/resume/cancel through Moonraker.
- Explicit start checklist.
- Bed clear / filament loaded / correct build plate confirmation.
- Side-by-side printer status and camera view.
- Better error surfaces and logs.

## v0.5 — AI Design Prep

Goal: prepare the data model and artifact rules before wiring in AI.

### Scope

- Source-first CAD conventions.
- OpenSCAD and/or CadQuery project layout.
- Prompt/measurement records.
- Revision notes.
- Design request templates.
- Clear separation between AI proposal and approved manufacturing job.

## v0.6 — Codex Provider

Goal: optional AI design/revision support through Codex CLI.

### Scope

- Detect Codex CLI availability.
- Use external Codex authentication; do not manage OAuth directly in HandAIManufacturer initially.
- Generate editable CAD source first.
- Store prompts, outputs, and revision rationale.
- Require human review before slicing AI-generated designs.

## Future ideas

- Multi-printer support.
- Profile tuning notebook.
- Filament inventory.
- QR labels for printed parts.
- Phone-friendly dashboard.
- Telegram/OpenClaw notification bridge.
- HandAIStack Core integration if the project ever gains a WordPress/public publishing surface.