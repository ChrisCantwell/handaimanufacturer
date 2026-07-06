from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from handai_manufacturer import __version__
from handai_manufacturer.config import load_config
from handai_manufacturer.jobs import JobManager, JobRecord
from handai_manufacturer.logging_setup import configure_logging
from handai_manufacturer.printers.moonraker import MoonrakerClient, MoonrakerError
from handai_manufacturer.slicers.orca import OrcaSlicerError, result_to_metadata, slice_stl

LOGGER = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def notice_redirect(message: str, level: str = "success", job_id: str | None = None) -> RedirectResponse:
    payload = {"notice": message, "notice_level": level}
    if job_id:
        payload["job_id"] = job_id
    query = urlencode(payload)
    return RedirectResponse(url=f"/?{query}", status_code=303)


def human_size(value: Any) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return ""

    units = ["B", "KB", "MB", "GB"]
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    if index == 0:
        return f"{int(size)} {units[index]}"
    return f"{size:.1f} {units[index]}"


def prepare_gcodes(gcodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for item in gcodes:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", ""))
        if path and not path.lower().endswith(".gcode"):
            continue
        enriched = dict(item)
        enriched["human_size"] = human_size(item.get("size"))
        prepared.append(enriched)

    return sorted(
        prepared,
        key=lambda item: float(item.get("modified", item.get("mtime", 0)) or 0),
        reverse=True,
    )


def summarize_job(job: JobRecord | None) -> dict[str, Any] | None:
    if not job:
        return None

    startable_filename = None
    remote_name = None
    generated_gcode = None
    source_stl = None

    if job.artifacts.get("source_stl"):
        source_stl = Path(job.artifacts["source_stl"]).name
    if job.artifacts.get("gcode"):
        generated_gcode = Path(job.artifacts["gcode"]).name

    slice_meta = job.metadata.get("slice", {}) if isinstance(job.metadata, dict) else {}
    if isinstance(slice_meta, dict) and slice_meta.get("gcode_file"):
        generated_gcode = Path(str(slice_meta["gcode_file"])).name

    for event in reversed(job.events):
        data = event.get("data", {}) if isinstance(event, dict) else {}
        if not isinstance(data, dict):
            continue
        if data.get("remote_name"):
            remote_name = str(data["remote_name"])
            startable_filename = remote_name
            break
        if data.get("gcode_file"):
            startable_filename = Path(str(data["gcode_file"])).name

    if not remote_name and job.metadata.get("moonraker_upload"):
        remote_name = startable_filename or generated_gcode

    return {
        "id": job.id,
        "kind": job.kind,
        "label": job.label,
        "status": job.status,
        "created_at": job.created_at,
        "source_stl": source_stl,
        "generated_gcode": generated_gcode,
        "remote_name": remote_name,
        "startable_filename": startable_filename,
        "events_count": len(job.events),
    }


def _printer_file_paths(printer: MoonrakerClient) -> list[str]:
    files = printer.list_gcodes()
    paths: list[str] = []
    for item in files:
        if isinstance(item, dict) and item.get("path"):
            paths.append(str(item["path"]))
    return paths


def _matching_printer_files(printer: MoonrakerClient, remote_name: str) -> list[str]:
    remote_basename = Path(remote_name).name
    matches: list[str] = []
    for path in _printer_file_paths(printer):
        if path == remote_name or Path(path).name == remote_basename:
            matches.append(path)
    return matches


def _record_duplicate_block(job_manager: JobManager, job: JobRecord, remote_name: str, matches: list[str]) -> None:
    job.status = "upload_blocked_duplicate"
    job_manager.add_event(
        job,
        "upload_blocked_duplicate",
        {"remote_name": remote_name, "matches": matches},
    )
    job_manager.save(job)


def _duplicate_message(remote_name: str, matches: list[str]) -> str:
    preview = ", ".join(matches[:3])
    if len(matches) > 3:
        preview += f", plus {len(matches) - 3} more"
    return (
        f"Upload blocked: '{remote_name}' appears to already exist on the printer "
        f"as {preview}. Check the overwrite box if you want to replace it."
    )


def create_app() -> FastAPI:
    config = load_config()
    configure_logging(config)
    config.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="HandAIManufacturer", version=__version__)
    app.state.config = config
    app.state.jobs = JobManager(config.data_dir)
    app.state.printer = MoonrakerClient(config.printer)

    static_dir = PACKAGE_DIR / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/status")
    def api_status() -> dict[str, object]:
        return app.state.printer.status()

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        status = app.state.printer.status()
        jobs = app.state.jobs.recent(limit=10)
        gcodes: list[dict[str, Any]] = []
        gcode_error = None
        try:
            gcodes = prepare_gcodes(app.state.printer.list_gcodes())
        except Exception as exc:  # noqa: BLE001 - dashboard should load even if list fails
            gcode_error = str(exc)

        selected_job = None
        requested_job_id = request.query_params.get("job_id")
        if requested_job_id:
            try:
                selected_job = app.state.jobs.load(requested_job_id)
            except Exception as exc:  # noqa: BLE001 - stale query params should not break dashboard
                LOGGER.warning("Could not load requested job %s: %s", requested_job_id, exc)
        if selected_job is None and jobs:
            selected_job = jobs[0]

        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "app_version": __version__,
                "config": config,
                "printer_status": status,
                "jobs": jobs,
                "latest_job": summarize_job(selected_job),
                "gcodes": gcodes[:30] if isinstance(gcodes, list) else [],
                "gcode_error": gcode_error,
                "notice": request.query_params.get("notice"),
                "notice_level": request.query_params.get("notice_level", "info"),
            },
        )

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    def job_detail(request: Request, job_id: str) -> HTMLResponse:
        try:
            job = app.state.jobs.load(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

        return TEMPLATES.TemplateResponse(
            request,
            "job_detail.html",
            {
                "app_version": __version__,
                "job": job,
                "summary": summarize_job(job),
                "metadata_json": json.dumps(job.metadata, indent=2, sort_keys=True),
                "events_json": json.dumps(job.events, indent=2, sort_keys=True),
                "artifacts_json": json.dumps(job.artifacts, indent=2, sort_keys=True),
            },
        )

    @app.post("/slice-stl")
    async def slice_stl_route(
        stl_file: Annotated[UploadFile, File()],
        profile_id: Annotated[str | None, Form()] = None,
        upload_to_printer: Annotated[bool, Form()] = False,
        overwrite_confirmed: Annotated[bool, Form()] = False,
    ) -> RedirectResponse:
        if not stl_file.filename or not stl_file.filename.lower().endswith(".stl"):
            raise HTTPException(status_code=400, detail="Upload must be an .stl file.")

        job = app.state.jobs.create_job(stl_file.filename, kind="slice_stl")
        job_dir = Path(job.path)
        source_path = job_dir / "source.stl"
        with source_path.open("wb") as handle:
            shutil.copyfileobj(stl_file.file, handle)

        job.artifacts["source_stl"] = str(source_path)
        app.state.jobs.add_event(job, "stl_uploaded", {"filename": stl_file.filename})

        try:
            result = slice_stl(config, source_path, job_dir, profile_id=profile_id)
            job.metadata["slice"] = result_to_metadata(result)
            job.status = "sliced" if result.ok else "slice_failed"
            app.state.jobs.add_event(job, "slice_finished", job.metadata["slice"])

            if not result.ok:
                app.state.jobs.save(job)
                return notice_redirect(
                    f"Slice failed for '{stl_file.filename}'. Logs were saved in job {job.id}.",
                    "error",
                    job.id,
                )

            if upload_to_printer and result.gcode_file:
                remote_name = result.gcode_file.name
                try:
                    matches = _matching_printer_files(app.state.printer, remote_name)
                except Exception as exc:  # noqa: BLE001 - safest behavior is no upload unless confirmed
                    app.state.jobs.add_event(
                        job,
                        "duplicate_check_failed",
                        {"remote_name": remote_name, "error": str(exc)},
                    )
                    if not overwrite_confirmed:
                        job.status = "upload_blocked_duplicate_check_failed"
                        app.state.jobs.save(job)
                        return notice_redirect(
                            f"Sliced '{stl_file.filename}', but upload was blocked because printer files could not be checked for duplicates: {exc}",
                            "warning",
                            job.id,
                        )
                    matches = []

                if matches and not overwrite_confirmed:
                    _record_duplicate_block(app.state.jobs, job, remote_name, matches)
                    return notice_redirect(_duplicate_message(remote_name, matches), "warning", job.id)

                upload_result = app.state.printer.upload_gcode(result.gcode_file, start_print=False)
                job.metadata["moonraker_upload"] = upload_result
                job.status = "uploaded"
                app.state.jobs.add_event(
                    job,
                    "gcode_uploaded",
                    {
                        "gcode_file": str(result.gcode_file),
                        "remote_name": remote_name,
                        "start_print": False,
                        "overwrite_confirmed": overwrite_confirmed,
                        "previous_matches": matches,
                    },
                )
                app.state.jobs.save(job)
                if matches:
                    return notice_redirect(
                        f"Sliced and uploaded '{remote_name}' to the printer after overwrite confirmation.",
                        "success",
                        job.id,
                    )
                return notice_redirect(
                    f"Sliced and uploaded '{remote_name}' to the printer.", "success", job.id
                )

            if upload_to_printer and not result.gcode_file:
                app.state.jobs.add_event(
                    job,
                    "upload_skipped",
                    {"reason": "Slicer did not produce a plain .gcode file."},
                )
                job.status = "sliced_no_uploadable_gcode"
                app.state.jobs.save(job)
                return notice_redirect(
                    f"Sliced '{stl_file.filename}', but no plain .gcode file was found to upload.",
                    "warning",
                    job.id,
                )

            app.state.jobs.save(job)
            return notice_redirect(f"Sliced '{stl_file.filename}'.", "success", job.id)
        except (OrcaSlicerError, MoonrakerError, TimeoutError, OSError) as exc:
            LOGGER.exception("Slice/upload job failed")
            job.status = "failed"
            app.state.jobs.add_event(job, "error", {"message": str(exc)})
            app.state.jobs.save(job)
            return notice_redirect(
                f"Slice/upload failed for '{stl_file.filename}': {exc}", "error", job.id
            )

    @app.post("/upload-gcode")
    async def upload_gcode_route(
        gcode_file: Annotated[UploadFile, File()],
        overwrite_confirmed: Annotated[bool, Form()] = False,
    ) -> RedirectResponse:
        if not gcode_file.filename or not gcode_file.filename.lower().endswith(".gcode"):
            raise HTTPException(status_code=400, detail="Upload must be a .gcode file.")

        job = app.state.jobs.create_job(gcode_file.filename, kind="upload_gcode")
        job_dir = Path(job.path)
        local_path = job_dir / gcode_file.filename
        with local_path.open("wb") as handle:
            shutil.copyfileobj(gcode_file.file, handle)
        job.artifacts["gcode"] = str(local_path)
        app.state.jobs.add_event(job, "gcode_uploaded_to_app", {"filename": gcode_file.filename})

        try:
            remote_name = local_path.name
            try:
                matches = _matching_printer_files(app.state.printer, remote_name)
            except Exception as exc:  # noqa: BLE001 - safest behavior is no upload unless confirmed
                app.state.jobs.add_event(
                    job,
                    "duplicate_check_failed",
                    {"remote_name": remote_name, "error": str(exc)},
                )
                if not overwrite_confirmed:
                    job.status = "upload_blocked_duplicate_check_failed"
                    app.state.jobs.save(job)
                    return notice_redirect(
                        f"Upload blocked because printer files could not be checked for duplicates: {exc}",
                        "warning",
                        job.id,
                    )
                matches = []

            if matches and not overwrite_confirmed:
                _record_duplicate_block(app.state.jobs, job, remote_name, matches)
                return notice_redirect(_duplicate_message(remote_name, matches), "warning", job.id)

            upload_result = app.state.printer.upload_gcode(local_path, start_print=False)
            job.metadata["moonraker_upload"] = upload_result
            job.status = "uploaded"
            app.state.jobs.add_event(
                job,
                "gcode_uploaded_to_printer",
                {
                    "remote_name": remote_name,
                    "start_print": False,
                    "overwrite_confirmed": overwrite_confirmed,
                    "previous_matches": matches,
                },
            )
            app.state.jobs.save(job)
            if matches:
                return notice_redirect(
                    f"Uploaded '{remote_name}' to the printer after overwrite confirmation.",
                    "success",
                    job.id,
                )
            return notice_redirect(f"Uploaded '{remote_name}' to the printer.", "success", job.id)
        except (MoonrakerError, OSError) as exc:
            LOGGER.exception("G-code upload failed")
            job.status = "failed"
            app.state.jobs.add_event(job, "error", {"message": str(exc)})
            app.state.jobs.save(job)
            return notice_redirect(f"G-code upload failed for '{gcode_file.filename}': {exc}", "error", job.id)

    @app.post("/start-print")
    async def start_print_route(
        filename: Annotated[str, Form()],
        bed_clear_confirmed: Annotated[bool, Form()] = False,
        filament_confirmed: Annotated[bool, Form()] = False,
    ) -> RedirectResponse:
        if config.safety.require_start_confirmation:
            if not bed_clear_confirmed or not filament_confirmed:
                raise HTTPException(
                    status_code=400,
                    detail="Starting a print requires bed-clear and filament confirmations.",
                )
        try:
            app.state.printer.start_print(filename)
        except MoonrakerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return notice_redirect(f"Print start requested for '{filename}'.", "success")

    return app
