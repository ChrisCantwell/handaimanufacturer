# Architecture Notes

HandAIManufacturer should be built as a set of small adapters around a conservative core.

## Core workflow

```text
STL upload
  -> preflight metadata
  -> slicer adapter
  -> generated G-code
  -> printer adapter
  -> status monitor
  -> job/library log
```

## Proposed modules

```text
handai_manufacturer/
  app.py
  config.py
  database.py
  jobs.py
  library.py
  slicers/
    base.py
    orca.py
  printers/
    base.py
    moonraker.py
  cameras/
    base.py
    rtsp.py
    onvif.py
  ai/
    base.py
    null_provider.py
    codex_cli.py
  static/
  templates/
```

## Adapter boundaries

### Slicers

The core app should not assume OrcaSlicer forever. Orca is the first target because it is installed locally and has CLI slicing support.

Responsibilities:

- Validate executable availability.
- Build command line safely.
- Write logs.
- Return output file paths and parsed metadata where possible.

### Printers

The first printer adapter is Moonraker.

Responsibilities:

- Query printer status.
- List G-code files.
- Upload G-code.
- Start/pause/resume/cancel only when explicitly requested.
- Surface errors clearly.

### Cameras

The first camera adapter should support manual RTSP streams. ONVIF discovery/control can come later.

Responsibilities:

- Store camera definitions without committing credentials.
- Provide preview/snapshot endpoints.
- Save snapshots into job folders.

### AI providers

AI providers should be optional and side-effect limited.

Responsibilities:

- Generate or revise CAD source.
- Preserve prompts and results.
- Never bypass human review.
- Never directly start a print.

## Runtime directories

Local runtime data should be outside the repository or ignored by Git.

Suggested default:

```text
~/.local/share/handai-manufacturer/
  config.local.yaml
  handai.sqlite3
  jobs/
  library/
  logs/
```

For development, `runtime/` inside the repo can be used and ignored.

## Configuration goals

- No hardcoded user home directory.
- No hardcoded printer IP in source code.
- No secrets committed.
- Config file plus environment overrides.

Example:

```yaml
server:
  host: 127.0.0.1
  port: 8765

printer:
  type: moonraker
  url: http://192.168.1.188:7125

slicer:
  type: orca
  executable: orcaslicer

ai:
  enabled: false
  provider: null
```

## Logging doctrine

Every important operation should have structured logs:

- Upload request received.
- File saved.
- Preflight checks.
- Slicer command, redacted if needed.
- Slicer exit code.
- Generated file paths.
- Moonraker upload request/result.
- Print start/pause/cancel request/result.
- Operator confirmation events.
- Camera snapshots.
- Job outcome notes.

When in doubt, log more.