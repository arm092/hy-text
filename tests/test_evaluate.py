import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "evaluate.py"
FIXTURES = ROOT / "tests" / "fixtures" / "evaluate"


def load_module():
    spec = importlib.util.spec_from_file_location("hy_text_evaluate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class EvaluateTest(unittest.TestCase):
    def test_detection_metrics_use_clean_case_rate_and_protected_mutations(self):
        module = load_module()
        golden = [
            {
                "id": "faulty",
                "text": "Սխալ config/app.php տեքստ։",
                "expected_rules": ["HY-TYP-001", "HY-GRM-002"],
                "expected_text": "Ուղղված config/app.php տեքստ։",
                "protected_spans": [{"type": "filename", "text": "config/app.php"}],
            },
            {
                "id": "clean-a",
                "text": "Մաքուր տեքստ։",
                "expected_rules": [],
                "expected_text": "Մաքուր տեքստ։",
                "protected_spans": [],
            },
            {
                "id": "clean-b",
                "text": "Երկրորդ մաքուր տեքստ։",
                "expected_rules": [],
                "expected_text": "Երկրորդ մաքուր տեքստ։",
                "protected_spans": [],
            },
        ]
        reported = [
            {
                "id": "faulty",
                "reported_rules": ["HY-TYP-001"],
                "corrected_text": "Ուղղված config/app.php տեքստ։",
            },
            {
                "id": "clean-a",
                "reported_rules": ["HY-INF-001", "HY-INF-002"],
                "corrected_text": "Մաքուր տեքստ։",
            },
            {
                "id": "clean-b",
                "reported_rules": [],
                "corrected_text": "Երկրորդ մաքուր տեքստ։",
            },
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(0.5, metrics["recall"])
        self.assertEqual(0.5, metrics["clean_false_positive_rate"])
        self.assertEqual(0, metrics["protected_mutations"])
        self.assertEqual(3, metrics["case_count"])
        self.assertEqual(
            {
                "id": "faulty",
                "missing_rules": ["HY-GRM-002"],
                "extra_rules": [],
                "protected_mutations": [],
                "correction_matches": True,
                "correction_accepted": True,
            },
            metrics["cases"][0],
        )

    def test_detection_metrics_count_each_changed_protected_span(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Տես `php artisan test` և app.php։",
                "expected_rules": [],
                "expected_text": "Տես `php artisan test` և app.php։",
                "protected_spans": [
                    {"type": "command", "text": "php artisan test"},
                    {"type": "filename", "text": "app.php"},
                ],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": [],
                "corrected_text": "Տես `php artisan test` և app-php։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["protected_mutations"])
        self.assertEqual(
            [{"type": "filename", "text": "app.php"}],
            metrics["cases"][0]["protected_mutations"],
        )

    def test_detection_metrics_detect_protected_span_relocation(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Գործարկեք `php artisan test` հրամանը հիմա։",
                "expected_text": "Գործարկեք `php artisan test` հրամանը։",
                "expected_rules": ["HY-INF-001"],
                "protected_spans": [{"type": "command", "text": "php artisan test"}],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": ["HY-INF-001"],
                "corrected_text": "`php artisan test` հրամանը գործարկեք հիմա։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["protected_mutations"])

    def test_detection_metrics_detect_protected_span_duplication(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php ֆայլը։",
                "expected_text": "Բացեք app.php ֆայլը։",
                "expected_rules": [],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": [],
                "corrected_text": "Բացեք app.php ֆայլը և պահեք app.php ֆայլը։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["protected_mutations"])

    def test_detection_metrics_detect_mutation_followed_by_reinsertion(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php ֆայլը։",
                "expected_text": "Բացեք app.php ֆայլը։",
                "expected_rules": [],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": [],
                "corrected_text": "Բացեք app-php ֆայլը։ Հղում՝ app.php։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["protected_mutations"])

    def test_detection_metrics_gate_empty_and_noop_faulty_corrections(self):
        module = load_module()
        golden = [
            {
                "id": "empty",
                "text": "Դիմումը հաստատվել է.",
                "expected_text": "Դիմումը հաստատվել է։",
                "expected_rules": ["HY-TYP-001"],
                "protected_spans": [],
            },
            {
                "id": "noop",
                "text": "Բարև , Անի։",
                "expected_text": "Բարև, Անի։",
                "expected_rules": ["HY-TYP-004"],
                "protected_spans": [],
            },
        ]
        reported = [
            {"id": "empty", "reported_rules": ["HY-TYP-001"], "corrected_text": ""},
            {
                "id": "noop",
                "reported_rules": ["HY-TYP-004"],
                "corrected_text": "Բարև , Անի։",
            },
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(2, metrics["correction_failures"])
        self.assertEqual(0.0, metrics["correction_accuracy"])

    def test_detection_metrics_gate_clean_text_rewrite(self):
        module = load_module()
        golden = [
            {
                "id": "clean",
                "text": "Դիմումը հաստատվել է։",
                "expected_text": "Դիմումը հաստատվել է։",
                "expected_rules": [],
                "protected_spans": [],
                "accepted_corrections": ["Դիմումը հաստատվել է։", "Հայտը հաստատվել է։"],
            }
        ]
        reported = [
            {"id": "clean", "reported_rules": [], "corrected_text": "Հայտը հաստատվել է։"}
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["correction_failures"])
        self.assertFalse(metrics["cases"][0]["correction_accepted"])

    def test_detection_metrics_accept_reviewed_faulty_alternate(self):
        module = load_module()
        golden = [
            {
                "id": "faulty",
                "text": "Դիմումը հաստատվել է.",
                "expected_text": "Դիմումը հաստատվել է։",
                "expected_rules": ["HY-TYP-001"],
                "protected_spans": [],
                "accepted_corrections": [
                    "Դիմումը հաստատվել է։",
                    "Հայտը հաստատվել է։",
                ],
            }
        ]
        reported = [
            {
                "id": "faulty",
                "reported_rules": ["HY-TYP-001"],
                "corrected_text": "Հայտը հաստատվել է։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(0, metrics["correction_failures"])
        self.assertEqual(1.0, metrics["correction_accuracy"])
        self.assertTrue(metrics["cases"][0]["correction_accepted"])

    def test_detection_metrics_reject_malformed_and_unknown_rule_ids(self):
        module = load_module()
        malformed_golden = [
            {
                "id": "bad",
                "text": "Տեքստ։",
                "expected_text": "Տեքստ։",
                "expected_rules": ["HY-TYP-001-extra"],
                "protected_spans": [],
            }
        ]
        valid_golden = [
            {
                "id": "bad",
                "text": "Տեքստ։",
                "expected_text": "Տեքստ։",
                "expected_rules": [],
                "protected_spans": [],
            }
        ]

        with self.assertRaisesRegex(ValueError, "invalid expected rules"):
            module.detection_metrics(malformed_golden, [])
        with self.assertRaisesRegex(ValueError, "unknown reported rule"):
            module.detection_metrics(
                valid_golden,
                [{"id": "bad", "reported_rules": ["HY-TYP-999"], "corrected_text": "Տեքստ։"}],
            )

    def test_detection_metrics_reject_accepted_correction_that_reorders_protected_spans(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Տես app.php և `php artisan test`։",
                "expected_text": "Տես `php artisan test` և app.php։",
                "expected_rules": ["HY-INF-001"],
                "protected_spans": [
                    {"type": "filename", "text": "app.php"},
                    {"type": "command", "text": "php artisan test"},
                ],
            }
        ]

        with self.assertRaisesRegex(ValueError, "reorders protected spans"):
            module.detection_metrics(golden, [])

    def test_detection_metrics_reject_accepted_correction_that_moves_one_protected_span(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php ֆայլը և պահեք փոփոխությունը։",
                "expected_text": "app.php ֆայլը բացեք և պահեք փոփոխությունը։",
                "expected_rules": ["HY-INF-001"],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]

        with self.assertRaisesRegex(ValueError, "relocates protected span"):
            module.detection_metrics(golden, [])

    def test_detection_metrics_reject_mutated_identical_occurrence_and_reinserted_copy(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php ֆայլը, ապա պահեք app.php ֆայլը։",
                "expected_text": "Բացեք app-php ֆայլը, ապա պահեք app.php ֆայլը։ Հղում՝ app.php։",
                "expected_rules": ["HY-TYP-004"],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]

        with self.assertRaisesRegex(ValueError, "relocates protected span"):
            module.detection_metrics(golden, [])

    def test_detection_metrics_reject_accepted_comma_and_question_moves(self):
        module = load_module()
        cases = (
            ("Տես app.php, հետո փակիր։", "Տես, app.php հետո փակիր։"),
            ("Տես app.php? Հետո փակիր։", "Տես? app.php Հետո փակիր։"),
        )

        for source, unsafe_correction in cases:
            with self.subTest(unsafe_correction=unsafe_correction):
                golden = [
                    {
                        "id": "protected",
                        "text": source,
                        "expected_text": unsafe_correction,
                        "expected_rules": ["HY-TYP-004"],
                        "protected_spans": [{"type": "filename", "text": "app.php"}],
                    }
                ]
                with self.assertRaisesRegex(ValueError, "relocates protected span"):
                    module.detection_metrics(golden, [])

    def test_detection_metrics_flag_reported_comma_and_question_moves(self):
        module = load_module()
        cases = (
            ("Տես app.php, հետո փակիր.", "Տես app.php, հետո փակիր։", "Տես, app.php հետո փակիր։"),
            ("Տես app.php? Հետո փակիր.", "Տես app.php? Հետո փակիր։", "Տես? app.php Հետո փակիր։"),
        )

        for source, expected, malicious in cases:
            with self.subTest(malicious=malicious):
                golden = [
                    {
                        "id": "protected",
                        "text": source,
                        "expected_text": expected,
                        "expected_rules": ["HY-TYP-001"],
                        "protected_spans": [{"type": "filename", "text": "app.php"}],
                    }
                ]
                reported = [
                    {
                        "id": "protected",
                        "reported_rules": ["HY-TYP-001"],
                        "corrected_text": malicious,
                    }
                ]

                metrics = module.detection_metrics(golden, reported)

                self.assertEqual(1, metrics["protected_mutations"])
                self.assertEqual(1, metrics["correction_failures"])

    def test_detection_metrics_accept_legitimate_wording_edits_before_protected_span(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php ֆայլը հիմա.",
                "expected_text": "Խնդրում եմ բացել app.php ֆայլը հիմա։",
                "expected_rules": ["HY-TYP-001"],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": ["HY-TYP-001"],
                "corrected_text": "Խնդրում եմ բացել app.php ֆայլը հիմա։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(0, metrics["protected_mutations"])
        self.assertEqual(0, metrics["correction_failures"])

    def test_detection_metrics_reject_anchorless_accepted_relocation(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php հիմա.",
                "expected_text": "Խնդրում եմ անմիջապես օգտագործեք app.php։",
                "expected_rules": ["HY-TYP-001"],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]

        with self.assertRaisesRegex(ValueError, "relocates protected span"):
            module.detection_metrics(golden, [])

    def test_detection_metrics_flag_anchorless_reported_relocation(self):
        module = load_module()
        golden = [
            {
                "id": "protected",
                "text": "Բացեք app.php հիմա.",
                "expected_text": "Բացեք app.php հիմա։",
                "expected_rules": ["HY-TYP-001"],
                "protected_spans": [{"type": "filename", "text": "app.php"}],
            }
        ]
        reported = [
            {
                "id": "protected",
                "reported_rules": ["HY-TYP-001"],
                "corrected_text": "Խնդրում եմ անմիջապես օգտագործեք app.php։",
            }
        ]

        metrics = module.detection_metrics(golden, reported)

        self.assertEqual(1, metrics["protected_mutations"])
        self.assertEqual(1, metrics["correction_failures"])

    def test_detection_metrics_accept_exact_protected_only_identity(self):
        module = load_module()
        for source in ("app.php", "app.php.", "app.php։"):
            with self.subTest(source=source):
                golden = [
                    {
                        "id": "protected",
                        "text": source,
                        "expected_text": source,
                        "expected_rules": [],
                        "protected_spans": [{"type": "filename", "text": "app.php"}],
                    }
                ]
                reported = [
                    {
                        "id": "protected",
                        "reported_rules": [],
                        "corrected_text": source,
                    }
                ]

                metrics = module.detection_metrics(golden, reported)

                self.assertEqual(0, metrics["protected_mutations"])
                self.assertEqual(0, metrics["correction_failures"])

    def test_detection_metrics_reject_terminal_punctuation_only_anchor_bypass(self):
        module = load_module()
        cases = (
            ("Բացեք app.php հիմա.", "Խնդրում եմ անմիջապես app.php."),
            ("Բացեք app.php հիմա։", "Խնդրում եմ անմիջապես app.php։"),
        )

        for source, unsafe_correction in cases:
            with self.subTest(unsafe_correction=unsafe_correction):
                golden = [
                    {
                        "id": "protected",
                        "text": source,
                        "expected_text": unsafe_correction,
                        "expected_rules": ["HY-TYP-001"],
                        "protected_spans": [{"type": "filename", "text": "app.php"}],
                    }
                ]

                with self.assertRaisesRegex(ValueError, "relocates protected span"):
                    module.detection_metrics(golden, [])

    def test_detection_metrics_flag_terminal_punctuation_only_reported_bypass(self):
        module = load_module()
        cases = (
            ("Բացեք app.php հիմա.", "Խնդրում եմ բացել app.php հիմա։", "Խնդրում եմ անմիջապես app.php."),
            ("Բացեք app.php հիմա։", "Խնդրում եմ բացել app.php հիմա։", "Խնդրում եմ անմիջապես app.php։"),
        )

        for source, expected, malicious in cases:
            with self.subTest(malicious=malicious):
                golden = [
                    {
                        "id": "protected",
                        "text": source,
                        "expected_text": expected,
                        "expected_rules": ["HY-TYP-001"],
                        "protected_spans": [{"type": "filename", "text": "app.php"}],
                    }
                ]
                reported = [
                    {
                        "id": "protected",
                        "reported_rules": ["HY-TYP-001"],
                        "corrected_text": malicious,
                    }
                ]

                metrics = module.detection_metrics(golden, reported)

                self.assertEqual(1, metrics["protected_mutations"])
                self.assertEqual(1, metrics["correction_failures"])

    def test_detection_metrics_reject_duplicate_or_incomplete_results(self):
        module = load_module()
        golden = [
            {
                "id": "a",
                "text": "Ա։",
                "expected_rules": [],
                "expected_text": "Ա։",
                "protected_spans": [],
            },
            {
                "id": "b",
                "text": "Բ։",
                "expected_rules": [],
                "expected_text": "Բ։",
                "protected_spans": [],
            },
        ]
        duplicate = [
            {"id": "a", "reported_rules": [], "corrected_text": "Ա։"},
            {"id": "a", "reported_rules": [], "corrected_text": "Ա։"},
        ]

        with self.assertRaisesRegex(ValueError, "duplicate check result id"):
            module.detection_metrics(golden, duplicate)

        with self.assertRaisesRegex(ValueError, "missing check results"):
            module.detection_metrics(golden, duplicate[:1])

    def test_detection_metrics_count_expected_and_extra_rules(self):
        module = load_module()
        golden = [
            {
                "id": "a",
                "text": "Ա.",
                "expected_text": "Ա։",
                "expected_rules": ["HY-TYP-001", "HY-PUN-001"],
                "protected_spans": [],
            },
            {
                "id": "b",
                "text": "Բ։",
                "expected_text": "Բ։",
                "expected_rules": [],
                "protected_spans": [],
            },
        ]
        reported = [
            {
                "id": "a",
                "reported_rules": ["HY-TYP-001", "HY-GRM-002"],
                "corrected_text": "Ա։",
            },
            {"id": "b", "reported_rules": [], "corrected_text": "Բ։"},
        ]
        metrics = module.detection_metrics(golden, reported)
        self.assertEqual(0.5, metrics["recall"])
        self.assertEqual(0.0, metrics["clean_false_positive_rate"])

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

    def test_total_score_applies_published_weights_rounding_and_caps(self):
        module = load_module()

        self.assertEqual(
            8.2,
            module.total_score(
                {"typography": 9, "language": 8, "grammar": 8, "structure": 8, "reader": 8}
            ),
        )
        self.assertEqual(
            5.0,
            module.total_score(
                {"typography": 10, "language": 2, "grammar": 10, "structure": 10, "reader": 10}
            ),
        )
        self.assertEqual(
            7.0,
            module.total_score(
                {"typography": 3, "language": 10, "grammar": 10, "structure": 10, "reader": 10}
            ),
        )
        self.assertEqual(
            7.0,
            module.total_score(
                {"typography": 10, "language": 10, "grammar": 3, "structure": 10, "reader": 10}
            ),
        )

    def test_score_calibration_passes_only_when_all_150_results_are_within_limits(self):
        module = load_module()

        metrics = module.score_calibration(
            load_fixture("score-golden.json"),
            load_fixture("score-runs-pass.json"),
        )

        self.assertTrue(metrics["passed"])
        self.assertEqual(
            {
                "expected_runs": 3,
                "actual_runs": 3,
                "reviewed_cases": 50,
                "expected_results": 150,
                "actual_results": 150,
                "complete": True,
            },
            metrics["run_completeness"],
        )
        self.assertEqual(0.0, metrics["max_total_deviation"])
        self.assertEqual(0.0, metrics["max_dimension_deviation"])
        self.assertEqual([], metrics["failing_cases"])

    def test_score_calibration_reports_dimension_failure_even_when_total_would_pass(self):
        module = load_module()

        metrics = module.score_calibration(
            load_fixture("score-golden.json"),
            load_fixture("score-runs-fail.json"),
        )

        self.assertFalse(metrics["passed"])
        self.assertEqual(0.3, metrics["max_total_deviation"])
        self.assertEqual(1.1, metrics["max_dimension_deviation"])
        self.assertEqual(
            [
                {
                    "run": 2,
                    "id": "case-01",
                    "total_deviation": 0.3,
                    "dimension_deviations": {"language": 1.1},
                }
            ],
            metrics["failing_cases"],
        )

    def test_score_calibration_rejects_truncated_reviewed_golden_set(self):
        module = load_module()
        golden = [load_fixture("score-golden.json")[0]]
        runs = [
            run
            for run in load_fixture("score-runs-pass.json")
            if run["id"] == "case-01"
        ]

        with self.assertRaisesRegex(ValueError, "exactly 50 reviewed golden cases"):
            module.score_calibration(golden, runs)

    def test_score_calibration_accepts_inclusive_total_and_dimension_boundaries(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        runs = load_fixture("score-runs-pass.json")
        eight_point_five = {dimension: 8.5 for dimension in module.DIMENSIONS}

        golden[0]["scores"] = eight_point_five
        for run in runs:
            if run["id"] == "case-01":
                run["scores"] = eight_point_five.copy()
        next(run for run in runs if run["run"] == 1 and run["id"] == "case-01")["scores"] = {
            dimension: 7.8 for dimension in module.DIMENSIONS
        }
        next(run for run in runs if run["run"] == 2 and run["id"] == "case-02")["scores"][
            "language"
        ] = 8.0

        metrics = module.score_calibration(golden, runs)

        self.assertTrue(metrics["passed"])
        self.assertEqual(0.7, metrics["max_total_deviation"])
        self.assertEqual(1.0, metrics["max_dimension_deviation"])
        self.assertEqual([], metrics["failing_cases"])

    def test_score_calibration_keeps_all_dimension_diagnostics_for_total_only_failure(self):
        module = load_module()
        runs = load_fixture("score-runs-pass.json")
        next(run for run in runs if run["run"] == 1 and run["id"] == "case-01")["scores"] = {
            dimension: 8.2 for dimension in module.DIMENSIONS
        }

        metrics = module.score_calibration(load_fixture("score-golden.json"), runs)

        self.assertEqual(
            [
                {
                    "run": 1,
                    "id": "case-01",
                    "total_deviation": 0.8,
                    "dimension_deviations": {
                        "typography": 0.8,
                        "language": 0.8,
                        "grammar": 0.8,
                        "structure": 0.8,
                        "reader": 0.8,
                    },
                }
            ],
            metrics["failing_cases"],
        )

    def test_score_calibration_rejects_duplicate_run_case_pairs(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        runs = load_fixture("score-runs-pass.json")

        with self.assertRaisesRegex(ValueError, "duplicate run/id pair"):
            module.score_calibration(golden, runs + [runs[0]])

    def test_score_calibration_rejects_missing_run(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        runs = [run for run in load_fixture("score-runs-pass.json") if run["run"] != 3]

        with self.assertRaisesRegex(ValueError, "missing or unexpected runs"):
            module.score_calibration(golden, runs)

    def test_score_calibration_rejects_missing_reviewed_run_case(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        runs = [
            run
            for run in load_fixture("score-runs-pass.json")
            if not (run["run"] == 3 and run["id"] == "case-50")
        ]

        with self.assertRaisesRegex(ValueError, "missing reviewed cases"):
            module.score_calibration(golden, runs)

    def test_score_calibration_rejects_unreviewed_golden_case(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        golden[0]["reviewed"] = False

        with self.assertRaisesRegex(ValueError, "reviewed"):
            module.score_calibration(golden, load_fixture("score-runs-pass.json"))

    def test_score_calibration_rejects_invalid_score_dimensions(self):
        module = load_module()
        runs = load_fixture("score-runs-pass.json")
        del runs[0]["scores"]["reader"]

        with self.assertRaisesRegex(ValueError, "dimensions"):
            module.score_calibration(load_fixture("score-golden.json"), runs)

    def test_score_calibration_rejects_scores_outside_zero_to_ten(self):
        module = load_module()
        golden = load_fixture("score-golden.json")
        golden[0]["scores"]["language"] = 10.1

        with self.assertRaisesRegex(ValueError, "0 to 10"):
            module.score_calibration(golden, load_fixture("score-runs-pass.json"))


if __name__ == "__main__":
    unittest.main()
