from __future__ import annotations

from collections import Counter
from datetime import date


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _matches_period(project: dict[str, object], start: date | None, end: date | None) -> bool:
    project_start = _parse_date(str(project.get("start_date") or ""))
    project_end = _parse_date(str(project.get("end_date") or "")) or project_start

    if start and project_end and project_end < start:
        return False
    if end and project_start and project_start > end:
        return False
    return True


def build_statistics(
    projects: list[dict[str, object]],
    *,
    project_group: str = "",
    specialist: str = "",
    date_from: str = "",
    date_to: str = "",
) -> dict[str, object]:
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    specialist_query = specialist.strip().lower()
    group_query = project_group.strip().lower()

    filtered = []
    for project in projects:
        if group_query and group_query not in str(project.get("project_group", "")).lower():
            continue
        if specialist_query:
            specialist_blob = " ".join(
                str(project.get(field, ""))
                for field in ("project_manager", "chief_engineer", "design_lead")
            ).lower()
            if specialist_query not in specialist_blob:
                continue
        if not _matches_period(project, start, end):
            continue
        filtered.append(project)

    plan_scores = [
        float(project["plan_result"]["total_score"])
        for project in filtered
        if project.get("plan_result")
    ]
    fact_scores = [
        float(project["fact_result"]["total_score"])
        for project in filtered
        if project.get("fact_result")
    ]

    stage_counter = Counter(str(project.get("stage") or "Не указана") for project in filtered)

    avg_plan = round(sum(plan_scores) / len(plan_scores), 6) if plan_scores else None
    avg_fact = round(sum(fact_scores) / len(fact_scores), 6) if fact_scores else None
    gap = round(avg_fact - avg_plan, 6) if avg_plan is not None and avg_fact is not None else None

    return {
        "filters": {
            "project_group": project_group,
            "specialist": specialist,
            "date_from": date_from,
            "date_to": date_to,
        },
        "summary": {
            "project_count": len(filtered),
            "average_plan_score": avg_plan,
            "average_fact_score": avg_fact,
            "average_gap_fact_minus_plan": gap,
        },
        "stage_distribution": [
            {"stage": stage, "count": count}
            for stage, count in stage_counter.most_common()
        ],
        "projects": [
            {
                "id": project.get("id"),
                "name": project.get("name"),
                "code": project.get("code"),
                "project_group": project.get("project_group"),
                "stage": project.get("stage"),
                "start_date": project.get("start_date"),
                "end_date": project.get("end_date"),
                "project_manager": project.get("project_manager"),
                "chief_engineer": project.get("chief_engineer"),
                "design_lead": project.get("design_lead"),
                "plan_score": project.get("plan_result", {}).get("total_score") if project.get("plan_result") else None,
                "fact_score": project.get("fact_result", {}).get("total_score") if project.get("fact_result") else None,
            }
            for project in filtered
        ],
    }
