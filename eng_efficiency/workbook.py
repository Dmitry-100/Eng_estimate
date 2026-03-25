from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


@dataclass(frozen=True)
class FactorOption:
    code: str
    label: str
    value: float

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "label": self.label, "value": self.value}


@dataclass(frozen=True)
class PlanFactor:
    key: str
    name: str
    options: list[FactorOption]

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "options": [option.to_dict() for option in self.options],
        }


@dataclass(frozen=True)
class PlanMeasure:
    key: str
    name: str
    worst: float
    best: float
    weight: float
    intercept: float
    coefficients: dict[str, float]
    score_slope: float
    score_intercept: float

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "worst": self.worst,
            "best": self.best,
            "weight": self.weight,
            "intercept": self.intercept,
            "coefficients": self.coefficients,
            "score_slope": self.score_slope,
            "score_intercept": self.score_intercept,
        }


@dataclass(frozen=True)
class FactMeasure:
    key: str
    name: str
    worst: float
    best: float
    weight: float
    reference_levels: list[str]
    score_slope: float
    score_intercept: float

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "worst": self.worst,
            "best": self.best,
            "weight": self.weight,
            "reference_levels": self.reference_levels,
            "score_slope": self.score_slope,
            "score_intercept": self.score_intercept,
        }


@dataclass(frozen=True)
class WorkbookModel:
    plan_factors: list[PlanFactor]
    plan_measures: list[PlanMeasure]
    fact_measures: list[FactMeasure]

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_factors": [factor.to_dict() for factor in self.plan_factors],
            "plan_measures": [measure.to_dict() for measure in self.plan_measures],
            "fact_measures": [measure.to_dict() for measure in self.fact_measures],
        }


@dataclass(frozen=True)
class CellData:
    value: str | None
    formula: str | None


def _safe_float(raw: str | None) -> float:
    if raw is None or raw == "":
        raise ValueError("Expected numeric cell value.")
    return float(raw)


def _parse_formula_term(formula: str) -> tuple[str, float]:
    match = re.fullmatch(
        r"\s*([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)\s*\*\s*([A-Za-z_][A-Za-z0-9_]*)\s*",
        formula,
    )
    if not match:
        raise ValueError(f"Unsupported workbook coefficient formula: {formula}")
    coefficient = float(match.group(1))
    variable = match.group(2)
    return variable, coefficient


def _parse_intercept(formula: str) -> float:
    match = re.match(
        r"\s*([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)\s*\+\s*SUM\(E\d+:S\d+\)\s*",
        formula,
    )
    if not match:
        raise ValueError(f"Unsupported workbook intercept formula: {formula}")
    return float(match.group(1))


def _parse_score_formula(formula: str) -> tuple[float, float]:
    match = re.search(
        r"([+-]?\d+(?:\.\d+)?)\*[A-Z]+\d+([+-]\d+(?:\.\d+)?)(?:\)+)\s*$",
        formula,
    )
    if not match:
        raise ValueError(f"Unsupported workbook score formula: {formula}")
    return float(match.group(1)), float(match.group(2))


