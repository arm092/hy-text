import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "evaluate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hy_text_evaluate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvaluateTest(unittest.TestCase):
    def test_detection_metrics_count_expected_and_extra_rules(self):
        module = load_module()
        golden = [
            {"id": "a", "expected_rules": ["HY-TYP-001", "HY-PUN-001"]},
            {"id": "b", "expected_rules": []},
        ]
        reported = [
            {"id": "a", "reported_rules": ["HY-TYP-001", "HY-GRM-002"]},
            {"id": "b", "reported_rules": []},
        ]
        metrics = module.detection_metrics(golden, reported)
        self.assertEqual(0.5, metrics["recall"])
        self.assertEqual(0.5, metrics["false_discovery_rate"])

    def test_score_drift_uses_reviewed_cases_only(self):
        module = load_module()
        golden = [
            {"id": "a", "reviewed": True, "scores": {"typography": 8, "language": 8, "grammar": 8, "structure": 8, "reader": 8}},
            {"id": "b", "reviewed": False, "scores": {"typography": 1, "language": 1, "grammar": 1, "structure": 1, "reader": 1}},
        ]
        runs = [
            {"id": "a", "scores": {"typography": 8.5, "language": 8, "grammar": 7.5, "structure": 8, "reader": 8}},
            {"id": "b", "scores": {"typography": 10, "language": 10, "grammar": 10, "structure": 10, "reader": 10}},
        ]
        drift = module.score_drift(golden, runs)
        self.assertEqual(0.2, drift["mean_composite_deviation"])
        self.assertEqual(0.5, drift["max_dimension_deviation"])


if __name__ == "__main__":
    unittest.main()
