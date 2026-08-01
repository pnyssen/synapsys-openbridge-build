"""
Regression tests for Correction v0.1
(LANE_B_CLAUDE_CODE_N8N_VIEWER_AND_CANVAS_COMPILER_CORRECTION_RETURN_v0.1.md):

  1. snapshot time not later than build/receipt time (no future-dating)
  2. HTML and Canvas return links are valid hrefs/paths and contain no literal
     arrow ("->") notation
  3. every filed review-subset file matches CANDIDATE_MANIFEST_SHA256.csv
     exactly (byte count + SHA-256)

Run after tools_build_live_fixtures.py / tools_build_labelled_fixtures.py /
tools_build_viewer_snapshot.py / generate_canvases.py / viewer/n8n_viewer.py
have all produced their current output — same precondition as
GeneratedCanvasFileTests in test_compiler.py.
"""
import copy
import csv
import hashlib
import pathlib
import re
import sys
import unittest
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.canvas_compiler import GraphCompileError, compile_canvas, validate_graph  # noqa: E402
from compiler.view_profiles import available_profiles, load_profile_graph  # noqa: E402

GENERATED_DIR = ROOT / "generated"
MANIFEST_PATH = ROOT / "CANDIDATE_MANIFEST_SHA256.csv"
VIEWER_HTML_PATH = GENERATED_DIR / "N8N_VIEWER.html"

# The literal old, future-dated value this correction replaced. Any profile still
# carrying it is a regression, not a legitimate re-snapshot.
_OLD_BAD_SNAPSHOT = "2026-08-02T02:15:00Z"

HREF_RE = re.compile(r'href="([^"]*)"')


def _parse_iso8601_utc(value: str) -> datetime:
    # graph_schema.json snapshots are always explicit 'Z' (UTC) per the adapter
    # contract's freshness convention — fail the test loudly if that ever isn't true,
    # rather than silently guessing a timezone.
    if not value.endswith("Z"):
        raise AssertionError(f"snapshot {value!r} has no explicit UTC 'Z' suffix")
    return datetime.fromisoformat(value[:-1] + "+00:00")


class TimestampTests(unittest.TestCase):
    def test_no_profile_still_carries_the_old_future_dated_snapshot(self):
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                self.assertNotEqual(graph["snapshot"], _OLD_BAD_SNAPSHOT)

    def test_every_profile_snapshot_is_not_later_than_now(self):
        now = datetime.now(timezone.utc)
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                snapshot_dt = _parse_iso8601_utc(graph["snapshot"])
                self.assertLessEqual(
                    snapshot_dt,
                    now,
                    f"{profile_id}: snapshot {graph['snapshot']} is later than build/receipt time {now.isoformat()}",
                )

    def test_every_profile_snapshot_is_not_later_than_hub_intake_plus_reasonable_build_window(self):
        # Hub intake time cited in the correction dispatch: 2026-08-02T01:56:00+10:00
        hub_intake = datetime.fromisoformat("2026-08-02T01:56:00+10:00").astimezone(timezone.utc)
        # Generous window for the correction build itself to complete — this is a
        # sanity ceiling against a *new* fabricated/guessed future timestamp, not a
        # tight bound on real build time.
        max_build_window_seconds = 6 * 3600
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                snapshot_dt = _parse_iso8601_utc(graph["snapshot"])
                delta = (snapshot_dt - hub_intake).total_seconds()
                self.assertLessEqual(
                    delta,
                    max_build_window_seconds,
                    f"{profile_id}: snapshot {graph['snapshot']} is {delta}s after Hub intake "
                    f"({hub_intake.isoformat()}) — exceeds the {max_build_window_seconds}s sanity window",
                )