class WorkbookReader:
    def __init__(self, workbook_path: Path) -> None:
        self.workbook_path = workbook_path
        self.shared_strings: list[str] = []

    def load(self) -> WorkbookModel:
        with ZipFile(self.workbook_path) as archive:
            self.shared_strings = self._load_shared_strings(archive)
            sheets = self._load_sheet_targets(archive)
            input_sheet = self._load_sheet(archive, sheets["input I"])
            plan_sheet = self._load_sheet(archive, sheets["engineering efficiency PLAN"])
            fact_sheet = self._load_sheet(archive, sheets["engineering efficiency FACT"])

        plan_factors = self._parse_plan_factors(input_sheet)
        plan_measures = self._parse_plan_measures(plan_sheet)
        fact_measures = self._parse_fact_measures(fact_sheet)
        return WorkbookModel(
            plan_factors=plan_factors,
            plan_measures=plan_measures,
            fact_measures=fact_measures,
        )

    def _load_shared_strings(self, archive: ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []

        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for item in root.findall("main:si", NS):
            parts = [node.text or "" for node in item.findall(".//main:t", NS)]
            values.append("".join(parts).strip())
        return values

    def _load_sheet_targets(self, archive: ZipFile) -> dict[str, str]:
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        rel_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {item.attrib["Id"]: item.attrib["Target"] for item in rel_root}

        sheets: dict[str, str] = {}
        sheets_node = workbook_root.find("main:sheets", NS)
        for sheet in list(sheets_node) if sheets_node is not None else []:
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            sheets[sheet.attrib["name"]] = f"xl/{rel_map[rel_id]}"
        return sheets

    def _load_sheet(self, archive: ZipFile, target: str) -> dict[str, CellData]:
        root = ET.fromstring(archive.read(target))
        cells: dict[str, CellData] = {}
        for cell in root.findall(".//main:c", NS):
            reference = cell.attrib.get("r")
            if not reference:
                continue

            cell_type = cell.attrib.get("t")
            formula_node = cell.find("main:f", NS)
            value_node = cell.find("main:v", NS)

            value: str | None = None
            if value_node is not None and value_node.text is not None:
                value = value_node.text
                if cell_type == "s":
                    value = self.shared_strings[int(value)]

            formula = formula_node.text if formula_node is not None else None
            cells[reference] = CellData(value=value, formula=formula)
        return cells

    def _text(self, cells: dict[str, CellData], reference: str) -> str:
        cell = cells.get(reference)
        if not cell or cell.value is None:
            return ""
        return cell.value.strip()

    def _number(self, cells: dict[str, CellData], reference: str) -> float:
        cell = cells.get(reference)
        return _safe_float(cell.value if cell else None)

    def _parse_plan_factors(self, cells: dict[str, CellData]) -> list[PlanFactor]:
        factors: list[PlanFactor] = []
        option_columns = ["D", "E", "F", "G", "H"]

        for row in range(5, 20):
            numeric_row = row + 19
            key = self._text(cells, f"C{row}")
            name = self._text(cells, f"B{row}").lstrip("• ").strip()
            options: list[FactorOption] = []
            for index, column in enumerate(option_columns, start=1):
                label = self._text(cells, f"{column}{row}")
                value = self._number(cells, f"{column}{numeric_row}")
                options.append(FactorOption(code=f"level_{index}", label=label, value=value))
            factors.append(PlanFactor(key=key, name=name, options=options))
        return factors

    def _parse_plan_measures(self, cells: dict[str, CellData]) -> list[PlanMeasure]:
        factor_columns: dict[str, str] = {}
        for column in [chr(code) for code in range(ord("E"), ord("S") + 1)]:
            key = self._text(cells, f"{column}3")
            if key:
                factor_columns[column] = key

        measures: list[PlanMeasure] = []
        for offset, row in enumerate(range(6, 16), start=1):
            name = self._text(cells, f"B{row}")
            intercept_formula = cells[f"V{row}"].formula
            intercept = _parse_intercept(intercept_formula or "")

            coefficients: dict[str, float] = {}
            for column, default_key in factor_columns.items():
                cell = cells.get(f"{column}{row}")
                if not cell or not cell.formula:
                    continue
                variable, coefficient = _parse_formula_term(cell.formula)
                coefficients[variable or default_key] = coefficient

            measures.append(
                PlanMeasure(
                    key=f"y{offset}",
                    name=name,
                    worst=self._number(cells, f"T{row}"),
                    best=self._number(cells, f"U{row}"),
                    weight=self._number(cells, f"X{row}"),
                    intercept=intercept,
                    coefficients=coefficients,
                    score_slope=_parse_score_formula(cells[f"W{row}"].formula or "")[0],
                    score_intercept=_parse_score_formula(cells[f"W{row}"].formula or "")[1],
                )
            )
        return measures

    def _parse_fact_measures(self, cells: dict[str, CellData]) -> list[FactMeasure]:
        measures: list[FactMeasure] = []
        for row in range(5, 15):
            measures.append(
                FactMeasure(
                    key=self._text(cells, f"C{row}") or f"y{row - 4}",
                    name=self._text(cells, f"B{row}"),
                    worst=self._number(cells, f"I{row}"),
                    best=self._number(cells, f"J{row}"),
                    weight=self._number(cells, f"M{row}"),
                    reference_levels=[self._text(cells, f"{column}{row}") for column in ["D", "E", "F", "G", "H"]],
                    score_slope=_parse_score_formula(cells[f"L{row}"].formula or "")[0],
                    score_intercept=_parse_score_formula(cells[f"L{row}"].formula or "")[1],
                )
            )
        return measures


def load_workbook_model(workbook_path: Path) -> WorkbookModel:
    return WorkbookReader(workbook_path).load()
