from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from app import create_app
from eng_efficiency.calculator import calculate_fact, calculate_plan
from eng_efficiency.workbook import load_workbook_model


BASE_DIR = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = BASE_DIR / "Engineering Efficiency Measurement.xlsx"


class WorkbookCalculationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = load_workbook_model(WORKBOOK_PATH)

    def test_plan_matches_reference_workbook_value(self) -> None:
        result = calculate_plan(
            self.model,
            {
                "data": 7.0,
                "cad": 4.0,
                "comm": 4.0,
                "constr": 5.0,
                "overlap": 4.0,
                "designer": 4.0,
                "qualifi": 7.0,
                "owner": 3.0,
                "percent": 4.0,
                "size": 3.0,
                "resize": 2.0,
                "scope": 6.0,
                "site": 3.0,
                "split": 3.0,
                "id": 3.0,
            },
        )
        self.assertAlmostEqual(result["total_score"], 0.532893, places=6)

    def test_fact_matches_reference_workbook_value(self) -> None:
        result = calculate_fact(
            self.model,
            {
                "y1": 0.03,
                "y2": 3,
                "y3": 0.06,
                "y4": 0.09,
                "y5": 0.03,
                "y6": 0.02,
                "y7": 2,
                "y8": 4,
                "y9": 0.04,
                "y10": 0.03,
            },
        )
        self.assertAlmostEqual(result["total_score"], 0.882211, places=6)


class ApiFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage_path = Path(self.temp_dir.name) / "projects.json"
        self.app = create_app(
            {
                "TESTING": True,
                "WORKBOOK_PATH": str(WORKBOOK_PATH),
                "STORAGE_PATH": str(storage_path),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_project_create_and_calculate_plan(self) -> None:
        create_response = self.client.post(
            "/api/projects",
            json={
                "name": "Demo Project",
                "code": "DEMO-1",
                "project_group": "Pilot",
                "stage": "FEED",
                "start_date": "2026-03-01",
                "end_date": "2026-06-01",
                "project_manager": "Ivan Ivanov",
                "chief_engineer": "Petr Petrov",
                "design_lead": "Anna Sidorova",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        project = create_response.get_json()

        config_response = self.client.get("/api/config")
        factor_keys = [item["key"] for item in config_response.get_json()["plan_factors"]]
        inputs = {key: "level_3" for key in factor_keys}

        plan_response = self.client.post(
            f"/api/projects/{project['id']}/plan",
            json={"inputs": inputs},
        )
        self.assertEqual(plan_response.status_code, 200)
        updated_project = plan_response.get_json()
        self.assertIn("plan_result", updated_project)
        self.assertIsNotNone(updated_project["plan_result"])


if __name__ == "__main__":
    unittest.main()
