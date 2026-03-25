from __future__ import annotations

from dataclasses import dataclass

from .workbook import FactMeasure, PlanFactor, PlanMeasure, WorkbookModel


@dataclass
class CalculationError(Exception):
    messages: list[str]

    def __str__(self) -> str:
        return "; ".join(self.messages)


def _round(value: float) -> float:
    return round(value, 6)


def _normalize_value(
    actual: float,
    worst: float,
    best: float,
    *,
    slope: float,
    intercept: float,
) -> float:
    if worst < best:
        if actual <= worst:
            return 0.0
        if actual >= best:
            return 1.0
    else:
        if actual >= worst:
            return 0.0
        if actual <= best:
            return 1.0

    return max(0.0, min(1.0, slope * actual + intercept))


def _orientation_label(worst: float, best: float) -> str:
    return "higher-is-better" if worst < best else "lower-is-better"


def _get_option(factor: PlanFactor, code: str | None):
    if code is None:
        return None
    return next((option for option in factor.options if option.code == code), None)


def _resolve_factor_value(factor: PlanFactor, raw_value):
    if raw_value in (None, ""):
        return None

    option = _get_option(factor, str(raw_value))
    if option is not None:
        return {
            "selected_code": option.code,
            "selected_label": option.label,
            "numeric_value": option.value,
        }

    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        return None

    return {
        "selected_code": "manual",
        "selected_label": "Manual numeric value",
        "numeric_value": numeric_value,
    }


def calculate_plan(model: WorkbookModel, selections: dict[str, str]) -> dict[str, object]:
    errors: list[str] = []
    factor_lookup = {factor.key: factor for factor in model.plan_factors}
    chosen_factors = []
    factor_values: dict[str, float] = {}

    for factor in model.plan_factors:
        resolved = _resolve_factor_value(factor, selections.get(factor.key))
        if resolved is None:
            errors.append(f"Не выбрано значение для фактора '{factor.name}'.")
            continue
        factor_values[factor.key] = resolved["numeric_value"]
        chosen_factors.append(
            {
                "key": factor.key,
                "name": factor.name,
                "selected_code": resolved["selected_code"],
                "selected_label": resolved["selected_label"],
                "numeric_value": _round(float(resolved["numeric_value"])),
            }
        )

    if errors:
        raise CalculationError(errors)

    measures = []
    total_score = 0.0
    for measure in model.plan_measures:
        contributions = []
        raw_value = measure.intercept
        for key, coefficient in measure.coefficients.items():
            factor_value = factor_values[key]
            product = coefficient * factor_value
            raw_value += product
            contributions.append(
                {
                    "factor_key": key,
                    "factor_name": factor_lookup[key].name,
                    "coefficient": _round(coefficient),
                    "factor_value": _round(factor_value),
                    "product": _round(product),
                }
            )

        normalized_score = _normalize_value(
            raw_value,
            measure.worst,
            measure.best,
            slope=measure.score_slope,
            intercept=measure.score_intercept,
        )
        weighted_score = normalized_score * measure.weight
        total_score += weighted_score
        measures.append(
            {
                "key": measure.key,
                "name": measure.name,
                "raw_value": _round(raw_value),
                "normalized_score": _round(normalized_score),
                "weight": _round(measure.weight),
                "weighted_score": _round(weighted_score),
                "worst": _round(measure.worst),
                "best": _round(measure.best),
                "orientation": _orientation_label(measure.worst, measure.best),
                "intercept": _round(measure.intercept),
                "contributions": contributions,
            }
        )

    return {
        "total_score": _round(total_score),
        "factors": chosen_factors,
        "measures": measures,
    }


def calculate_fact(model: WorkbookModel, actual_values: dict[str, float | str]) -> dict[str, object]:
    errors: list[str] = []
    measures = []
    total_score = 0.0

    for measure in model.fact_measures:
        raw_input = actual_values.get(measure.key)
        if raw_input in ("", None):
            errors.append(f"Не заполнено фактическое значение для показателя '{measure.name}'.")
            continue

        try:
            value = float(raw_input)
        except (TypeError, ValueError):
            errors.append(f"Неверное фактическое значение для показателя '{measure.name}'.")
            continue

        normalized_score = _normalize_value(
            value,
            measure.worst,
            measure.best,
            slope=measure.score_slope,
            intercept=measure.score_intercept,
        )
        weighted_score = normalized_score * measure.weight
        total_score += weighted_score
        measures.append(
            {
                "key": measure.key,
                "name": measure.name,
                "actual_value": _round(value),
                "normalized_score": _round(normalized_score),
                "weight": _round(measure.weight),
                "weighted_score": _round(weighted_score),
                "worst": _round(measure.worst),
                "best": _round(measure.best),
                "orientation": _orientation_label(measure.worst, measure.best),
                "reference_levels": measure.reference_levels,
            }
        )

    if errors:
        raise CalculationError(errors)

    return {
        "total_score": _round(total_score),
        "measures": measures,
    }
