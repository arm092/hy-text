import json
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROUND10_CHUNK_SHA256 = (
    "9d83607645e949b2701fe62e1a0e5fd290cf4e6669e251d5381f444638d35bac",
    "1f676973dbc288f0931bb0909186c9f08658ee3e96661cc2c9c9eb65b3aa6249",
    "bb995eb856e6a821de0a68c29556f376a5c2e2e8699cbd5fca5c01e0d201c1c2",
    "831b844f288cf43f7c4d0586b2096c3c643a335b60214802a2271d99ef5c056d",
    "d9461f847c6da049cb0d983f3a045f0252285d08acfa957944133144a0e83256",
    "6a8d07e2b7fe942fcafbb94fb4fd3403a379d83f1c4e7068921bee0572a018e3",
    "5608606cef8039b807f9ced5bf30db1edf6f07c0dc69f8e3c8d6b5cf85d63ff7",
    "679e8c8a5bfbb1b1b3e59dec8c62b1c5c2c734523dc5c2bad66565de8639fc21",
    "6f414a69b69bc7c14206d552993facd295e8b6c9158ca6c6d8f3cee6270f4a36",
    "7bc44c73756ab67853786941c6764ccfcf0bc5ef065ca2abb86df2d174f3ba42",
    "f5ec866a38ccef2a32309139a65712519edf00bf80c0b186c3a507a366ae57f8",
    "d0be100b835621a8a872500b5146981b9ba9e38ac11510f7a01388a16ea09ec3",
    "2ac0df90ad7d7736bf5c5c62816d30876033740dd78b614b22fa4b2ff41d254c",
    "ab7a55cc194e7aa2e668ba3eb85005d5064ca56827198a6c7ad64e3a877b74db",
    "84fc8b9d0c406c979889543f26e210a74e8093e022aba7fecfde68e08f56f2e0",
    "9e9b798486bff9aba929739129158b3f5001209ef1a675a7b7f6991cd4bd5d4a",
    "83203afb82e44dc705880c6334decc0d1f3cd3d34966dd85a5d213619c617ab9",
    "57c4ee9b836e74e157cc1c1d8db598f3e3d28146f0e5a6b27b44adf93ad04a97",
    "992e21cc8cd90e68869392c80dbea0e8cd36430a087f3ad7d7548a39a9752cb7",
    "9706973973d62ef17e62aad05491016b499507120e6df05ab27d02a52a0cebc6",
    "fdb114c92433a4fb078e7f5ebf1253ae162eb48a6b2ea167ba7fdf64c0d88d71",
    "1d2130652218ebeafe5ad2c74b64a00f133517d9b62a8c6e9b91630c8ee2174e",
    "821d38e6c6a5d2f6429845383d67e3c64f65f79dc9511946c3473f303f7f523d",
    "f73042d540678cfc4e59e40ddebd089fddf444db3266f077a4baf0d166510844",
    "b78a8987fe705495ae5afe8e47485a435a1a6c976bcba3e13f26adeb82e56aab",
    "584aebb7f29a8c688c235a14556425671a16625309186be96c92f47494c9124f",
    "5b60143c75aa60764cb1089ee28a5c3893dda9cb0cbb99b8c8e081fb113dad2e",
    "221a33a25080e393b6f1cfe03d721cc5a89b38d71ce30d7537f04116b9ecd143",
    "17d703cf8e4b4bb769b2f277ec327b5e7426e12c9d316e9e440468288ef07264",
    "f1d3c336a809eeafa1c8e29ff4ca149f83fea13f32bdca80429b925e3154b368",
)


