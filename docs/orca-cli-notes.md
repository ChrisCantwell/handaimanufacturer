# OrcaSlicer CLI Notes

OrcaSlicer is the first planned slicer adapter for HandAIManufacturer.

## Adapter responsibilities

- Find the OrcaSlicer executable.
- Verify CLI support.
- Build safe command lines.
- Load printer/process/filament settings.
- Write slicer stdout/stderr to logs.
- Verify output file exists.
- Return generated G-code metadata where possible.

## Expected CLI shape

The exact flags may evolve with OrcaSlicer versions, but the integration is expected to resemble:

```bash
orcaslicer \
  --slice 0 \
  --load-settings "machine.json;process.json" \
  --load-filaments "filament.json" \
  --outputdir ./out \
  model.stl
```

## Configuration

```yaml
slicer:
  type: orca
  executable: orcaslicer
  datadir: null
  profiles_dir: ./profiles
```

## Profile goals

Profiles should be explicit and versioned.

Suggested layout:

```text
profiles/
  printers/
    creality-ender-3-v3-0.4.json
  processes/
    pla-0.20-standard.json
    petg-0.20-standard.json
  filaments/
    hyper-pla-white.json
    generic-petg-black.json
```

## v0.1 profile posture

Start with one trusted PLA workflow. Do not over-optimize early.

Required v0.1 profile:

- Ender-3 V3
- 0.4 mm nozzle
- PLA
- 0.20 mm layer height

PETG can be added after PLA slicing/uploading is boringly reliable.

## Logging fields

Suggested slicer log metadata:

```json
{
  "slicer": "orca",
  "executable": "orcaslicer",
  "version": "detected at runtime",
  "input_file": "source.stl",
  "output_file": "sliced.gcode",
  "profile_ids": ["ender3v3", "pla-0.20-standard", "hyper-pla-white"],
  "exit_code": 0,
  "duration_seconds": 12.34
}
```

## Failure handling

If slicing fails:

- Keep the STL.
- Keep stdout/stderr logs.
- Show a readable error in the UI.
- Do not upload stale or partial G-code.
- Mark the job as `slice_failed`.