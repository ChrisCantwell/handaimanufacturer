from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class JobRecord:
    id: str
    kind: str
    label: str
    created_at: str
    path: str
    status: str = "created"
    events: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_slug(value: str, fallback: str = "job") -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-._")
    return value or fallback


class JobManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.jobs_dir = data_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, label: str, kind: str) -> JobRecord:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = safe_slug(label)
        job_id = f"{timestamp}-{slug}"
        path = self.jobs_dir / job_id
        path.mkdir(parents=True, exist_ok=False)
        record = JobRecord(
            id=job_id,
            kind=kind,
            label=label,
            created_at=utc_now(),
            path=str(path),
        )
        self.add_event(record, "job_created", {"kind": kind, "label": label})
        self.save(record)
        return record

    def add_event(self, record: JobRecord, event_type: str, data: dict[str, Any] | None = None) -> None:
        record.events.append({"time": utc_now(), "type": event_type, "data": data or {}})

    def save(self, record: JobRecord) -> None:
        path = Path(record.path) / "job.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(record), handle, indent=2, sort_keys=True)

    def load(self, job_id: str) -> JobRecord:
        path = self.jobs_dir / job_id / "job.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return JobRecord(**payload)

    def recent(self, limit: int = 20) -> list[JobRecord]:
        records: list[JobRecord] = []
        for job_file in sorted(self.jobs_dir.glob("*/job.json"), reverse=True):
            try:
                with job_file.open("r", encoding="utf-8") as handle:
                    records.append(JobRecord(**json.load(handle)))
            except (OSError, json.JSONDecodeError, TypeError):
                continue
            if len(records) >= limit:
                break
        return records
