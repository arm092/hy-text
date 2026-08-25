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
RELEASE_VERSION = "1.0.0"
RELEASE_MANIFESTS = (
    (".claude-plugin/plugin.json", ("version",)),
    (".claude-plugin/marketplace.json", ("metadata", "version")),
    (".claude-plugin/marketplace.json", ("plugins", 0, "version")),
    (".codex-plugin/plugin.json", ("version",)),
    (".cursor-plugin/plugin.json", ("version",)),
    ("gemini-extension.json", ("version",)),
    ("openclaw.plugin.json", ("version",)),
)
RELEASE_EVIDENCE = (
    "tests/golden/scoring.json",
    "tests/golden/check.json",
    "tests/calibration/v1.0.0/check-results.json",
    "tests/calibration/v1.0.0/install-smoke.json",
    "maximum total deviation <= 0.7",
    "maximum dimension deviation <= 1.0",
    "recall >= 0.90",
    "false-positive rate <= 0.05",
    "protected-span mutations = 0",
    "six hermetic packaging checks",
)


def nested_value(data, path):
    for part in path:
        data = data[part]
    return data


class RepositoryContractTest(unittest.TestCase):
    def test_release_manifests_have_the_stable_version(self):
        for relative_path, version_path in RELEASE_MANIFESTS:
            with self.subTest(path=relative_path, version_path=version_path):
                manifest = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                self.assertEqual(RELEASE_VERSION, nested_value(manifest, version_path))

    def test_stable_release_documentation_targets_v1(self):
        for relative_path in ("README.md", "README.en.md"):
            with self.subTest(path=relative_path):
                text = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("v1.0.0", text)
                self.assertNotIn("active development", text.lower())
                self.assertNotIn("մշակման փուլում", text)

        for relative_path in ("INSTALL.md", "INSTALL.en.md"):
            with self.subTest(path=relative_path):
                text = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("v1.0.0", text)
                self.assertIn("--temp-root", text)

    def test_changelog_has_the_dated_stable_release_heading(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 1.0.0 – 2026-08-15", changelog)

    def test_release_note_links_all_evidence_and_thresholds(self):
        release_note = (ROOT / "docs" / "releases" / "v1.0.0.md").read_text(encoding="utf-8")
        for evidence in RELEASE_EVIDENCE:
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, release_note)

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

    def test_score_rubric_has_deterministic_dimension_boundaries(self):
        scoring = (ROOT / "skills" / "hy-text" / "references" / "scoring.md").read_text(encoding="utf-8")
        for fragment in ("50 բառից կարճ", "9.0", "10.0"):
            self.assertIn(fragment, scoring)
        for dimension_source in (
            "Տպագրություն", "typography.md",
            "Լեզվի մաքրություն", "info-style.md",
            "Գրագիտություն", "editorial-punctuation.md",
            "Կառուցվածք", "addenda.md",
            "Ընթերցողի համար ճշգրտություն", "ux-writing.md",
        ):
            self.assertIn(dimension_source, scoring)
        for required_deduction_part in ("HY-*", "հատված", "ազդեցություն"):
            self.assertIn(required_deduction_part, scoring)
        self.assertIn("Մեկ խնդիրը ինքնաբերաբար չի նվազեցնում բոլոր չափումները", scoring)
        self.assertIn("Պաշտպանված ամբողջական հատվածները անփոփոխ են և բացառվում են նվազեցումներից", scoring)

    def test_score_rubric_maps_rules_to_independent_observable_effects(self):
        scoring = (ROOT / "skills" / "hy-text" / "references" / "scoring.md").read_text(encoding="utf-8")
        for fragment in (
            "Կանոնից չափում անցման մատրից",
            "`HY-INF-002`, `HY-ANT-002`, `HY-ADD-004`",
            "ստուգելի հիմքի առկայությունը",
            "Փաստական ճշմարտությունը չի ստուգվում",
            "`HY-UX-002`, `HY-UX-004`, `HY-UX-005`, `HY-UX-006`",
            "Լեզվի մաքրությունը չնվազեցնել միայն հաղորդագրության ընդհանրական լինելու պատճառով",
            "Չափմանը հատուկ թվային խարիսխներ",
            "Միավորները չգումարել կամ հաջորդաբար չհանել",
        ):
            self.assertIn(fragment, scoring)

        score_skill = (ROOT / "skills" / "hy-score" / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "rule-to-dimension matrix",
            "dimension-specific numeric anchors",
            "verifiable support",
            "Do not test whether the claim is true",
            "Do not add deductions or subtract points sequentially",
        ):
            self.assertIn(fragment, score_skill)

        prose = re.sub(r"```.*?```", "", scoring, flags=re.DOTALL)
        prose = re.sub(r"`[^`\r\n]*`", "", prose)
        prose = re.sub(r"https?://[^\s)>]+", "", prose)
        ascii_sentence_stops = re.findall(
            r"[\u0531-\u0556\u0561-\u0587]\.(?=\s|$)",
            prose,
        )
        self.assertEqual([], ascii_sentence_stops)

    def test_score_rubric_has_stable_rule_impact_anchors(self):
        reference_dir = ROOT / "skills" / "hy-text" / "references"
        scoring = (reference_dir / "scoring.md").read_text(encoding="utf-8")
        for fragment in (
            "Կայուն կանոնների ազդեցության աղյուսակ",
            "`HY-TYP-001` – ճիշտ մեկ",
            "`HY-TYP-002` – մեկ տեղային",
            "`HY-PUN-001` – ճիշտ մեկ",
            "`HY-PUN-004` – մեկ տեղային",
            "առնվազն երկու սխալները զբաղեցնում են բոլոր կամ գրեթե բոլոր կիրառելի նախադասությունների սահմանները",
            "առնվազն երկու սխալները զբաղեցնում են բոլոր կամ գրեթե բոլոր կիրառելի հնչերանգային նշանները",
            "`HY-BIZ-001`, `HY-BIZ-002`",
            "`HY-BIZ-004`",
            "`HY-UX-002`",
            "`HY-UX-003`",
            "`HY-UX-004`",
            "`HY-UX-005`",
            "`HY-UX-006`",
            "մեկ կիրառելի UX կանոնի պահանջած հաղորդագրային միավորը",
            "ամենացածր կիրառելի խարիսխը",
            "ամենահատուկ կիրառելի տողը",
            "ավելի հատուկ `HY-UX-*` տող չկա",
            "`HY-ADD-004` և `HY-ANT-002`",
            "`HY-ADD-001` – ծառայողական բացումը",
            "Պաշտպանված հատվածի ներսում հայտնաբերված երևույթը աղյուսակին չհամապատասխանեցնել",
        ):
            self.assertIn(fragment, scoring)

        corpus_ids = set()
        for name in REFERENCES[:-2]:
            corpus_ids.update(RULE_RE.findall((reference_dir / name).read_text(encoding="utf-8")))
        referenced_ids = set(re.findall(r"\bHY-[A-Z]{2,4}-\d{3}\b", scoring))
        self.assertLessEqual(referenced_ids, corpus_ids)

        impact_table = scoring.split("## Կայուն կանոնների ազդեցության աղյուսակ", 1)[1]
        numeric_anchors = [
            float(value)
            for value in re.findall(r"(?<![A-Z0-9-])`(\d+(?:\.\d+)?)`", impact_table)
        ]
        self.assertGreater(len(numeric_anchors), 20)
        self.assertTrue(all(0.0 <= value <= 10.0 for value in numeric_anchors))

        self.assertIn("| `HY-TYP-001` – ճիշտ մեկ", impact_table)
        self.assertIn("| `HY-PUN-001` – ճիշտ մեկ", impact_table)
        self.assertIn("կամ առնվազն երկու լատինական վերջակետ, որոնք չեն զբաղեցնում", impact_table)
        self.assertIn("կամ առնվազն երկու ASCII հարցական նշան, որոնք չեն զբաղեցնում", impact_table)
        self.assertIn("չի գործածում գերադրական, համընդհանուր կամ հեղափոխական պնդում", impact_table)
        self.assertIn("`HY-TYP-002` – առնվազն երկու կրկնվող, բայց ոչ խիտ", impact_table)
        self.assertIn("`HY-PUN-004` – առնվազն երկու կրկնվող, բայց ոչ խիտ", impact_table)
        self.assertNotRegex(impact_table, r"(?m)^\| Նույն (?:տպագրական|կետադրական) խմբի սխալները")

        for line in impact_table.splitlines():
            if not line.startswith("|") or "HY-" not in line:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != 6:
                continue
            ids = set(re.findall(r"HY-[A-Z]{2,4}-\d{3}", cells[0]))
            if ids and all(rule.startswith("HY-TYP-") for rule in ids):
                self.assertEqual(["–", "–", "–", "–"], cells[2:])
            if ids and all(rule.startswith("HY-PUN-") for rule in ids):
                self.assertEqual("–", cells[1])
                self.assertEqual("–", cells[2])
                self.assertEqual("–", cells[4])
            if ids and all(not rule.startswith(("HY-TYP-", "HY-PUN-", "HY-GRM-")) for rule in ids):
                self.assertEqual("–", cells[1])
                self.assertEqual("–", cells[3])

        golden = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        for case in golden:
            self.assertNotIn(case["id"], scoring)
            self.assertNotIn(case["text"], scoring)

    def test_score_rubric_prioritizes_combined_promotional_and_confirmation_states(self):
        scoring = (ROOT / "skills" / "hy-text" / "references" / "scoring.md").read_text(encoding="utf-8")
        impact_table = scoring.split("## Կայուն կանոնների ազդեցության աղյուսակ", 1)[1]

        def anchors_for(rule_state):
            for line in impact_table.splitlines():
                if rule_state not in line:
                    continue
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) == 6:
                    return cells[1:]
            self.fail(f"Missing impact-table state: {rule_state}")

        anonymous_universal = anchors_for("`HY-ADD-004` և `HY-ANT-002`")
        anonymous_only = anchors_for("`HY-ADD-004` –")
        false_contrast = anchors_for("`HY-ADD-003` –")
        unsupported_revolutionary = anchors_for(
            "`HY-INF-002`, `HY-ANT-002` – կարճ համոզող"
        )
        qualitative_only = anchors_for("`HY-INF-002` – կարճ համոզող")
        dangerous_confirmation = anchors_for("`HY-UX-005` –")
        dangerous_confirmation_with_language = anchors_for("`HY-UX-005` և `HY-INF-002`")

        self.assertEqual(["–", "`4.0`", "–", "`6.0`", "`2.0`"], anonymous_universal)
        self.assertEqual(["–", "`6.0`", "–", "`7.0`", "`4.0`"], anonymous_only)
        self.assertEqual(["–", "`5.0`", "–", "`6.0`", "`4.0`"], false_contrast)
        self.assertEqual(["–", "`3.0`", "–", "`5.0`", "`2.0`"], unsupported_revolutionary)
        self.assertEqual(["–", "`4.0`", "–", "`6.0`", "`3.0`"], qualitative_only)
        self.assertEqual(["–", "–", "–", "`6.0`", "`3.0`"], dangerous_confirmation)
        self.assertEqual(["–", "`7.0`", "–", "`6.0`", "`3.0`"], dangerous_confirmation_with_language)

        self.assertIn("նորարարության, հեղափոխական փոփոխության կամ համընդհանուր", impact_table)
        self.assertRegex(impact_table, r"`HY-ADD-003`.{0,80}չի կրկնվում")
        self.assertIn("ինքնուրույն բավարարում է `HY-INF-002`", impact_table)
        self.assertIn("Ճիշտ հայերեն կետադրությամբ", impact_table)

        score_skill = (ROOT / "skills" / "hy-score" / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "combined `HY-ADD-004` + `HY-ANT-002`",
            "innovation, revolution, or universal-coverage framing",
            "false contrast under `HY-ADD-003`",
            "certainty-only dangerous-action confirmation",
        ):
            self.assertIn(fragment, score_skill)

    def test_score_rubric_classifies_generalized_ux_and_business_states(self):
        scoring = (ROOT / "skills" / "hy-text" / "references" / "scoring.md").read_text(encoding="utf-8")
        heading = "## Ընդհանրացված UX և գործարար ձևակերպումների դասակարգում"
        self.assertIn(heading, scoring)
        state_table = scoring.split(heading, 1)[1].split(
            "## Կայուն կանոնների ազդեցության աղյուսակ", 1
        )[0]

        def state_row_for(marker):
            for line in state_table.splitlines():
                if marker not in line:
                    continue
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) == 4:
                    return cells
            self.fail(f"Missing generalized scoring state: {marker}")

        impact_table = scoring.split("## Կայուն կանոնների ազդեցության աղյուսակ", 1)[1]
        expected = {
            "դեյքտիկ հղումը": (
                "`HY-BIZ-005` և `HY-INF-002`",
                "կցված նյութը փոխարինված է միայն անորոշ գնահատականով կամ շտապության բառով",
            ),
            "ընդհանուր սխալի դասը": (
                "`HY-UX-002` և `HY-INF-002`",
                "սխալը փոխարինված է միայն ընդհանրական գնահատականով",
            ),
            "ընդհանուր բացակայության դասը": (
                "`HY-UX-004` և `HY-INF-002`",
                "բացակայությունը ձևակերպված է միայն ընդհանրական վիճակով",
            ),
            "դեյքտիկ մուտքագրման հրաման": (
                "`HY-UX-003` և `HY-INF-002`",
                "հուշումը նաև ընդհանրական է և չի անվանում ակնկալվող արժեքը",
            ),
            "միայն որոշակիություն հարցնող հաստատումը": (
                "`HY-UX-005` և `HY-INF-002`",
                "հաստատման հարցը նաև փոխարինված է ընդհանրական գնահատականով",
            ),
        }

        for marker, (rule_state, impact_condition) in expected.items():
            with self.subTest(marker=marker):
                cells = state_row_for(marker)
                self.assertIn(rule_state, cells[2])
                self.assertIn(impact_condition, cells[3])
                matching_rows = [
                    line
                    for line in impact_table.splitlines()
                    if rule_state in line and impact_condition in line
                ]
                self.assertEqual(1, len(matching_rows))

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

    def test_typography_008_uses_compact_measurement_units(self):
        text = (ROOT / "skills" / "hy-text" / "references" / "typography.md").read_text(encoding="utf-8")
        rule = text.split("## HY-TYP-008", 1)[1]
        self.assertIn("**Ճիշտ։** `5կգ`, `20°C`", rule)
        self.assertIn("`5 kg`, `20 °C`", rule)
        self.assertIn("`30°`", rule)
        self.assertIn("SRC-BIPM-SI-BROCHURE", rule)
        self.assertIn("ընթերցողական ոճային ընտրությունն են", rule)

        skill = (ROOT / "skills" / "hy-text" / "SKILL.md").read_text(encoding="utf-8")
        safe_pass = skill.split("## Safe always-on pass", 1)[1].split("## Load references by task", 1)[0]
        self.assertFalse(
            any(
                line.startswith("|") and line.rstrip().endswith("| HY-TYP-008 |")
                for line in safe_pass.splitlines()
            )
        )
        self.assertIn("contextual", safe_pass.lower())

    def test_typography_sentence_stop_and_internal_separator_have_distinct_ownership(self):
        text = (ROOT / "skills" / "hy-text" / "references" / "typography.md").read_text(
            encoding="utf-8"
        )
        typ_001 = text.split("## HY-TYP-001", 1)[1].split("## HY-TYP-002", 1)[0]
        typ_002 = text.split("## HY-TYP-002", 1)[1].split("## HY-TYP-003", 1)[0]

        self.assertIn("երկու անկախ նախադասությունների սահմանին", typ_001)
        self.assertIn("`Ժողովն ավարտվեց. Մասնակիցները հեռացան։`", typ_001)
        self.assertIn("`Ժողովն ավարտվեց։ Մասնակիցները հեռացան։`", typ_001)
        self.assertIn("HY-TYP-001", typ_001)

        self.assertIn("միայն նույն նախադասության ներքին մասերի միջև", typ_002)
        self.assertIn("HY-TYP-001", typ_002)
        self.assertIn("վերջակետ `։`", typ_002)

    def test_grammar_008_separates_foreign_script_from_armenian_ending(self):
        text = (ROOT / "skills" / "hy-text" / "references" / "editorial-grammar.md").read_text(encoding="utf-8")
        after_heading = text.split("## HY-GRM-008", 1)[1]
        rule = re.split(r"(?=^## HY-)", after_heading, maxsplit=1, flags=re.MULTILINE)[0]

        self.assertIn("Apricode-ում", rule)
        self.assertIn("Apricode-ի թիմը պատասխանեց։", rule)
        self.assertIn("Apricodeում", rule)
        self.assertIn("Մենք ընտրեցինք Apricode։", rule)
        self.assertIn("Apricode ընկերությունում", rule)
        for protected_class in (
            "կոդը",
            "հրամանները",
            "URL-ները",
            "էլեկտրոնային փոստի հասցեները",
            "նույնացուցիչները",
            "ֆայլերի անունները",
            "օտարալեզու մեջբերումները",
            "պաշտպանված պաշտոնական գրությունները",
        ):
            self.assertIn(protected_class, rule)
        self.assertIn("ամբողջությամբ անփոփոխ պահել", rule)
        self.assertIn("**Խստություն։** medium", rule)
        self.assertIn("**Հիմք։** խմբագրական որոշում – SRC-EDITORIAL-POLICY։", rule)
        self.assertIn("Նորմատիվ զուգահեռի աղբյուրն է SRC-LC-FOREIGN-INFLECTION։", rule)
        self.assertIn("պաշտոնական հիմնավորում չէ այս կանոնի՝ առանց չակերտների կիրառության համար", rule)
        self.assertIn("U+002D-ը U+2010 HYPHEN-ի փոխարեն ընտրելը թվային համատեղելիության խմբագրական որոշում է, ոչ թե պաշտոնական նորմ", rule)
        self.assertIn("նիշային քաղաքականության տեխնիկական հիմքն է SRC-UNICODE-ARMENIAN։", rule)

        for example in ("Apricode-ում", "Apricode-ի"):
            separator_index = rule.index(example) + len("Apricode")
            self.assertEqual(0x002D, ord(rule[separator_index]))

        for disallowed_separator in ("\u058a", "\u2010", "\u2014"):
            self.assertNotIn(disallowed_separator, rule)

    def test_business_006_omits_terminal_marks_only_from_non_question_subjects(self):
        path = ROOT / "skills" / "hy-text" / "references" / "business-writing.md"
        after_heading = path.read_text(encoding="utf-8").split("## HY-BIZ-006", 1)[1]
        rule = re.split(r"(?=^## HY-)", after_heading, maxsplit=1, flags=re.MULTILINE)[0]

        self.assertIn(
            "Սովորական թեմա-բառակապակցության կամ թեմա-պնդման վերջում վերջակետադրական նշան չդնել։",
            rule,
        )
        self.assertIn("Էլեկտրոնային նամակի թեմայի տող", rule)
        self.assertIn("`Օգոստոսի հաշվետվություն։`", rule)
        self.assertIn("`Պայմանագիրը հաստատվել է։`", rule)
        self.assertIn("`Օգոստոսի հաշվետվություն`", rule)
        self.assertIn("`Պայմանագիրը հաստատվել է`", rule)
        self.assertIn("Հարցական թեմաները կանոնի կիրառության շրջանակից դուրս են", rule)
        self.assertIn("USAGE-BIZ-003-ը հարցական թեմաների օրինակ չի պարունակում", rule)
        self.assertIn("**Խստություն։** low", rule)
        self.assertIn("**Հիմք։** ժամանակակից գործածություն – USAGE-BIZ-003։", rule)

    def test_all_runtime_skills_preserve_complete_protected_spans(self):
        required_classes = (
            "code",
            "commands",
            "URLs",
            "email addresses",
            "identifiers",
            "filenames",
            "foreign-language segments or quotations",
            "third-party quotations",
            "protected official spellings",
        )
        for skill_name in SKILLS:
            text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill_name):
                self.assertIn("complete protected token or span", text)
                self.assertIn("preserve it verbatim", text)
                for protected_class in required_classes:
                    self.assertIn(protected_class, text)
        score = (ROOT / "skills" / "hy-score" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("exclude the complete span from deductions", score)

    def test_punctuation_005_keeps_approved_prescription_with_honest_basis(self):
        path = ROOT / "skills" / "hy-text" / "references" / "editorial-punctuation.md"
        after_heading = path.read_text(encoding="utf-8").split("## HY-PUN-005", 1)[1]
        rule = re.split(r"(?=^## HY-)", after_heading, maxsplit=1, flags=re.MULTILINE)[0]
        for approved_fragment in (
            "Շեշտի նշանը `՛` դնել շեշտվող բառի համապատասխան ձայնավորի վրա։",
            "Հակադրություն, կրկնադիր շաղկապներ և հատուկ իմաստային շեշտ։",
            "`թե սա, թե նա`",
            "`թե՛ սա, թե՛ նա`",
            "Սովորական բառային շեշտը գրավոր խոսքում պարտադիր չի նշվում։",
            "**Խստություն։** medium",
        ):
            self.assertIn(approved_fragment, rule)
        self.assertIn("**Հիմք։** խմբագրական որոշում – SRC-EDITORIAL-POLICY։", rule)
        self.assertIn("SRC-LC-STRESS", rule)
        self.assertIn("կրկնադիր շաղկապի", rule)
        self.assertIn("ոչ հակադրության կամ հատուկ իմաստային շեշտի բոլոր դեպքերը", rule)

    def test_approved_observed_ux_practices_are_narrow_normative_rules(self):
        path = ROOT / "skills" / "hy-text" / "references" / "ux-writing.md"
        text = path.read_text(encoding="utf-8")

        expected = {
            "HY-UX-007": (
                "Անդառնալի գործողությունն ուղղակիորեն անվանող հսկիչի պիտակը գրել անորոշ դերբայով։",
                "`Ջնջեք հաշիվը`",
                "`Ջնջել հաշիվը`",
                "չի հիմնավորում անվտանգության կամ հասկանալիության առավելություն",
                "**Հիմք։** ժամանակակից գործածություն – USAGE-UX-001։",
            ),
            "HY-UX-008": (
                "Կարճ տեսանելի դաշտանվան վերջում երկու կետ չդնել։",
                "`Անուն:`",
                "`Անուն`",
                "Ամբողջական հարցը կամ նախադասությունը պահպանում է իրեն անհրաժեշտ կետադրությունը",
                "**Հիմք։** ժամանակակից գործածություն – USAGE-UX-002։",
            ),
            "HY-UX-009": (
                "Ընդհանուր հանրային միջերեսում օգտատիրոջն անմիջականորեն դիմելիս լռելյայն ընտրել պաշտոնական դիմելաձևը։",
                "`Մուտքագրիր էլ․ փոստի հասցեն։`",
                "`Մուտքագրեք էլ․ փոստի հասցեն։`",
                "Գիտակցված մտերմական ձայն",
                "**Հիմք։** ժամանակակից գործածություն – USAGE-UX-003։",
            ),
            "HY-UX-010": (
                "Բեռնման հաղորդագրության քերականական ձևն ընտրել ըստ հաղորդագրության դերի",
                "`Բեռնում`՝ որպես միակ ձև բոլոր վիճակներում։",
                "`Ֆայլը բեռնվում է։`",
                "Չկա բոլոր բեռնման վիճակների համար պարտադիր մեկ ձև",
                "**Հիմք։** ժամանակակից գործածություն – USAGE-UX-004։",
            ),
        }

        for rule_id, fragments in expected.items():
            with self.subTest(rule=rule_id):
                after_heading = text.split(f"## {rule_id}", 1)[1]
                rule = re.split(r"(?=^## HY-)", after_heading, maxsplit=1, flags=re.MULTILINE)[0]
                for fragment in fragments:
                    self.assertIn(fragment, rule)

        loading = text.split("## HY-UX-010", 1)[1]
        self.assertIn("`Ֆայլի բեռնում`", loading)
        self.assertIn("`Բեռնված է 3-ը 10-ից։`", loading)
        self.assertIn("Կախման կետերը ներկայացման միջոց են", loading)


if __name__ == "__main__":
    unittest.main()
