from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from eng_efficiency.calculator import CalculationError, calculate_fact, calculate_plan
from eng_efficiency.runtime import projects_storage_path, workbook_path
from eng_efficiency.statistics import build_statistics
from eng_efficiency.storage import ProjectStore
from eng_efficiency.workbook import WorkbookModel, load_workbook_model


def _project_summary(project: dict[str, object]) -> dict[str, object]:
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "code": project.get("code"),
        "project_group": project.get("project_group"),
        "stage": project.get("stage"),
        "updated_at": project.get("updated_at"),
        "plan_score": project.get("plan_result", {}).get("total_score") if project.get("plan_result") else None,
        "fact_score": project.get("fact_result", {}).get("total_score") if project.get("fact_result") else None,
    }


def _validate_metadata(payload: dict[str, object]) -> list[str]:
    required_fields = {
        "name": "Наименование проекта",
        "code": "Код проекта",
        "stage": "Стадия",
        "start_date": "Дата начала",
        "end_date": "Дата окончания",
        "project_manager": "Руководитель проекта",
        "chief_engineer": "ГИП",
        "design_lead": "Ответственный за проектирование",
    }
    errors = []
    for field, label in required_fields.items():
        if not str(payload.get(field) or "").strip():
            errors.append(f"Поле '{label}' обязательно.")
    return errors


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        WORKBOOK_PATH=str(workbook_path()),
        STORAGE_PATH=str(projects_storage_path()),
    )
    if test_config:
        app.config.update(test_config)

    workbook_model: WorkbookModel = load_workbook_model(Path(app.config["WORKBOOK_PATH"]))
    store = ProjectStore(Path(app.config["STORAGE_PATH"]))

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/config")
    def config():
        return jsonify(workbook_model.to_dict())

    @app.get("/api/projects")
    def list_projects():
        projects = [_project_summary(project) for project in store.list_projects()]
        return jsonify({"projects": projects})

    @app.get("/api/projects/<project_id>")
    def get_project(project_id: str):
        project = store.get_project(project_id)
        if not project:
            return jsonify({"error": "Проект не найден."}), 404
        return jsonify(project)

    @app.post("/api/projects")
    def save_project():
        payload = request.get_json(silent=True) or {}
        errors = _validate_metadata(payload)
        if errors:
            return jsonify({"error": "Ошибка валидации.", "details": errors}), 400

        project_payload = {
            "id": payload.get("id"),
            "name": str(payload.get("name", "")).strip(),
            "code": str(payload.get("code", "")).strip(),
            "project_group": str(payload.get("project_group", "")).strip(),
            "stage": str(payload.get("stage", "")).strip(),
            "start_date": str(payload.get("start_date", "")).strip(),
            "end_date": str(payload.get("end_date", "")).strip(),
            "project_manager": str(payload.get("project_manager", "")).strip(),
            "chief_engineer": str(payload.get("chief_engineer", "")).strip(),
            "design_lead": str(payload.get("design_lead", "")).strip(),
        }

        existing = store.get_project(str(payload.get("id") or ""))
        if existing:
            project_payload["plan_inputs"] = existing.get("plan_inputs", {})
            project_payload["plan_result"] = existing.get("plan_result")
            project_payload["fact_inputs"] = existing.get("fact_inputs", {})
            project_payload["fact_result"] = existing.get("fact_result")

        project = store.upsert_project(project_payload)
        return jsonify(project)

    @app.post("/api/projects/<project_id>/plan")
    def calculate_project_plan(project_id: str):
        project = store.get_project(project_id)
        if not project:
            return jsonify({"error": "Проект не найден."}), 404

        payload = request.get_json(silent=True) or {}
        inputs = payload.get("inputs") or {}

        try:
            result = calculate_plan(workbook_model, inputs)
        except CalculationError as exc:
            return jsonify({"error": "Ошибка расчета PLAN.", "details": exc.messages}), 400

        project["plan_inputs"] = inputs
        project["plan_result"] = result
        saved = store.upsert_project(project)
        return jsonify(saved)

    @app.post("/api/projects/<project_id>/fact")
    def calculate_project_fact(project_id: str):
        project = store.get_project(project_id)
        if not project:
            return jsonify({"error": "Проект не найден."}), 404

        payload = request.get_json(silent=True) or {}
        inputs = payload.get("inputs") or {}

        try:
            result = calculate_fact(workbook_model, inputs)
        except CalculationError as exc:
            return jsonify({"error": "Ошибка расчета FACT.", "details": exc.messages}), 400

        project["fact_inputs"] = inputs
        project["fact_result"] = result
        saved = store.upsert_project(project)
        return jsonify(saved)

    @app.get("/api/statistics")
    def statistics():
        report = build_statistics(
            store.list_projects(),
            project_group=request.args.get("project_group", ""),
            specialist=request.args.get("specialist", ""),
            date_from=request.args.get("date_from", ""),
            date_to=request.args.get("date_to", ""),
        )
        return jsonify(report)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
