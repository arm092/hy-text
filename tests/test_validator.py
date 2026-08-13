import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "validate.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("hy_text_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidatorTest(unittest.TestCase):
    def test_repository_passes_validator(self):
        validator = load_validator()
        self.assertEqual([], validator.validate_repository(ROOT))

    def test_non_nfc_text_is_rejected(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.md"
            path.write_text("e\u0301", encoding="utf-8")
            errors = validator.validate_nfc([path])
        self.assertTrue(any("NFC" in error for error in errors))

    def test_jsonl_is_included_in_nfc_validation(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "observations.jsonl"
            path.write_text('{"variant":"e\u0301"}\n', encoding="utf-8")

            self.assertIn(path, validator.text_files(root))
            errors = validator.validate_nfc([path])

        self.assertTrue(any("NFC" in error for error in errors), errors)

    def test_invalid_utf8_is_a_validation_error_not_an_exception(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_bytes(b"\xff\xfe\n")

            errors = validator.validate_nfc([path])

        self.assertTrue(any("UTF-8" in error for error in errors), errors)

    def test_duplicate_rule_id_is_rejected(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "a.md"
            second = Path(directory) / "b.md"
            first.write_text("## HY-TYP-001\n", encoding="utf-8")
            second.write_text("## HY-TYP-001\n", encoding="utf-8")
            errors = validator.validate_rule_ids([first, second])
        self.assertTrue(any("duplicate" in error.lower() for error in errors))

    def test_unknown_source_id_is_rejected(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sources.md"
            rule = root / "rules.md"
            source.write_text("| SRC-KNOWN | official | x | y |\n", encoding="utf-8")
            rule.write_text("**Հիմք։** պաշտոնական նորմ – SRC-MISSING։\n", encoding="utf-8")
            errors = validator.validate_source_ids([rule], source)
        self.assertTrue(any("SRC-MISSING" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
