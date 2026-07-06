# Changelog

All notable project changes should be documented here.

This project follows a practical changelog style: concise release notes, plus enough technical detail to understand what changed and why.

## [Unreleased]

### Planned

- Job log file browser links.
- Better OrcaSlicer profile handling.
- Camera preview groundwork.

## [0.1.1] - 2026-07-06

### Added

- Version indicator in the application header.
- Package and FastAPI application version bumped to `0.1.1`.
- Last Operation card showing recent job status, source STL, generated G-code, printer destination, and job ID.
- Job detail pages at `/jobs/{job_id}` with artifacts, metadata, and event logs.
- Manual printer status refresh link.
- Human-readable printer file sizes.
- Printer-file Use buttons that populate the Start Print filename field.
- Selected-file display in the Start Print card.

### Changed

- Recent jobs are now clickable.
- Printer G-code list filters to `.gcode` files and attempts to sort newest first when timestamp metadata is available.
- Slice/upload redirects carry job IDs so the dashboard can summarize what just happened.

## [0.1.0] - 2026-07-06

### Added

- Initial FastAPI application package.
- Local dashboard template and CSS.
- Configuration loader using `config.local.yaml`, `HANDAI_CONFIG`, or defaults.
- Job folder creation with `job.json` metadata and event logging.
- Moonraker adapter for status, file listing, G-code upload, and start/pause/resume/cancel methods.
- OrcaSlicer CLI adapter for STL slicing attempts with stdout/stderr capture.
- Explicit print-start confirmation route.
- Visible success/warning/error notices after slice, upload, duplicate block, and print-start requests.
- Duplicate filename detection before uploading G-code to the printer.
- Overwrite confirmation checkbox for sliced uploads and existing G-code uploads.
- Printer-file selection controls that populate the Start Print filename field without copy/paste.

### Changed

- Upload routes now block possible overwrites unless the operator explicitly confirms overwrite.
- Printer G-code file list now includes a selection column for Start Print workflow.

### Known limitations

- OrcaSlicer profile JSONs are not yet included.
- Slicing behavior depends on local OrcaSlicer CLI/profile setup.
- Camera support is documented but not implemented.
- AI provider layer is documented but not implemented.
- No automated tests yet.

## [0.0.0] - 2026-07-05

### Added

- Repository initialized with planning documentation.
- MIT license.
- Early-stage contribution policy.
- Local-first manufacturing workflow goals.
- Staged roadmap for slicer/upload/library/camera/AI integration.
- Safety-first default posture for print start actions.