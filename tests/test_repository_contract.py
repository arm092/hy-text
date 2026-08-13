import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("hy-text", "hy-check", "hy-score")
REFERENCES = (
    "typography.md",
    "info-style.md",
    "editorial-punctuation.md",
    "editorial-grammar.md",
    "ux-writing.md",
    "business-writing.md",
    "anti-patterns.md",
    "addenda.md",
    "scoring.md",
    "sources.md",
)
RULE_RE = re.compile(r"^## (HY-[A-Z]{2,4}-\d{3})$", re.MULTILINE)


class RepositoryContractTest(unittest.TestCase):
    def test_three_public_skills_exist(self):
        for skill in SKILLS:
            self.assertTrue((ROOT / "skills" / skill / "SKILL.md").is_file(), skill)

    def test_reference_corpus_is_complete(self):
        reference_dir = ROOT / "skills" / "hy-text" / "references"
        self.assertEqual(set(REFERENCES), {path.name for path in reference_dir.glob("*.md")})

    def test_every_normative_reference_has_stable_unique_rule_ids(self):
        seen = set()
        for name in REFERENCES[:-2]:
            text = (ROOT / "skills" / "hy-text" / "references" / name).read_text(encoding="utf-8")
            ids = RULE_RE.findall(text)
            self.assertGreater(len(ids), 0, name)
            for rule_id in ids:
                self.assertNotIn(rule_id, seen)
                seen.add(rule_id)

    def test_each_rule_has_required_fields(self):
        reference_dir = ROOT / "skills" / "hy-text" / "references"
        for path in reference_dir.glob("*.md"):
            if path.name in {"scoring.md", "sources.md"}:
                continue
            text = path.read_text(encoding="utf-8")
            chunks = re.split(r"(?=^## HY-)", text, flags=re.MULTILINE)[1:]
            for chunk in chunks:
                rule_id = chunk.splitlines()[0].removeprefix("## ")
                for field in ("**Կանոն։**", "**Կիրառություն։**", "**Սխալ։**", "**Ճիշտ։**", "**Բացառություն։**", "**Խստություն։**", "**Հիմք։**"):
                    self.assertIn(field, chunk, f"{rule_id}: {field}")

    def test_score_contract_is_present(self):
        text = (ROOT / "skills" / "hy-text" / "references" / "scoring.md").read_text(encoding="utf-8")
        for fragment in ("0.15", "0.25", "0.20", "< 3.0", "< 4.0", "50 բառ", "Գերազանց", "Կրիտիկական"):
            self.assertIn(fragment, text)

    def test_check_and_score_are_read_only(self):
        for skill in ("hy-check", "hy-score"):
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Never modify", text)
            self.assertIn("protected", text.lower())

    def test_codex_manifest_is_public_ready(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("hy-text", manifest["name"])
        self.assertEqual("Arman Khachatryan", manifest["author"]["name"])
        self.assertEqual("https://github.com/arm092/hy-text", manifest["repository"])
        self.assertEqual("MIT", manifest["license"])
        self.assertEqual("./assets/icon.png", manifest["interface"]["composerIcon"])
        self.assertEqual("./assets/logo.png", manifest["interface"]["logo"])
        self.assertEqual("./assets/logo-dark.png", manifest["interface"]["logoDark"])

    def test_visual_assets_exist(self):
        for name in ("icon.png", "logo.png", "logo-dark.png"):
            self.assertTrue((ROOT / "assets" / name).is_file(), name)

    def test_platform_manifests_exist(self):
        for path in (
            ".claude-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
            "gemini-extension.json",
            "openclaw.plugin.json",
        ):
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
