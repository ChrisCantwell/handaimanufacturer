# Changelog

All notable project changes should be documented here.

This project follows a practical changelog style: concise release notes, plus enough technical detail to understand what changed and why.

## [Unreleased]

### Added

- Initial FastAPI application package.
- Local dashboard template and CSS.
- Configuration loader using `config.local.yaml`, `HANDAI_CONFIG`, or defaults.
- Job folder creation with `job.json` metadata and event logging.
- Moonraker adapter for status, file listing, G-code upload, and start/pause/resume/cancel methods.
- OrcaSlicer CLI adapter for STL slicing attempts with stdout/stderr capture.
- Explicit print-start confirmation route.

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