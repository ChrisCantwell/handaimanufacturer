from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from handai_manufacturer.config import Config

LOGGER = logging.getLogger(__name__)


class OrcaSlicerError(RuntimeError):
    pass


@dataclass(slots=True)
class SliceResult:
    ok: bool
    command: list[str]
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    output_dir: Path
    output_files: list[Path] = field(default_factory=list)
    gcode_file: Path | None = None
    messages: list[str] = field(default_factory=list)

    @property
    def uploadable(self) -> bool:
        return self.gcode_file is not None and self.gcode_file.suffix.lower() == ".gcode"


def _resolve_existing(path_value: str | Path | None, base_dir: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _profile_paths(config: Config, profile_id: str | None) -> tuple[list[Path], list[Path], list[str]]:
    messages: list[str] = []
    if not profile_id:
        profile_id = config.slicer.default_profile

    profile = config.profiles.get(profile_id, {})
    base_dir = Path.cwd()
    settings: list[Path] = []
    filaments: list[Path] = []

    for key in ("printer", "process"):
        path = _resolve_existing(profile.get(key), base_dir)
        if path and path.exists():
            settings.append(path)
        elif path:
            messages.append(f"Configured {key} profile not found: {path}")

    filament_path = _resolve_existing(profile.get("filament"), base_dir)
    if filament_path and filament_path.exists():
        filaments.append(filament_path)
    elif filament_path:
        messages.append(f"Configured filament profile not found: {filament_path}")

    if not profile:
        messages.append(
            f"Profile '{profile_id}' is not defined. OrcaSlicer will run without explicit profile JSONs."
        )

    return settings, filaments, messages


def find_orca(executable: str) -> str:
    resolved = shutil.which(executable)
    if resolved:
        return resolved
    candidate = Path(executable).expanduser()
    if candidate.exists() and candidate.is_file():
        return str(candidate)
    raise OrcaSlicerError(
        f"OrcaSlicer executable '{executable}' was not found. Install OrcaSlicer or update config."
    )


def slice_stl(config: Config, stl_path: Path, job_dir: Path, profile_id: str | None = None) -> SliceResult:
    executable = find_orca(config.slicer.executable)
    output_dir = job_dir / "slicer-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    settings, filaments, profile_messages = _profile_paths(config, profile_id)

    command = [executable, "--slice", "0", "--outputdir", str(output_dir)]
    if config.slicer.datadir:
        command.extend(["--datadir", str(Path(config.slicer.datadir).expanduser())])
    if settings:
        command.extend(["--load-settings", ";".join(str(path) for path in settings)])
    if filaments:
        command.extend(["--load-filaments", ";".join(str(path) for path in filaments)])
    command.append(str(stl_path))

    stdout_path = job_dir / "slice.stdout.log"
    stderr_path = job_dir / "slice.stderr.log"

    LOGGER.info("Running OrcaSlicer: %s", " ".join(command))
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        completed = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            text=True,
            timeout=config.slicer.timeout_seconds,
            check=False,
        )

    output_files = sorted(
        [
            *output_dir.glob("*.gcode"),
            *output_dir.glob("*.gcode.3mf"),
            *output_dir.glob("*.3mf"),
        ]
    )
    gcode_file = next((path for path in output_files if path.suffix.lower() == ".gcode"), None)

    messages = list(profile_messages)
    if completed.returncode != 0:
        messages.append(f"OrcaSlicer exited with code {completed.returncode}.")
    if not output_files:
        messages.append("No output files were found after slicing.")
    if output_files and not gcode_file:
        messages.append("Slicer output did not include a plain .gcode file for Moonraker upload.")

    return SliceResult(
        ok=completed.returncode == 0 and bool(output_files),
        command=command,
        exit_code=completed.returncode,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_dir=output_dir,
        output_files=output_files,
        gcode_file=gcode_file,
        messages=messages,
    )


def result_to_metadata(result: SliceResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "command": result.command,
        "exit_code": result.exit_code,
        "stdout_path": str(result.stdout_path),
        "stderr_path": str(result.stderr_path),
        "output_dir": str(result.output_dir),
        "output_files": [str(path) for path in result.output_files],
        "gcode_file": str(result.gcode_file) if result.gcode_file else None,
        "uploadable": result.uploadable,
        "messages": result.messages,
    }
