import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
AGGREGATOR_PATH = ROOT / "tools" / "aggregate_usage.py"
VALIDATOR_PATH = ROOT / "tools" / "validate.py"
AGGREGATE_SCHEMA_PATH = ROOT / "research" / "aggregate.schema.json"
OBSERVATION_SCHEMA_PATH = ROOT / "research" / "observation.schema.json"


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
            "url": f"https://www.example-{index % domains}.am/article/{index}",
            "domain": f"www.example-{index % domains}.am",
            "layer": layer_names[index % layers],
            "variant": "hyphen-minus" if index % 2 == 0 else "armenian-hyphen",
            "observed_at": "2026-08-13",
            "example": f"Short example {index}",
        }
        for index in range(total)
    ]


def usage_registry(*rows):
    lines = [
        "# Sources",
        "",
        "| Usage ID | Aggregate | Observations | Scope |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {aggregate_id} | `{aggregate_path}` | `{observation_path}` | test scope |"
        for aggregate_id, aggregate_path, observation_path in rows
    )
    return "\n".join(lines) + "\n"


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
        observations[0]["url"] = "HTTPS://WWW.EXAMPLE-0.AM/article/0"
        observations[0]["domain"] = "WWW.EXAMPLE-0.AM"

        result = aggregate_usage.build_aggregate(
            list(reversed(observations)),
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(sorted(result["domains"]), result["domains"])
        self.assertIn("example-0.am", result["domains"])
        self.assertEqual(sorted(result["variants"]), list(result["variants"]))
        self.assertEqual(sorted(result["layers"]), list(result["layers"]))
        self.assertEqual(sorted(result["examples"]), result["examples"])

    def test_subdomains_use_the_manually_verified_independence_key(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            domain = f"example-{index % 20}.am"
            observation["url"] = f"https://article-{index}.{domain}/item"
            observation["domain"] = f"WWW.{domain.upper()}."

        result = aggregate_usage.build_aggregate(
            observations,
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(20, len(result["domains"]))
        self.assertEqual("example-0.am", result["domains"][0])

    def test_idna_aliases_share_one_key_and_manual_parent_key_is_preserved(self):
        observations = make_observations(total=100, domains=20, layers=3)
        idna_key = "օրինակ.am".encode("idna").decode("ascii")
        for index in range(0, 100, 20):
            observations[index]["domain"] = "օրինակ.am" if index % 40 == 0 else idna_key
            observations[index]["url"] = (
                f"https://news.{idna_key}/article/{index}"
            )

        result = aggregate_usage.build_aggregate(
            observations,
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual(20, len(result["domains"]))
        self.assertIn(idna_key, result["domains"])
        self.assertNotIn(f"news.{idna_key}", result["domains"])

    def test_idna_mapped_legacy_ipv4_aliases_cannot_inflate_domain_threshold(self):
        fullwidth_digits = str.maketrans("0123456789", "０１２３４５６７８９")
        aliases = ["１２７.１"] + [
            f"{'0' * padding}177.0.0.1".translate(fullwidth_digits)
            for padding in range(1, 20)
        ]
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            alias = aliases[index % len(aliases)]
            observation["url"] = f"https://{alias}/article/{index}"
            observation["domain"] = alias

        with self.assertRaises(ValueError):
            aggregate_usage.build_aggregate(
                observations,
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

    def test_idna_mapped_global_legacy_ipv4_is_canonicalized(self):
        self.assertEqual(
            "8.8.8.8",
            aggregate_usage.canonical_usage_domain("０１０.０１０.０１０.０１０"),
        )

    def test_ipv6_scope_ids_cannot_inflate_domain_threshold(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            scoped_address = f"2001:4860:4860::8888%25z{index % 20}"
            observation["url"] = f"https://[{scoped_address}]/article/{index}"
            observation["domain"] = scoped_address

        with self.assertRaisesRegex(ValueError, "scope"):
            aggregate_usage.build_aggregate(
                observations,
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

    def test_non_public_hosts_and_addresses_are_rejected(self):
        rejected = (
            "localhost",
            "intranet",
            "127.0.0.1",
            "10.0.0.1",
            "169.254.10.2",
            "192.0.2.1",
            "224.0.0.1",
            "0.0.0.0",
            "::1",
            "fe80::1",
            "ff02::1",
            "::",
            "127.1",
            "0177.0.0.1",
            "0x7f.0.0.1",
            "１２７.１",
            "０１７７.０.０.１",
            "foo.local",
            "foo.localhost",
            "example.invalid",
            "example.test",
            "example.example",
            "example.onion",
            "service.internal",
            "printer.lan",
            "home.arpa",
            "service.home.arpa",
            "resolver.arpa",
            "x.resolver.arpa",
            "ipv4only.arpa",
            "eap.arpa",
            "6tisch.arpa",
            "10.in-addr.arpa",
            "xn--a.am",
            "faß.de",
            "xn--fa-hia.de",
            "example.com",
            "news.example.org",
            "a." * 126 + "am",
            "www." + "a." * 125 + "am",
        )
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    aggregate_usage.canonical_usage_domain(value)

        self.assertEqual(
            "example.am",
            aggregate_usage.canonical_usage_domain("WWW.EXAMPLE.AM."),
        )
        self.assertEqual(
            "8.8.8.8",
            aggregate_usage.canonical_usage_domain("8.8.8.8"),
        )
        self.assertEqual(
            "2001:4860:4860::8888",
            aggregate_usage.canonical_usage_domain("2001:4860:4860::8888"),
        )

    def test_subdomains_cannot_inflate_one_independence_key(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            observation["url"] = f"https://article-{index}.example.am/item"
            observation["domain"] = "example.am"

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
        observations[1]["url"] = "HTTPS://WWW.EXAMPLE-0.AM/article/0#fragment"
        observations[1]["domain"] = "WWW.EXAMPLE-0.AM"

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

    def test_variant_labels_and_examples_are_trimmed_and_normalized_to_nfc(self):
        observations = make_observations(total=100, domains=20, layers=3)
        for index, observation in enumerate(observations):
            observation["variant"] = " e\u0301 " if index % 2 == 0 else "é"
            observation["example"] = f" Cafe\u0301 {index} "

        result = aggregate_usage.build_aggregate(
            observations,
            "USAGE-FOREIGN-SUFFIX",
            "mixed-script suffix",
        )

        self.assertEqual({"é": 100}, result["variants"])
        self.assertTrue(result["examples"])
        self.assertTrue(
            all(example == unicodedata.normalize("NFC", example) for example in result["examples"])
        )
        self.assertTrue(all(example == example.strip() for example in result["examples"]))

    def test_control_only_variant_and_example_are_rejected(self):
        for field, value in (
            ("variant", "\u200b"),
            ("example", "\u200b"),
            ("variant", "same\u200b"),
            ("example", "same\u200b"),
        ):
            observations = make_observations(total=100, domains=20, layers=3)
            observations[0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    aggregate_usage.build_aggregate(
                        observations,
                        "USAGE-FOREIGN-SUFFIX",
                        "mixed-script suffix",
                    )

    def test_verification_examples_require_a_letter_or_number(self):
        observations = make_observations(total=100, domains=20, layers=3)
        observations[0]["example"] = "."

        with self.assertRaisesRegex(ValueError, "letter or number"):
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

    def test_jsonl_loader_reports_invalid_utf8_as_a_validation_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            path.write_bytes(b"\xff\xfe\n")

            with self.assertRaisesRegex(ValueError, "UTF-8"):
                aggregate_usage.load_observations(path)


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
            "zero-count extra layer": {
                "layers": {
                    "commercial": 34,
                    "community": 0,
                    "government": 33,
                    "media": 33,
                }
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
            "empty variants": {"variants": {}},
            "blank variant": {"variants": {" ": 100}},
            "control-only variant": {"variants": {"\u200b": 100}},
            "embedded-control variant": {"variants": {"same\u200b": 100}},
            "noncanonical variant": {"variants": {"e\u0301": 100}},
            "zero-count variant": {
                "variants": {"hyphen-minus": 100, "unused": 0}
            },
            "no verification example": {"examples": []},
            "blank verification example": {"examples": [" "]},
            "control-only verification example": {"examples": ["\u200b"]},
            "embedded-control verification example": {"examples": ["same\u200b"]},
            "noncanonical verification example": {"examples": ["e\u0301"]},
            "punctuation-only verification example": {"examples": ["."]},
            "non-public domain": {
                "domains": self.aggregate["domains"][:19] + ["127.0.0.1"]
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
        observations[0]["url"] = "https://article.example-0.am/item"
        observations[0]["domain"] = "EXAMPLE-0.AM."

        self.assertEqual([], self.validate(observations))

    def test_unsafe_and_duplicate_observation_content_is_rejected(self):
        cases = {}

        extra_field = make_observations(total=2, domains=2, layers=2)
        extra_field[0]["page_text"] = "copied page"
        cases["full page field"] = extra_field

        long_example = make_observations(total=2, domains=2, layers=2)
        long_example[0]["example"] = "x" * 241
        cases["long example"] = long_example

        punctuation_example = make_observations(total=2, domains=2, layers=2)
        punctuation_example[0]["example"] = "."
        cases["punctuation-only example"] = punctuation_example

        duplicate_url = make_observations(total=2, domains=2, layers=2)
        duplicate_url[1]["url"] = duplicate_url[0]["url"]
        duplicate_url[1]["domain"] = duplicate_url[0]["domain"]
        cases["duplicate URL"] = duplicate_url

        for name, observations in cases.items():
            with self.subTest(name=name):
                self.assertTrue(self.validate(observations), name)

    def test_invalid_utf8_is_reported_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            path.write_bytes(b"\xff\xfe\n")

            errors = validator.validate_usage_observations([path])

        self.assertTrue(errors)
        self.assertTrue(any("UTF-8" in error for error in errors), errors)

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


class UsageChainOfCustodyTest(unittest.TestCase):
    def make_repository(self, directory, *, stem="foreign-suffix", aggregate_id="USAGE-FOREIGN-SUFFIX"):
        root = Path(directory)
        aggregate_directory = root / "research" / "aggregates"
        observation_directory = root / "research" / "observations"
        rule_directory = root / "skills" / "hy-text" / "references"
        aggregate_directory.mkdir(parents=True)
        observation_directory.mkdir(parents=True)
        rule_directory.mkdir(parents=True)

        observations = make_observations()
        observation_path = observation_directory / f"{stem}.jsonl"
        observation_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in observations) + "\n",
            encoding="utf-8",
        )
        aggregate = aggregate_usage.build_aggregate(
            observations,
            aggregate_id,
            "mixed-script suffix",
        )
        aggregate_path = aggregate_directory / f"{stem}.json"
        aggregate_path.write_text(
            json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        source_path = rule_directory / "sources.md"
        source_path.write_text(
            usage_registry(
                (
                    aggregate_id,
                    f"research/aggregates/{stem}.json",
                    f"research/observations/{stem}.jsonl",
                )
            ),
            encoding="utf-8",
        )
        rule_path = rule_directory / "rules.md"
        rule_path.write_text(
            "## HY-INF-999\n\n"
            f"**Հիմք։** ժամանակակից գործածություն – {aggregate_id}։\n",
            encoding="utf-8",
        )
        return root, aggregate_path, observation_path, source_path, rule_path

    def validate(self, root, source_path, rule_path):
        return validator.validate_usage_chain(root, [rule_path], source_path)

    def test_registered_aggregate_is_recomputed_from_same_stem_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            root, aggregate_path, observation_path, source_path, rule_path = self.make_repository(directory)

            self.assertEqual([], self.validate(root, source_path, rule_path))

            aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
            aggregate["variants"] = {"armenian-hyphen": 49, "hyphen-minus": 51}
            aggregate_path.write_text(json.dumps(aggregate), encoding="utf-8")
            mismatch_errors = self.validate(root, source_path, rule_path)

            observation_path.unlink()
            missing_errors = self.validate(root, source_path, rule_path)

        self.assertTrue(any("recomputed" in error for error in mismatch_errors), mismatch_errors)
        self.assertTrue(any("paired observations" in error for error in missing_errors), missing_errors)

    def test_usage_id_filename_registry_and_modern_basis_are_one_to_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root, aggregate_path, _, source_path, rule_path = self.make_repository(
                directory,
                stem="wrong-stem",
            )
            errors = self.validate(root, source_path, rule_path)
            self.assertTrue(any("filename" in error and "USAGE-FOREIGN-SUFFIX" in error for error in errors), errors)

            source_path.write_text(usage_registry(), encoding="utf-8")
            errors = self.validate(root, source_path, rule_path)
            self.assertTrue(any("not registered" in error for error in errors), errors)

            rule_path.write_text(
                "## HY-INF-999\n\n**Հիմք։** ժամանակակից գործածություն – SRC-EDITORIAL-POLICY։\n",
                encoding="utf-8",
            )
            errors = self.validate(root, source_path, rule_path)
            self.assertTrue(any("must reference" in error for error in errors), errors)

            ghost_id = "USAGE-GHOST-STUDY"
            source_path.write_text(
                usage_registry(
                    (
                        ghost_id,
                        "research/aggregates/ghost-study.json",
                        "research/observations/ghost-study.jsonl",
                    )
                ),
                encoding="utf-8",
            )
            rule_path.write_text(
                f"## HY-INF-999\n\n**Հիմք։** ժամանակակից գործածություն – {ghost_id}։\n",
                encoding="utf-8",
            )
            errors = self.validate(root, source_path, rule_path)
            self.assertTrue(any("registered aggregate" in error and "does not exist" in error for error in errors), errors)

    def test_multiline_modern_basis_cannot_bypass_aggregate_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            basis_forms = (
                "**Հիմք։**\nժամանակակից գործածություն – USAGE-GHOST։",
                "**Հիմք։** Ժամանակակից գործածություն – USAGE-GHOST։",
                "**Հիմք։** ժամանակակից\nգործածություն – USAGE-GHOST։",
                "  **Հիմք։** ժամանակակից գործածություն – USAGE-GHOST։",
                "> **Հիմք։** ժամանակակից գործածություն – USAGE-GHOST։",
                "- **Հիմք։** ժամանակակից գործածություն – USAGE-GHOST։",
                "**Հիմք։** ժամանակակից\u00a0գործածություն – USAGE-GHOST։",
                "**Հիմք։** ժամանակակից **գործածություն** – USAGE-GHOST։",
            )
            for basis in basis_forms:
                with self.subTest(basis=basis):
                    rule_path.write_text(
                        "## HY-INF-999\n\n"
                        f"{basis}\n\n"
                        "**Կիրառություն։** օրինակ։\n",
                        encoding="utf-8",
                    )

                    errors = self.validate(root, source_path, rule_path)

                    self.assertTrue(
                        any(
                            "references unregistered or missing aggregate USAGE-GHOST" in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_intra_word_markdown_cannot_hide_a_modern_usage_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            basis_forms = (
                "**Հիմք։** ժամանակակից գոր**ծա**ծություն – SRC-EDITORIAL-POLICY։",
                "  **Հիմք։** ԺԱՄԱՆԱ**ԿԱԿԻՑ**\n  գոր__ծա__ծություն – SRC-EDITORIAL-POLICY։",
                "> **Հիմք։** ժամանակակից գոր~~ծա~~ծություն – SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր[ծա](https://example.am)ծություն "
                "– SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր[ծա](https://example.am/a((b)))ծություն "
                "– SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր[ծա]ծություն – SRC-EDITORIAL-POLICY։\n\n"
                "[ծա]: https://example.am",
                "**Հիմք։** ժամանակակից գոր<em>ծա</em>ծություն – SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր<em title=\">\">ծա</em>ծություն "
                "– SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր<em\n title=\"x\">ծա</em>ծություն "
                "– SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր<!---->ծածություն – SRC-EDITORIAL-POLICY։",
                "**Հիմք։** ժամանակակից գոր<?target?>ծածություն "
                "– SRC-EDITORIAL-POLICY։",
            )
            for basis in basis_forms:
                with self.subTest(basis=basis):
                    rule_path.write_text(
                        "## HY-INF-999\n\n"
                        f"{basis}\n\n"
                        "**Կիրառություն։** օրինակ։\n",
                        encoding="utf-8",
                    )

                    errors = self.validate(root, source_path, rule_path)

                    self.assertTrue(
                        any("modern usage must reference" in error for error in errors),
                        errors,
                    )

    def test_escaped_reference_label_cannot_hide_a_modern_usage_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            rule_path.write_text(
                "## HY-INF-999\n\n"
                "**Հիմք։** ժամանակակից գոր[ծա][ref\\]x]ծություն "
                "– SRC-EDITORIAL-POLICY։\n\n"
                "[ref\\]x]: https://example.am\n\n"
                "**Կիրառություն։** օրինակ։\n",
                encoding="utf-8",
            )

            errors = self.validate(root, source_path, rule_path)

        self.assertTrue(
            any("modern usage must reference" in error for error in errors),
            errors,
        )

    def test_hidden_html_comment_cannot_swallow_a_visible_modern_usage_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            rule_path.write_text(
                "## HY-INF-999\n\n"
                "**Հիմք։** <!-- ](\" -->ժամանակակից գործածություն<!-- \" ) --> "
                "– SRC-EDITORIAL-POLICY։\n\n"
                "**Կիրառություն։** օրինակ։\n",
                encoding="utf-8",
            )

            errors = self.validate(root, source_path, rule_path)

        self.assertTrue(
            any("modern usage must reference" in error for error in errors),
            errors,
        )

    def test_whitespace_controls_preserve_modern_usage_word_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            basis_forms = (
                "նշում\nժամանակակից գործածություն – SRC-EDITORIAL-POLICY։",
                "նշում\tժամանակակից գործածություն – SRC-EDITORIAL-POLICY։",
                "ժամանակակից գործածություն\nհավելում – SRC-EDITORIAL-POLICY։",
                "ժամանակակից գործածություն\tհավելում – SRC-EDITORIAL-POLICY։",
            )
            for basis in basis_forms:
                with self.subTest(basis=ascii(basis)):
                    rule_path.write_text(
                        "## HY-INF-999\n\n"
                        f"**Հիմք։** {basis}\n\n"
                        "**Կիրառություն։** օրինակ։\n",
                        encoding="utf-8",
                    )

                    errors = self.validate(root, source_path, rule_path)

                    self.assertTrue(
                        any("modern usage must reference" in error for error in errors),
                        errors,
                    )

    def test_format_controls_cannot_hide_a_modern_usage_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            basis_forms = [
                f"ժամանակակից գոր{character}ծածություն"
                for character in ("\u200b", "\u2060", "\x00", "\ufe0f")
            ] + [
                f"ժամա{character}նակակից գործածություն"
                for character in ("\u200b", "\u2060", "\x00", "\ufe0f")
            ] + [
                f"ժամանակակից{character}գործածություն"
                for character in ("\u200b", "\u2060", "\x00")
            ]
            for basis in basis_forms:
                with self.subTest(basis=ascii(basis)):
                    rule_path.write_text(
                        "## HY-INF-999\n\n"
                        f"**Հիմք։** {basis} "
                        "– SRC-EDITORIAL-POLICY։\n\n"
                        "**Կիրառություն։** օրինակ։\n",
                        encoding="utf-8",
                    )

                    errors = self.validate(root, source_path, rule_path)

                    self.assertTrue(
                        any("modern usage must reference" in error for error in errors),
                        errors,
                    )

    def test_unrelated_text_does_not_trigger_modern_usage_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            basis_forms = (
                "**Հիմք։** խմբագրական որոշում՝ ժամանակակից լեզվի գործածություն։",
                "**Հիմք։** նախաժամանակակից գործածություն։",
                "**Հիմք։** նախ**ժամանակակից** գործածություն։",
                "**Հիմք։** նախ\u0301ժամանակակից գործածություն։",
                "**Հիմք։** նախ\u200bժամանակակից գործածություն։",
                "**Հիմք։** ժամանակակից գործածությունային օրինակ։",
                "**Հիմք։** ժամանակակից գործածություն\u200bային օրինակ։",
            )
            for basis in basis_forms:
                with self.subTest(basis=basis):
                    rule_path.write_text(
                        "## HY-INF-999\n\n"
                        f"{basis}\n\n"
                        "**Կիրառություն։** օրինակ։\n",
                        encoding="utf-8",
                    )

                    errors = self.validate(root, source_path, rule_path)

                    self.assertEqual([], errors)

    def test_every_usage_reference_is_resolved_even_without_a_modern_basis_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            rule_path.write_text(
                "## HY-INF-999\n\n"
                "**Հիմք։** խմբագրական որոշում – USAGE-GHOST-STUDY։\n",
                encoding="utf-8",
            )

            errors = self.validate(root, source_path, rule_path)

        self.assertTrue(
            any(
                "references unregistered or missing aggregate USAGE-GHOST-STUDY" in error
                for error in errors
            ),
            errors,
        )

    def test_usage_registry_paths_cannot_escape_the_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _, source_path, rule_path = self.make_repository(directory)
            source_path.write_text(
                usage_registry(
                    (
                        "USAGE-FOREIGN-SUFFIX",
                        "../../foreign-suffix.json",
                        "../../foreign-suffix.jsonl",
                    )
                ),
                encoding="utf-8",
            )

            errors = self.validate(root, source_path, rule_path)

        self.assertTrue(any("registry paths must be" in error for error in errors), errors)

    def test_duplicate_aggregate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, aggregate_path, observation_path, source_path, rule_path = self.make_repository(directory)
            duplicate_aggregate = aggregate_path.with_name("duplicate-study.json")
            duplicate_observations = observation_path.with_name("duplicate-study.jsonl")
            duplicate_aggregate.write_bytes(aggregate_path.read_bytes())
            duplicate_observations.write_bytes(observation_path.read_bytes())

            errors = self.validate(root, source_path, rule_path)

        self.assertTrue(any("duplicate aggregate ID" in error for error in errors), errors)

    def test_unaggregated_observations_are_allowed_while_research_is_in_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observation_directory = root / "research" / "observations"
            reference_directory = root / "skills" / "hy-text" / "references"
            observation_directory.mkdir(parents=True)
            reference_directory.mkdir(parents=True)
            observation_path = observation_directory / "draft-study.jsonl"
            observation_path.write_text(
                json.dumps(make_observations(total=1)[0]) + "\n",
                encoding="utf-8",
            )
            source_path = reference_directory / "sources.md"
            source_path.write_text(usage_registry(), encoding="utf-8")
            rule_path = reference_directory / "rules.md"
            rule_path.write_text("# No modern-usage rules\n", encoding="utf-8")

            errors = self.validate(root, source_path, rule_path)

        self.assertEqual([], errors)


class UsageSchemaContractTest(unittest.TestCase):
    def test_observation_schema_matches_runtime_shape_and_url_scheme_acceptance(self):
        schema = json.loads(OBSERVATION_SCHEMA_PATH.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(set(aggregate_usage.REQUIRED_FIELDS), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(sorted(aggregate_usage.ALLOWED_LAYERS), sorted(properties["layer"]["enum"]))
        self.assertEqual(1, properties["variant"]["minLength"])
        self.assertEqual("\\S", properties["variant"]["pattern"])
        self.assertEqual(1, properties["example"]["minLength"])
        self.assertEqual(240, properties["example"]["maxLength"])
        self.assertEqual("\\S", properties["example"]["pattern"])
        self.assertIn("letter or number", properties["example"]["description"])
        self.assertIn("runtime", properties["url"]["description"].lower())

        pattern = re.compile(properties["url"]["pattern"])
        accepted = ("https://example.am/a", "HTTPS://օրինակ.am/էջ")
        rejected = ("ftp://example.am/a", "https://user@example.am/a", "https://example.am/a b")
        for value in accepted:
            with self.subTest(value=value):
                self.assertIsNotNone(pattern.fullmatch(value))
                aggregate_usage.normalized_public_url(value)
        for value in rejected:
            with self.subTest(value=value):
                self.assertIsNone(pattern.fullmatch(value))
                with self.assertRaises(ValueError):
                    aggregate_usage.normalized_public_url(value)

    def test_aggregate_schema_requires_meaningful_evidence_collections(self):
        schema = json.loads(AGGREGATE_SCHEMA_PATH.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual("^USAGE-[A-Z0-9]+(?:-[A-Z0-9]+)*$", properties["id"]["pattern"])
        self.assertEqual(1, properties["variants"]["minProperties"])
        self.assertEqual("\\S", properties["query"]["pattern"])
        self.assertEqual("\\S", properties["variants"]["propertyNames"]["pattern"])
        self.assertEqual(1, properties["variants"]["additionalProperties"]["minimum"])
        self.assertEqual(3, properties["layers"]["minProperties"])
        self.assertEqual(len(aggregate_usage.ALLOWED_LAYERS), properties["layers"]["maxProperties"])
        self.assertEqual(
            sorted(aggregate_usage.ALLOWED_LAYERS),
            sorted(properties["layers"]["propertyNames"]["enum"]),
        )
        self.assertEqual(1, properties["layers"]["additionalProperties"]["minimum"])
        self.assertEqual(1, properties["examples"]["minItems"])
        self.assertEqual(1, properties["examples"]["items"]["minLength"])
        self.assertEqual("\\S", properties["examples"]["items"]["pattern"])
        self.assertIn("letter or number", properties["examples"]["items"]["description"])


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

    def test_cli_rejects_identical_paths_without_changing_the_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            self.write_observations(path)
            original = path.read_bytes()

            completed = self.run_cli(path, path)

            self.assertEqual(original, path.read_bytes())
        self.assertEqual(1, completed.returncode)
        self.assertIn("same file", completed.stderr)

    def test_cli_rejects_hard_link_aliases_without_changing_the_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "observations.jsonl"
            output_path = root / "aggregate.json"
            self.write_observations(input_path)
            original = input_path.read_bytes()
            try:
                os.link(input_path, output_path)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")

            completed = self.run_cli(input_path, output_path)

            self.assertEqual(original, input_path.read_bytes())
            self.assertEqual(original, output_path.read_bytes())
        self.assertEqual(1, completed.returncode)
        self.assertIn("same file", completed.stderr)

    def test_atomic_write_preserves_existing_output_when_replace_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_path = root / "aggregate.json"
            output_path.write_text("existing output\n", encoding="utf-8")
            aggregate = aggregate_usage.build_aggregate(
                make_observations(),
                "USAGE-FOREIGN-SUFFIX",
                "mixed-script suffix",
            )

            with mock.patch.object(
                aggregate_usage.os,
                "replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    aggregate_usage.write_aggregate_atomic(output_path, aggregate)

            remaining = sorted(path.name for path in root.iterdir())
            self.assertEqual("existing output\n", output_path.read_text(encoding="utf-8"))
            self.assertEqual(["aggregate.json"], remaining)

if __name__ == "__main__":
    unittest.main()
