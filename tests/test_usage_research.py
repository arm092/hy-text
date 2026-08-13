import importlib.util
import json
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
            "fewer than 20 domains": {"domains": self.aggregate["domains"][:19]},
            "fewer than three positive layers": {
                "layers": {"commercial": 50, "government": 50, "media": 0}
            },
            "variant total mismatch": {"variants": {"hyphen-minus": 99}},
            "duplicate domains": {
                "domains": self.aggregate["domains"][:-1]
                + [self.aggregate["domains"][0]]
            },
            "malformed date": {"collected_at": "2026-02-30"},
            "example over 240 characters": {"examples": ["x" * 241]},
        }
        for name, replacement in cases.items():
            with self.subTest(name=name):
                invalid = dict(self.aggregate)
                invalid.update(replacement)
                self.assertTrue(self.validate(invalid), name)


if __name__ == "__main__":
    unittest.main()