def canonical_json_sha256(value):
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized_text_sha256(path):
    text = (
        path.read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class GoldenContractTest(unittest.TestCase):
    def test_check_set_has_release_scale_domain_and_rule_family_coverage(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual(50, len({case["id"] for case in cases}))

        domains = ("article", "business", "marketing", "mixed", "ux")
        self.assertEqual(
            {domain: 10 for domain in domains},
            {domain: sum(case["domain"] == domain for case in cases) for domain in domains},
        )
        for domain in domains:
            domain_cases = [case for case in cases if case["domain"] == domain]
            self.assertTrue(any(case["expected_rules"] for case in domain_cases))
            self.assertTrue(any(not case["expected_rules"] for case in domain_cases))

        expected_families = {
            rule.split("-")[1]
            for case in cases
            for rule in case["expected_rules"]
        }
        self.assertTrue(
            {"TYP", "PUN", "GRM", "INF", "UX", "BIZ", "ANT", "ADD"}.issubset(
                expected_families
            )
        )

        protected_types = {
            span["type"]
            for case in cases
            for span in case["protected_spans"]
        }
        self.assertTrue(
            {"code", "command", "url", "foreign", "quotation", "filename"}.issubset(
                protected_types
            )
        )
        for case in cases:
            required_fields = {
                "id", "domain", "text", "expected_text", "expected_rules", "protected_spans"
            }
            self.assertTrue(required_fields.issubset(case))
            self.assertTrue(set(case).issubset(required_fields | {"accepted_corrections"}))
            self.assertTrue(case["text"].strip())
            self.assertTrue(case["expected_text"].strip())
            accepted = case.get("accepted_corrections", [case["expected_text"]])
            self.assertIn(case["expected_text"], accepted)
            self.assertEqual(len(accepted), len(set(accepted)))
            if case["expected_rules"]:
                self.assertNotIn(case["text"], accepted)
            else:
                self.assertEqual(case["text"], case["expected_text"])
            for span in case["protected_spans"]:
                self.assertIn(span["text"], case["text"])
                self.assertIn(span["text"], case["expected_text"])

    def test_check_corrections_do_not_invent_missing_operational_facts(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in cases}

        self.assertEqual(
            "Հանդիպման ամփոփում\nՊետք է որոշել՝ ով և մինչև երբ կպատրաստի ամսական "
            "հաշվետվությունը։ Հաջորդ հանդիպումը երկուշաբթի է։",
            by_id["business-03"]["expected_text"],
        )
        self.assertEqual(
            "Կցել եմ contract.pdf ֆայլը։ Խնդրում եմ ստուգել այն և պատասխանել մինչև "
            "չորեքշաբթի։",
            by_id["business-05"]["expected_text"],
        )
        self.assertEqual(
            "Մեր թիմը պատրաստ է օգնել նոր հաճախորդներին։",
            by_id["marketing-01"]["expected_text"],
        )
        self.assertEqual(
            "Պատվերը հասել է երկուշաբթի՝ սահմանված ժամկետից ուշ։",
            by_id["marketing-05"]["expected_text"],
        )

    def test_check_corrections_do_not_add_unsupported_times_or_payment_instruments(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        payment_instruments = ("քարտ", "բանկային հաշիվ", "կանխիկ")

        for case in cases:
            corrections = case.get("accepted_corrections", [case["expected_text"]])
            source_times = set(re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", case["text"]))
            for correction in corrections:
                with self.subTest(case=case["id"], correction=correction):
                    self.assertTrue(
                        set(re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", correction)).issubset(
                            source_times
                        )
                    )
                    for instrument in payment_instruments:
                        if instrument not in case["text"]:
                            self.assertNotIn(instrument, correction)

    def test_check_release_results_are_complete_and_pass_quality_gates(self):
        module = __import__("importlib.util").util
        spec = module.spec_from_file_location("hy_text_evaluate_for_golden", ROOT / "tools" / "evaluate.py")
        evaluate = module.module_from_spec(spec)
        spec.loader.exec_module(evaluate)
        golden = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        results = json.loads(
            (ROOT / "tests" / "calibration" / "v1.0.0" / "check-results.json").read_text(
                encoding="utf-8"
            )
        )

        metrics = evaluate.detection_metrics(golden, results)

        self.assertEqual(50, metrics["case_count"])
        self.assertGreaterEqual(metrics["recall"], 0.90)
        self.assertLessEqual(metrics["clean_false_positive_rate"], 0.05)
        self.assertEqual(0, metrics["protected_mutations"])
        self.assertEqual(0, metrics["correction_failures"])
        self.assertEqual(1.0, metrics["correction_accuracy"])

    def test_scoring_set_has_fifty_arman_reviewed_cases(self):
        cases = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual({"article", "business", "marketing", "mixed", "ux"}, {case["domain"] for case in cases})
        for case in cases:
            self.assertEqual({"typography", "language", "grammar", "structure", "reader"}, set(case["scores"]))
            self.assertTrue(case["reviewed"], "every scoring fixture must carry Arman's explicit review")

        by_id = {case["id"]: case for case in cases}
        self.assertEqual(
            "Բացեք config/app.php ֆայլը և փոխեք locale-ի արժեքը։",
            by_id["mixed-05"]["text"],
        )
        self.assertEqual(
            "API-ի պատասխանը պարունակում է `{\"status\":\"ok\"}` տողը։",
            by_id["mixed-06"]["text"],
        )
        self.assertEqual(
            {
                "typography": 4,
                "language": 9,
                "grammar": 4,
                "structure": 9,
                "reader": 9,
            },
            by_id["article-03"]["scores"],
        )
        readme = (ROOT / "tests" / "golden" / "README.md").read_text(encoding="utf-8")
        self.assertIn("article-03", readme)
        self.assertIn("human re-review on 2026-08-15", readme)

    def test_second_human_adjudication_is_exact_and_preserves_fixture_identity(self):
        cases = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual(
            [
                f"{domain}-{number:02d}"
                for domain in ("article", "business", "marketing", "mixed", "ux")
                for number in range(1, 11)
            ],
            [case["id"] for case in cases],
        )
        self.assertTrue(all(case["reviewed"] for case in cases))

        identity = hashlib.sha256(
            "".join(f'{case["id"]}\0{case["text"]}\n' for case in cases).encode()
        ).hexdigest()
        self.assertEqual(
            "07386b8a8135abc5065d624b4063950304e3ec528ffb3d40a1141dcf274b4219",
            identity,
        )

        by_id = {case["id"]: case for case in cases}
        expected = {
            "article-05": {"typography": 9, "language": 4, "grammar": 9, "structure": 6, "reader": 2},
            "marketing-04": {"typography": 9, "language": 3, "grammar": 9, "structure": 5, "reader": 2},
            "ux-02": {"typography": 9, "language": 7, "grammar": 9, "structure": 6, "reader": 3},
        }
        for case_id, scores in expected.items():
            self.assertEqual(scores, by_id[case_id]["scores"])

        unchanged = hashlib.sha256(
            "".join(
                f'{case["id"]}\0{json.dumps(case["scores"], sort_keys=True, separators=(",", ":"))}\n'
                for case in cases
                if case["id"] not in expected
            ).encode()
        ).hexdigest()
        self.assertEqual(
            "198c414c4f711999f3099d5bc8f704ebdf7fc54c24ca0ecfe3b0c4abcbe7b704",
            unchanged,
        )

    def test_score_release_evidence_is_exact_complete_and_passing(self):
        module = __import__("importlib.util").util
        spec = module.spec_from_file_location(
            "hy_text_evaluate_for_score_evidence", ROOT / "tools" / "evaluate.py"
        )
        evaluate = module.module_from_spec(spec)
        spec.loader.exec_module(evaluate)

        calibration = ROOT / "tests" / "calibration" / "v1.0.0"
        golden_path = ROOT / "tests" / "golden" / "scoring.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        canonical_ids = [case["id"] for case in golden]
        dimensions = ("typography", "language", "grammar", "structure", "reader")
        all_runs = []

        expected_pass_hashes = {
            1: "1bd45b76a2eac5abf292fc510490e13714231f9f8a02bb8aecc668be95d6383d",
            2: "471949b53e6f2b88141841a48515f570134328f824c4934e0b357bb47457cde4",
            3: "95ff36ba9f7473054b005e2940b82a179b1c55ed44b2e4c191cca7ccf385202d",
        }
        for run in range(1, 4):
            path = calibration / f"pass-{run}.json"
            records = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(expected_pass_hashes[run], canonical_json_sha256(records))
            self.assertEqual(50, len(records))
            self.assertEqual(canonical_ids, [record["id"] for record in records])
            self.assertEqual(50, len({record["id"] for record in records}))
            for record in records:
                self.assertEqual({"id", "run", "scores"}, set(record))
                self.assertEqual(run, record["run"])
                self.assertNotIsInstance(record["run"], bool)
                self.assertEqual(dimensions, tuple(record["scores"]))
                for score in record["scores"].values():
                    self.assertIsInstance(score, (int, float))
                    self.assertNotIsInstance(score, bool)
                    self.assertGreaterEqual(score, 0)
                    self.assertLessEqual(score, 10)
            all_runs.extend(records)

        self.assertEqual(150, len(all_runs))
        self.assertEqual(150, len({(record["run"], record["id"]) for record in all_runs}))
        self.assertEqual(
            "67a82e617697874b2c3cb57f4fa8ecb9099333eaed10b73b4debb54c9721c7e1",
            canonical_json_sha256(all_runs),
        )

        metrics = evaluate.score_calibration(golden, all_runs)
        self.assertTrue(metrics["passed"])
        self.assertEqual([], metrics["failing_cases"])
        self.assertEqual(150, metrics["run_completeness"]["actual_results"])
        self.assertTrue(metrics["run_completeness"]["complete"])
        self.assertLessEqual(metrics["max_total_deviation"], 0.7)
        self.assertLessEqual(metrics["max_dimension_deviation"], 1.0)

        summary = json.loads((calibration / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "176dd8f459da89a6ed20ead17cba0ea8466c9abe",
            summary["provenance"]["source_head"],
        )
        self.assertEqual(
            canonical_json_sha256(golden),
            summary["provenance"]["golden"]["sha256"],
        )
        for relative, digest in summary["provenance"]["rubric"]["files"].items():
            self.assertEqual(normalized_text_sha256(ROOT / relative), digest)
        integrity = summary["provenance"]["integrity_statement"]
        for word in ("edited", "filtered", "discarded", "substituted", "averaged"):
            self.assertIn(word, integrity)

        recorded_chunk_hashes = tuple(
            summary["chunk_hashes"][f"pass-{run}"][f"chunk-{chunk:02d}"]["sha256"]
            for run in range(1, 4)
            for chunk in range(1, 11)
        )
        self.assertEqual(ROUND10_CHUNK_SHA256, recorded_chunk_hashes)
        for run in range(1, 4):
            evidence = summary["assembled_hashes"][f"pass-{run}"]
            self.assertEqual(50, evidence["records"])
            self.assertEqual(expected_pass_hashes[run], evidence["sha256"])
        self.assertEqual(150, summary["assembled_hashes"]["all-runs"]["records"])
        self.assertEqual(
            canonical_json_sha256(all_runs),
            summary["assembled_hashes"]["all-runs"]["sha256"],
        )
        self.assertEqual(0, summary["evaluator"]["exit_code"])
        self.assertEqual(
            {"max_total_deviation": 0.7, "max_dimension_deviation": 1.0},
            summary["evaluator"]["thresholds"],
        )
        self.assertEqual(metrics, summary["evaluator"]["result"])

    def test_protected_content_cases_cover_all_types(self):
        cases = json.loads((ROOT / "tests" / "golden" / "protected.json").read_text(encoding="utf-8"))
        self.assertEqual({"code", "command", "foreign", "quote", "url"}, {case["type"] for case in cases})
        for case in cases:
            self.assertIn(case["protected"], case["input"])

    def test_score_skill_requires_independent_dimension_evidence(self):
        skill = (ROOT / "skills" / "hy-score" / "SKILL.md").read_text(encoding="utf-8")
        for fragment in ("50 բառից կարճ", "9.0", "10.0", "separate observable effect"):
            self.assertIn(fragment, skill)
        self.assertIn("One issue does not automatically lower every dimension", skill)
        self.assertIn("exclude the complete span from deductions", skill)

    def test_grammar_008_golden_cases_preserve_every_protected_class(self):
        cases = json.loads(
            (ROOT / "tests" / "golden" / "hy-grm-008-protected.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                "code",
                "command",
                "url",
                "email",
                "identifier",
                "filename",
                "foreign-quotation",
                "protected-official-spelling",
            },
            {case["type"] for case in cases},
        )
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["input"], case["expected"])
                self.assertIn("Apricodeում", case["protected"])
                self.assertIn(case["protected"], case["input"])
                self.assertEqual([], case["expected_findings"])

    def test_ci_covers_three_operating_systems(self):
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        for runner in ("windows-latest", "macos-latest", "ubuntu-latest"):
            self.assertIn(runner, workflow)


if __name__ == "__main__":
    unittest.main()
