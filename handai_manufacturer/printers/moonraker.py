from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from handai_manufacturer.config import PrinterConfig

LOGGER = logging.getLogger(__name__)


class MoonrakerError(RuntimeError):
    pass


class MoonrakerClient:
    def __init__(self, config: PrinterConfig):
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        url = self._url(path)
        LOGGER.debug("Moonraker GET %s", url)
        response = self.session.get(url, timeout=self.config.timeout_seconds, **kwargs)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise MoonrakerError(str(payload["error"]))
        return payload

    def _post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        url = self._url(path)
        LOGGER.debug("Moonraker POST %s", url)
        response = self.session.post(url, timeout=self.config.timeout_seconds, **kwargs)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise MoonrakerError(str(payload["error"]))
        return payload

    def server_info(self) -> dict[str, Any]:
        return self._get("/server/info")

    def printer_info(self) -> dict[str, Any]:
        return self._get("/printer/info")

    def status(self) -> dict[str, Any]:
        try:
            server = self.server_info()
            printer = self.printer_info()
            objects = self._get(
                "/printer/objects/query?print_stats&extruder&heater_bed&display_status"
            )
            return {
                "ok": True,
                "server": server.get("result", server),
                "printer": printer.get("result", printer),
                "objects": objects.get("result", objects),
            }
        except Exception as exc:  # noqa: BLE001 - status endpoint should not crash dashboard
            LOGGER.warning("Printer status check failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    def list_gcodes(self) -> list[dict[str, Any]]:
        payload = self._get("/server/files/list", params={"root": "gcodes"})
        result = payload.get("result", [])
        if not isinstance(result, list):
            raise MoonrakerError("Unexpected file list response from Moonraker.")
        return result

    def upload_gcode(
        self,
        local_path: Path,
        remote_name: str | None = None,
        start_print: bool = False,
    ) -> dict[str, Any]:
        if local_path.suffix.lower() != ".gcode":
            raise MoonrakerError("Moonraker upload currently expects a .gcode file.")

        remote_name = remote_name or local_path.name
        LOGGER.info("Uploading G-code to Moonraker: %s -> %s", local_path, remote_name)
        with local_path.open("rb") as handle:
            files = {"file": (remote_name, handle, "text/plain")}
            data = {"root": "gcodes", "path": remote_name, "print": "true" if start_print else "false"}
            return self._post("/server/files/upload", data=data, files=files)

    def start_print(self, filename: str) -> dict[str, Any]:
        if not filename.strip():
            raise MoonrakerError("A filename is required to start a print.")
        LOGGER.warning("Starting print through Moonraker: %s", filename)
        return self._post("/printer/print/start", json={"filename": filename})

    def pause_print(self) -> dict[str, Any]:
        return self._post("/printer/print/pause")

    def resume_print(self) -> dict[str, Any]:
        return self._post("/printer/print/resume")

    def cancel_print(self) -> dict[str, Any]:
        return self._post("/printer/print/cancel")