class LinkValidityTests(unittest.TestCase):
    def test_compiler_fails_closed_on_arrow_notation_in_return_route(self):
        # Enforced twice (defense in depth): the JSON-Schema 'pattern' on
        # return_route rejects it first (jsonschema.validate runs before the
        # explicit "->" check in validate_graph), so either failure mode is an
        # acceptable pass here — what matters is that no canvas is compiled from
        # an arrow-notation return_route, not which layer caught it.
        graph = load_profile_graph("psa")
        bad_graph = copy.deepcopy(graph)
        bad_graph["return_route"] = "Obsidian/00_HOME.md -> NAVIGATOR_MVP_v0.2/SOMETHING.md"
        with self.assertRaises(GraphCompileError) as ctx:
            validate_graph(bad_graph)
        message = str(ctx.exception)
        self.assertTrue(
            "INVALID_RETURN_ROUTE" in message or "return_route" in message,
            f"expected the arrow-notation return_route to be rejected by name, got: {message}",
        )
        with self.assertRaises(GraphCompileError):
            compile_canvas(bad_graph)

    def test_every_profile_return_route_has_no_arrow_notation(self):
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                self.assertNotIn("->", graph["return_route"])
                canvas = compile_canvas(copy.deepcopy(graph))
                self.assertNotIn("->", canvas["metadata"]["return_route"])
                home_node = next(n for n in canvas["nodes"] if n["id"] == "__return_to_navigator_home__")
                self.assertNotIn("->", home_node["text"])

    def test_every_profile_return_route_is_a_single_clean_path(self):
        # No embedded whitespace-arrow-whitespace, and looks like a real path/URL
        # (contains no raw spaces, which would also make an href invalid/ambiguous).
        for profile_id in available_profiles():
            with self.subTest(profile=profile_id):
                graph = load_profile_graph(profile_id)
                self.assertNotIn(" ", graph["return_route"])

    def test_viewer_html_return_links_have_no_arrow_notation_and_are_well_formed(self):
        self.assertTrue(VIEWER_HTML_PATH.exists(), f"missing {VIEWER_HTML_PATH} — run viewer/n8n_viewer.py first")
        html_text = VIEWER_HTML_PATH.read_text(encoding="utf-8")
        hrefs = HREF_RE.findall(html_text)
        self.assertGreaterEqual(len(hrefs), 2, "expected at least the banner and footer return links")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertNotIn("->", href)
                self.assertNotIn(" ", href, "href must not contain a raw unencoded space")
                self.assertTrue(
                    href.startswith("https://") or href.startswith("/") or href.startswith("../"),
                    f"href {href!r} is not a well-formed absolute/relative URL",
                )

    def test_viewer_html_return_href_points_at_the_v1_2_primary_interface(self):
        html_text = VIEWER_HTML_PATH.read_text(encoding="utf-8")
        hrefs = HREF_RE.findall(html_text)
        self.assertTrue(
            any(href.endswith("SYNAPSYS_NAVIGATOR_MVP_ARCHITECTURE_v1.2.html") for href in hrefs),
            f"no return link points at the v1.2 primary interface; found hrefs: {hrefs}",
        )


class ManifestIntegrityTests(unittest.TestCase):
    """Guards CANDIDATE_MANIFEST_SHA256.csv itself — must be regenerated LAST,
    after all corrected files are final, and must match the tree byte-for-byte.
    """

    def test_manifest_exists(self):
        self.assertTrue(MANIFEST_PATH.exists())

    def test_every_manifest_row_matches_the_file_on_disk(self):
        with open(MANIFEST_PATH, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreater(len(rows), 0)
        for row in rows:
            rel_path = row["path"]
            expected_sha256 = row["sha256"]
            expected_bytes = int(row["bytes"])
            full_path = ROOT / rel_path
            with self.subTest(file=rel_path):
                self.assertTrue(full_path.exists(), f"manifest lists {rel_path} but it does not exist on disk")
                content = full_path.read_bytes()
                self.assertEqual(len(content), expected_bytes, f"{rel_path}: byte count drifted from manifest")
                actual_sha256 = hashlib.sha256(content).hexdigest()
                self.assertEqual(actual_sha256, expected_sha256, f"{rel_path}: SHA-256 drifted from manifest")

    def test_manifest_does_not_still_record_the_pre_correction_readme_byte_count(self):
        # The correction dispatch flagged an internal drift: filed README was 8,920
        # bytes while the manifest recorded 8,472 (the stale pre-correction figure).
        # Guard against that specific class of staleness recurring.
        with open(MANIFEST_PATH, newline="", encoding="utf-8") as fh:
            rows = {row["path"]: row for row in csv.DictReader(fh)}
        readme_row = rows.get("README.md")
        self.assertIsNotNone(readme_row, "README.md missing from manifest")
        actual_bytes = len((ROOT / "README.md").read_bytes())
        self.assertEqual(int(readme_row["bytes"]), actual_bytes)


if __name__ == "__main__":
    unittest.main()
