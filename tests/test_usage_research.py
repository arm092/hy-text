import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGGREGATOR_PATH = ROOT / "tools" / "aggregate_usage.py"
VALIDATOR_PATH = ROOT / "tools" / "validate.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aggregate_usage = load_module("aggregate_usage", AGGREGATOR_PATH)
validator = load_module("usage_validator", VALIDATOR_PATH)


def make_observations(total=100, domains=20, layers=3):
    layer_names = ["government", "media", "commercial", "professional", "community"]
    return [
        {
            "url": f"https://www.example-{index % domains}.test/article/{index}",
            "domain": f"www.example-{index % domains}.test",
            "layer": layer_names[index % layers],
            "variant": "hyphen-minus" if index % 2 == 0 else "armenian-hyphen",
            "observed_at": "2026-08-13",
            "example": f"Short example {index}",
        }
        for index in range(total)
    ]


class UsageAggregateTest(unittest.TestCase):
    def test_aggregate_requires_one_hundred_uses_twenty_domains_and_three_layers(self):
        cases = (
            make_observations(total=99, domains=20, layers=3),
            make_observations(total=100, domains=19, layers=3),
            make_observations(total=100, domains=20, layers=2),
        )
        for observations in cases:
            with self.subTest(total=len(observations)):
                with self.assertRaises(ValueError):
                    aggregate_usage.build_aggregate(
                        observations,
                        "USAGE-FOREIGN-SUFFIX",
                        "mixed-script suffix",
                    )

    def test_aggregate_counts_variants_without_storing_full_pages(self):
        observations = make_observations(total=100, domains=20, layers=3)

        result = aggregate_usage.build_aggregate(
            observations,
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(100, result["total"])
        self.assertEqual(100, sum(result["variants"].values()))
        self.assertNotIn("page_text", result)

    def test_aggregate_normalizes_domains_and_sorts_derived_values(self):
        observations = make_observations(total=100, domains=20, layers=3)
        observations[0]["url"] = "HTTPS://WWW.EXAMPLE-0.TEST/article/0"
        observations[0]["domain"] = "WWW.EXAMPLE-0.TEST"

        result = aggregate_usage.build_aggregate(
            list(reversed(observations)),
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(sorted(result["domains"]), result["domains"])
        self.assertIn("example-0.test", result["domains"])
        self.assertEqual(sorted(result["variants"]), list(result["variants"]))
        self.assertEqual(sorted(result["layers"]), list(result["layers"]))
        self.assertEqual(sorted(result["examples"]), result["examples"])

    def test_subdomains_use_the_manually_verified_independence_key(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            domain = f"example-{index % 20}.test"
            observation["url"] = f"https://article-{index}.{domain}/item"
            observation["domain"] = f"WWW.{domain.upper()}."

        result = aggregate_usage.build_aggregate(
            observations,
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(20, len(result["domains"]))
        self.assertEqual("example-0.test", result["domains"][0])

    def test_subdomains_cannot_inflate_one_independence_key(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            observation["url"] = f"https://article-{index}.example.test/item"
            observation["domain"] = "example.test"

        with self.assertRaisesRegex(ValueError, "at least 20 domains"):
            aggregate_usage.build_aggregate(
                observations,
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

    def test_observation_fields_must_match_the_schema_exactly(self):
        observations = make_observations(total=100, domains=20, layers=3)
        observations[0]["page_text"] = "full copied page"

        with self.assertRaisesRegex(ValueError, "unexpected"):
            aggregate_usage.build_aggregate(
                observations,
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

    def test_duplicate_urls_are_rejected_after_normalization(self):
        observations = make_observations(total=100, domains=20, layers=3)
        observations[1]["url"] = "HTTPS://WWW.EXAMPLE-0.TEST/article/0#fragment"
        observations[1]["domain"] = "WWW.EXAMPLE-0.TEST"

        with self.assertRaisesRegex(ValueError, "duplicate URL"):
            aggregate_usage.build_aggregate(
                observations,
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

    def test_invalid_layer_and_long_example_are_rejected(self):
        for field, value in (("layer", "search-results"), ("example", "x" * 241)):
            observations = make_observations(total=100, domains=20, layers=3)
            observations[0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    aggregate_usage.build_aggregate(
                        observations,
                        "USAGE-FOREIGN-SUFFIX",
                        "mixed-script suffix",
                    )

    def test_jsonl_loader_reads_observation_objects(self):
        rows = make_observations(total=2, domains=2, layers=2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )

            result = aggregate_usage.load_observations(path)

        self.assertEqual(rows, result)


class UsageAggregateValidatorTest(unittest.TestCase):
    def setUp(self):
        self.aggregate = aggregate_usage.build_aggregate(
            make_observations(),
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

    def validate(self, aggregate):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aggregate.json"
            path.write_text(json.dumps(aggregate), encoding="utf-8")
            return validator.validate_usage_aggregates([path])

    def test_qualifying_aggregate_is_accepted(self):
        self.assertEqual([], self.validate(self.aggregate))

    def test_nonqualifying_aggregate_conditions_are_rejected(self):
        cases = {
            "total below 100": {"total": 99},
            "no domains": {"domains": []},
            "fewer than 20 domains": {"domains": self.aggregate["domains"][:19]},
            "fewer than three positive layers": {
                "layers": {"commercial": 50, "government": 50, "media": 0}
            },
            "variant total mismatch": {"variants": {"hyphen-minus": 99}},
            "duplicate domains": {
                "domains": self.aggregate["domains"][:-1]
                + [self.aggregate["domains"][0]]
            },
            "equivalent domains": {
                "domains": self.aggregate["domains"][:19]
                + [f"WWW.{self.aggregate['domains'][0].upper()}."]
            },
            "malformed date": {"collected_at": "2026-02-30"},
            "example over 240 characters": {"examples": ["x" * 241]},
            "unknown layer": {
                "layers": {
                    "commercial": 33,
                    "government": 33,
                    "media": 33,
                    "search-results": 1,
                }
            },
            "layer total mismatch": {
                "layers": {"commercial": 33, "government": 33, "media": 33}
            },
        }
        for name, replacement in cases.items():
            with self.subTest(name=name):
                invalid = dict(self.aggregate)
                invalid.update(replacement)
                self.assertTrue(self.validate(invalid), name)

    def test_aggregate_object_contract_is_enforced(self):
        cases = {}

        missing_id = dict(self.aggregate)
        del missing_id["id"]
        cases["missing id"] = missing_id

        blank_query = dict(self.aggregate)
        blank_query["query"] = " "
        cases["blank query"] = blank_query

        invalid_exclusions = dict(self.aggregate)
        invalid_exclusions["exclusions"] = "none"
        cases["invalid exclusions"] = invalid_exclusions

        extra_field = dict(self.aggregate)
        extra_field["page_text"] = "copied page"
        cases["unexpected property"] = extra_field

        for name, invalid in cases.items():
            with self.subTest(name=name):
                self.assertTrue(self.validate(invalid), name)


class UsageObservationValidatorTest(unittest.TestCase):
    def validate(self, observations):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in observations) + "\n",
                encoding="utf-8",
            )
            return validator.validate_usage_observations([path])

    def test_qualifying_observation_rows_are_accepted_before_thresholds(self):
        observations = make_observations(total=2, domains=2, layers=2)
        observations[0]["url"] = "https://article.example-0.test/item"
        observations[0]["domain"] = "EXAMPLE-0.TEST."

        self.assertEqual([], self.validate(observations))

    def test_unsafe_and_duplicate_observation_content_is_rejected(self):
        cases = {}

        extra_field = make_observations(total=2, domains=2, layers=2)
        extra_field[0]["page_text"] = "copied page"
        cases["full page field"] = extra_field

        long_example = make_observations(total=2, domains=2, layers=2)
        long_example[0]["example"] = "x" * 241
        cases["long example"] = long_example

        duplicate_url = make_observations(total=2, domains=2, layers=2)
        duplicate_url[1]["url"] = duplicate_url[0]["url"]
        duplicate_url[1]["domain"] = duplicate_url[0]["domain"]
        cases["duplicate URL"] = duplicate_url

        for name, observations in cases.items():
            with self.subTest(name=name):
                self.assertTrue(self.validate(observations), name)

    def test_repository_discovers_aggregate_and_observation_files(self):
        aggregate_directory = ROOT / "research" / "aggregates"
        observation_directory = ROOT / "research" / "observations"
        aggregate_path = aggregate_directory / ".test-invalid.json"
        observation_path = observation_directory / ".test-invalid.jsonl"
        aggregate_directory_existed = aggregate_directory.exists()
        observation_directory_existed = observation_directory.exists()
        aggregate_directory.mkdir(exist_ok=True)
        observation_directory.mkdir(exist_ok=True)
        try:
            aggregate_path.write_text("{}\n", encoding="utf-8")
            observation = make_observations(total=1, domains=1, layers=1)[0]
            observation["page_text"] = "copied page"
            observation_path.write_text(json.dumps(observation) + "\n", encoding="utf-8")

            errors = validator.validate_repository(ROOT)
        finally:
            aggregate_path.unlink(missing_ok=True)
            observation_path.unlink(missing_ok=True)
            if not aggregate_directory_existed:
                aggregate_directory.rmdir()
            if not observation_directory_existed:
                observation_directory.rmdir()

        self.assertTrue(any(str(aggregate_path) in error for error in errors))
        self.assertTrue(any(str(observation_path) in error for error in errors))


class UsageAggregateCliTest(unittest.TestCase):
    def run_cli(self, input_path, output_path):
        return subprocess.run(
            [
                sys.executable,
                str(AGGREGATOR_PATH),
                str(input_path),
                str(output_path),
                "--id",
                "USAGE-FOREIGN-SUFFIX",
                "--query",
                "mixed-script suffix",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_observations(self, path):
        path.write_text(
            "\n".join(json.dumps(row) for row in make_observations()) + "\n",
            encoding="utf-8",
        )

    def test_cli_writes_a_qualifying_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "observations.jsonl"
            output_path = root / "nested" / "aggregate.json"
            self.write_observations(input_path)

            completed = self.run_cli(input_path, output_path)

            result = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(100, result["total"])
        self.assertEqual(20, len(result["domains"]))

    def test_cli_reports_output_errors_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "observations.jsonl"
            blocked_parent = root / "not-a-directory"
            output_path = blocked_parent / "aggregate.json"
            self.write_observations(input_path)
            blocked_parent.write_text("file", encoding="utf-8")

            completed = self.run_cli(input_path, output_path)

        self.assertEqual(1, completed.returncode)
        self.assertTrue(completed.stderr.startswith("ERROR:"), completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

if __name__ == "__main__":
    unittest.main()
