# Printer Safety Notes

HandAIManufacturer should make printing easier without making unsafe behavior easier.

## Default safety posture

- Bind the web server to localhost by default.
- Do not auto-start prints after slicing/uploading.
- Require explicit confirmation before starting a print.
- Make pause/cancel easy to reach in the dashboard.
- Preserve operator checklists and logs.

## Start print checklist

Before enabling a remote start, the UI should ask the operator to confirm:

- Print bed is clear.
- Correct build plate is installed.
- Correct filament is loaded.
- Filament path is not tangled or restricted.
- No tools, clips, scraps, or failed print debris are on the bed.
- Camera view, if configured, matches the expected printer.

## Things software cannot assume

- Bed is actually clear.
- First layer is adhering.
- Filament is dry.
- Nozzle is clean.
- Part orientation is sensible.
- Supports are adequate.
- Material profile is safe for the loaded filament.

## High-risk operations

These should be gated and logged:

- Start print.
- Resume print.
- Run arbitrary G-code.
- Heat nozzle or bed outside a print.
- Disable safety checks.
- Change printer URL.
- Expose app beyond localhost.

## Camera use

Camera monitoring improves confidence but does not remove operator responsibility.

Useful camera checkpoints:

- Before-print bed snapshot.
- First-layer snapshot.
- Periodic progress snapshots.
- Failure evidence snapshots.

## Public release warning

The project README and docs should repeatedly warn users not to expose the app directly to the internet. A local tool that can heat and move machinery should not be treated like an ordinary web app.