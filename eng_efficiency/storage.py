from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ProjectStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"projects": []})

    def _read(self) -> dict[str, object]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"projects": []}

    def _write(self, payload: dict[str, object]) -> None:
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    def list_projects(self) -> list[dict[str, object]]:
        projects = self._read().get("projects", [])
        ordered = sorted(
            projects,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )
        return deepcopy(ordered)

    def get_project(self, project_id: str) -> dict[str, object] | None:
        for project in self._read().get("projects", []):
            if project.get("id") == project_id:
                return deepcopy(project)
        return None

    def upsert_project(self, payload: dict[str, object]) -> dict[str, object]:
        data = self._read()
        projects = data.setdefault("projects", [])

        project_id = str(payload.get("id") or "")
        existing = None
        for index, project in enumerate(projects):
            if project.get("id") == project_id and project_id:
                existing = (index, project)
                break

        now = _utc_now()
        if existing is None:
            project = {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "plan_inputs": {},
                "plan_result": None,
                "fact_inputs": {},
                "fact_result": None,
            }
        else:
            project = deepcopy(existing[1])

        for key, value in payload.items():
            if key == "id" and not value:
                continue
            project[key] = value
        project["updated_at"] = now

        if existing is None:
            projects.append(project)
        else:
            projects[existing[0]] = project

        self._write(data)
        return deepcopy(project)
