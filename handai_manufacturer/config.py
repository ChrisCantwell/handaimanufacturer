from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False


@dataclass(slots=True)
class ApplicationConfig:
    data_dir: Path = Path("~/.local/share/handai-manufacturer")
    log_level: str = "info"


@dataclass(slots=True)
class PrinterConfig:
    type: str = "moonraker"
    name: str = "Printer"
    url: str = "http://127.0.0.1:7125"
    auto_start_after_upload: bool = False
    timeout_seconds: float = 10.0


@dataclass(slots=True)
class SlicerConfig:
    type: str = "orca"
    executable: str = "orcaslicer"
    datadir: str | None = None
    profiles_dir: Path = Path("./profiles")
    default_profile: str = "ender3v3-pla-020"
    timeout_seconds: int = 1800


@dataclass(slots=True)
class CameraConfig:
    id: str
    name: str
    type: str = "rtsp"
    enabled: bool = False
    url: str | None = None


@dataclass(slots=True)
class AIConfig:
    enabled: bool = False
    provider: str | None = None
    codex_cli: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SafetyConfig:
    require_start_confirmation: bool = True
    require_bed_clear_confirmation: bool = True
    allow_arbitrary_gcode: bool = False


@dataclass(slots=True)
class Config:
    server: ServerConfig = field(default_factory=ServerConfig)
    app: ApplicationConfig = field(default_factory=ApplicationConfig)
    printer: PrinterConfig = field(default_factory=PrinterConfig)
    slicer: SlicerConfig = field(default_factory=SlicerConfig)
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    cameras: list[CameraConfig] = field(default_factory=list)
    ai: AIConfig = field(default_factory=AIConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    source_path: Path | None = None

    @property
    def data_dir(self) -> Path:
        return self.app.data_dir.expanduser().resolve()


DEFAULTS: dict[str, Any] = {
    "server": {"host": "127.0.0.1", "port": 8765, "debug": False},
    "app": {"data_dir": "~/.local/share/handai-manufacturer", "log_level": "info"},
    "printer": {
        "type": "moonraker",
        "name": "Printer",
        "url": "http://127.0.0.1:7125",
        "auto_start_after_upload": False,
        "timeout_seconds": 10.0,
    },
    "slicer": {
        "type": "orca",
        "executable": "orcaslicer",
        "datadir": None,
        "profiles_dir": "./profiles",
        "default_profile": "ender3v3-pla-020",
        "timeout_seconds": 1800,
    },
    "profiles": {},
    "cameras": [],
    "ai": {"enabled": False, "provider": None, "codex_cli": {}},
    "safety": {
        "require_start_confirmation": True,
        "require_bed_clear_confirmation": True,
        "allow_arbitrary_gcode": False,
    },
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file {path} must contain a YAML object at the top level.")
    return payload


def _config_path() -> Path | None:
    env_path = os.environ.get("HANDAI_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    local_path = Path("config.local.yaml")
    if local_path.exists():
        return local_path

    example_path = Path("config.example.yaml")
    if example_path.exists():
        return example_path

    return None


def _path(value: str | Path | None, default: Path) -> Path:
    if value is None:
        return default
    return Path(value).expanduser()


def build_config(raw: dict[str, Any], source_path: Path | None = None) -> Config:
    data = deep_merge(DEFAULTS, raw)

    server = ServerConfig(**data["server"])
    app_data = dict(data["app"])
    app_data["data_dir"] = _path(app_data.get("data_dir"), ApplicationConfig.data_dir)
    app = ApplicationConfig(**app_data)

    printer = PrinterConfig(**data["printer"])

    slicer_data = dict(data["slicer"])
    slicer_data["profiles_dir"] = _path(slicer_data.get("profiles_dir"), SlicerConfig.profiles_dir)
    slicer = SlicerConfig(**slicer_data)

    cameras = [CameraConfig(**camera) for camera in data.get("cameras", [])]
    ai = AIConfig(**data.get("ai", {}))
    safety = SafetyConfig(**data.get("safety", {}))

    return Config(
        server=server,
        app=app,
        printer=printer,
        slicer=slicer,
        profiles=data.get("profiles", {}),
        cameras=cameras,
        ai=ai,
        safety=safety,
        source_path=source_path,
    )


def load_config() -> Config:
    path = _config_path()
    raw = _load_yaml(path) if path else {}
    return build_config(raw, source_path=path)
