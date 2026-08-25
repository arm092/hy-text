import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASH_ALGORITHM = "sha256-utf8-lf-v1"


def canonical_text_sha256(payload: bytes) -> str:
    text = payload.decode("utf-8")
    canonical_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


class ReviewLedgerTest(unittest.TestCase):
    def test_approval_hash_is_stable_across_text_line_endings(self):
        lf = "Հայերեն\nsecond line\n".encode("utf-8")
        crlf = lf.replace(b"\n", b"\r\n")
        bare_cr = lf.replace(b"\n", b"\r")

        expected = hashlib.sha256(lf).hexdigest()
        self.assertEqual(
            {expected},
            {canonical_text_sha256(payload) for payload in (lf, crlf, bare_cr)},
        )
        self.assertEqual(
            3,
            len({hashlib.sha256(payload).hexdigest() for payload in (lf, crlf, bare_cr)}),
        )

    def test_all_ten_references_are_approved_at_immutable_commits(self):
        rows = json.loads((ROOT / "research" / "reviews.json").read_text(encoding="utf-8"))
        by_name = {row["reference"]: row for row in rows}
        expected_reviews = {
            "typography.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-TYP-008",
                "approved_sha256": "d914676c2a5e085b26144bdcefdd6b421191caa1bc1b9af98d4f85b2e2ad5baf",
            },
            "editorial-punctuation.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-PUN-008",
                "approved_sha256": "e74f5f053963908bc45b7184af92b2809a1497c6deb58d976b81e3dc964792cc",
            },
            "editorial-grammar.md": {
                "reviewed_commit": "3771480a6fc7d1106462d8e8aaeacc1e9ad1de64",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-GRM-008",
                "approved_sha256": "da2ffe2b0194dff3c1a9dc8dd37460b3d13ed27d5aa09b80a73b08f63effc3d8",
            },
            "info-style.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-INF-007",
                "approved_sha256": "cd4848b49738e5cd5b549b902b94cc3df5d4919693a16a6ee2288547ba66faaf",
            },
            "ux-writing.md": {
                "reviewed_commit": "324841d3b731f0c10149af0fa4377ae723fbb257",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-UX-010",
                "approved_sha256": "c41e101bb33f9d0d3b4279b986ea96cf622ed8799fc4251a177e2a1f5052e025",
            },
            "business-writing.md": {
                "reviewed_commit": "f20b16cc6acc64db10ded5f630a1e707b3c50787",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-BIZ-007",
                "approved_sha256": "46f1be58da38b05cfe0f5c52a60b1235103ef576181f4299eaca3528ce5ee97a",
            },
            "anti-patterns.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ANT-005",
                "approved_sha256": "16b11fe03666ee5948ba441e94ded012b5a47112df7e3cef380566f85a01760c",
            },
            "addenda.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ADD-006",
                "approved_sha256": "be56ec6e9a97c2daf006dc538173ff5e22ac12ccc337c5885a255fe92cb6e097",
            },
            "scoring.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": None,
                "approved_sha256": "459d3d78dbc63b9485f9682c4a867f0f8eb034397190d37479f2bc3ec96b59d5",
            },
            "sources.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": None,
                "approved_sha256": "5f2d84af70cd61700f9e02a0c05069dacf63ed29d551231e1f4ab1536d048cbe",
            },
        }
        self.assertEqual(set(expected_reviews), set(by_name))
        for row in rows:
            self.assertEqual("Arman Khachatryan", row["reviewer"])
            self.assertEqual("approved", row["status"])
            reference_path = ROOT / "skills" / "hy-text" / "references" / row["reference"]
            current_sha256 = canonical_text_sha256(reference_path.read_bytes())
            self.assertEqual(current_sha256, row.get("approved_sha256"))
            self.assertEqual(HASH_ALGORITHM, row.get("hash_algorithm"))
        self.assertEqual(
            expected_reviews,
            {
                reference: {
                    "reviewed_commit": row["reviewed_commit"],
                    "reviewed_at": row["reviewed_at"],
                    "through_rule": row["through_rule"],
                    "approved_sha256": row["approved_sha256"],
                }
                for reference, row in by_name.items()
            },
        )
