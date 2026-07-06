from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from handai_manufacturer.config import Config, load_config
from handai_manufacturer.jobs import JobManager
from handai_manufacturer.logging_setup import configure_logging
from handai_manufacturer.printers.moonraker import MoonrakerClient, MoonrakerError
from handai_manufacturer.slicers.orca import OrcaSlicerError, result_to_metadata, slice_stl

LOGGER = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def create_app() -> FastAPI:
    config = load_config()
    configure_logging(config)
    config.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="HandAIManufacturer", version="0.1.0")
    app.state.config = config
    app.state.jobs = JobManager(config.data_dir)
    app.state.printer = MoonrakerClient(config)

    static_dir = PACKAGE_DIR / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/status")
    def api_status() -> dict[str, object]:
        return app.state.printer.status()

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        status = app.state.printer.status()
        jobs = app.state.jobs.recent(limit=10)
        gcodes = []
        gcode_error = None
        try:
            gcodes = app.state.printer.list_gcodes()
        except Exception as exc:  # noqa: BLE001 - dashboard should load even if list fails
            gcode_error = str(exc)

        return TEMPLATES.TemplateResponse(
            "index.html",
            {
                "request": request,
                "config": config,
                "printer_status": status,
                "jobs": jobs,
                "gcodes": gcodes[:20] if isinstance(gcodes, list) else [],
                "gcode_error": gcode_error,
            },
        )

    @app.post("/slice-stl")
    async def slice_stl_route(
        stl_file: Annotated[UploadFile, File()],
        profile_id: Annotated[str | None, Form()] = None,
        upload_to_printer: Annotated[bool, Form()] = False,
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

            if upload_to_printer and result.gcode_file:
                upload_result = app.state.printer.upload_gcode(result.gcode_file, start_print=False)
                job.metadata["moonraker_upload"] = upload_result
                job.status = "uploaded"
                app.state.jobs.add_event(
                    job,
                    "gcode_uploaded",
                    {"gcode_file": str(result.gcode_file), "start_print": False},
                )
            elif upload_to_printer and not result.gcode_file:
                app.state.jobs.add_event(
                    job,
                    "upload_skipped",
                    {"reason": "Slicer did not produce a plain .gcode file."},
                )
        except (OrcaSlicerError, MoonrakerError, TimeoutError, OSError) as exc:
            LOGGER.exception("Slice/upload job failed")
            job.status = "failed"
            app.state.jobs.add_event(job, "error", {"message": str(exc)})
        finally:
            app.state.jobs.save(job)

        return RedirectResponse(url="/", status_code=303)

    @app.post("/upload-gcode")
    async def upload_gcode_route(
        gcode_file: Annotated[UploadFile, File()],
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
            upload_result = app.state.printer.upload_gcode(local_path, start_print=False)
            job.metadata["moonraker_upload"] = upload_result
            job.status = "uploaded"
            app.state.jobs.add_event(job, "gcode_uploaded_to_printer", {"start_print": False})
        except (MoonrakerError, OSError) as exc:
            LOGGER.exception("G-code upload failed")
            job.status = "failed"
            app.state.jobs.add_event(job, "error", {"message": str(exc)})
        finally:
            app.state.jobs.save(job)

        return RedirectResponse(url="/", status_code=303)

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
        return RedirectResponse(url="/", status_code=303)

    return app
