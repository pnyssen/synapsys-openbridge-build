"""Deterministic, offline tests. No network call anywhere in this file."""
from __future__ import annotations

import unittest

from checks.link_checker import check_links
from checks.manifest_parity import ManifestRow, check_parity, parse_manifest_csv
from checks.presentation_standard import check_dead_data_open_targets, check_presentation
from checks.state_vocabulary import compare_hook_to_expected, extract_window_hook, find_state_collapse


class ManifestParityTests(unittest.TestCase):
    def test_parse_path_bytes_sha_header(self):
        csv_text = "path,bytes,sha256\nfoo.md,10,abc\n"
        rows = parse_manifest_csv(csv_text)
        self.assertEqual(rows, [ManifestRow(path="foo.md", bytes=10, sha256="abc")])

    def test_parse_path_sha_bytes_header(self):
        csv_text = "path,sha256,bytes\nfoo.md,abc,10\n"
        rows = parse_manifest_csv(csv_text)
        self.assertEqual(rows, [ManifestRow(path="foo.md", bytes=10, sha256="abc")])

    def test_matching_row_produces_no_finding(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {"foo.md": (10, "abc")}
        self.assertEqual(check_parity(rows, actual), [])

    def test_byte_mismatch_detected(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {"foo.md": (12, "abc")}
        findings = check_parity(rows, actual)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "BYTE_MISMATCH")

    def test_hash_mismatch_detected_when_bytes_match(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {"foo.md": (10, "def")}
        findings = check_parity(rows, actual)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "HASH_MISMATCH")

    def test_missing_on_disk_detected(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {}
        findings = check_parity(rows, actual)
        self.assertEqual(findings[0].kind, "MISSING_ON_DISK")

    def test_extra_not_in_manifest_detected(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {"foo.md": (10, "abc"), "bar.md": (5, "xyz")}
        findings = check_parity(rows, actual)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "EXTRA_NOT_IN_MANIFEST")

    def test_byte_mismatch_does_not_also_report_hash_mismatch(self):
        rows = [ManifestRow("foo.md", 10, "abc")]
        actual = {"foo.md": (12, "def")}
        findings = check_parity(rows, actual)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "BYTE_MISMATCH")


BASE_DIR = "Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT"
HOME_PATH = "Obsidian/00_HOME.md"


class LinkCheckerTests(unittest.TestCase):
    def test_clean_page_with_home_return_has_no_findings(self):
        html = '<a href="../../../00_HOME.md">Home</a><a href="page.md">Page</a>'
        known = {"Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/page.md", HOME_PATH}
        findings = check_links(html, base_dir=BASE_DIR, known_paths=known)
        self.assertEqual(findings, [])

    def test_unresolved_relative_link_detected(self):
        html = '<a href="missing.md">Missing</a><a href="../../../00_HOME.md">Home</a>'
        findings = check_links(html, base_dir=BASE_DIR, known_paths={HOME_PATH})
        kinds = [f.kind for f in findings]
        self.assertIn("UNRESOLVED_RELATIVE", kinds)

    def test_missing_home_return_detected(self):
        html = '<a href="page.md">Page</a>'
        findings = check_links(html, base_dir=BASE_DIR,
                                known_paths={"Obsidian/00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/page.md"})
        kinds = [f.kind for f in findings]
        self.assertIn("NO_HOME_RETURN", kinds)

    def test_arrow_notation_detected(self):
        html = '<div>Obsidian/00_HOME.md -> somewhere</div><a href="../../../00_HOME.md">Home</a>'
        findings = check_links(html, base_dir=BASE_DIR, known_paths={HOME_PATH})
        kinds = [f.kind for f in findings]
        self.assertIn("ARROW_NOTATION", kinds)

    def test_absolute_url_and_anchor_not_flagged_as_unresolved(self):
        html = '<a href="https://example.com/x">Ext</a><a href="#main">Skip</a><a href="../../../00_HOME.md">Home</a>'
        findings = check_links(html, base_dir=BASE_DIR, known_paths={HOME_PATH})
        kinds = [f.kind for f in findings]
        self.assertNotIn("UNRESOLVED_RELATIVE", kinds)

    def test_competing_interface_claim_detected(self):
        html = ("<p>This is the current interface.</p>"
                "<p>Also, this is the current interface.</p>"
                '<a href="../../../00_HOME.md">Home</a>')
        findings = check_links(html, base_dir=BASE_DIR, known_paths={HOME_PATH})
        kinds = [f.kind for f in findings]
        self.assertIn("COMPETING_INTERFACE_CLAIM", kinds)


class PresentationStandardTests(unittest.TestCase):
    def test_white_background_no_dark_mode_passes(self):
        html = "<style>body{background:#fff}</style>"
        self.assertEqual(check_presentation(html), [])

    def test_dark_mode_query_flagged(self):
        html = "<style>body{background:#fff}@media (prefers-color-scheme: dark){body{background:#000}}</style>"
        findings = check_presentation(html)
        kinds = [f.kind for f in findings]
        self.assertIn("DARK_MODE_QUERY_PRESENT", kinds)

    def test_missing_white_background_flagged(self):
        html = "<style>body{background:#123456}</style>"
        findings = check_presentation(html)
        kinds = [f.kind for f in findings]
        self.assertIn("NO_WHITE_BACKGROUND_DECLARED", kinds)

    def test_dead_data_open_target_detected(self):
        html = '<button data-open="wave">Go</button><section id="operate"></section>'
        findings = check_dead_data_open_targets(html)
        self.assertEqual(len(findings), 1)
        self.assertIn("wave", findings[0].detail)

    def test_live_data_open_target_not_flagged(self):
        html = '<button data-open="wave">Go</button><section id="wave"></section>'
        findings = check_dead_data_open_targets(html)
        self.assertEqual(findings, [])


class StateVocabularyTests(unittest.TestCase):
    def test_clean_candidate_language_not_flagged(self):
        html = "<p>This is a candidate view. It is not yet implemented and not current.</p>"
        findings = find_state_collapse(html)
        self.assertEqual(findings, [])

    def test_unqualified_collapse_flagged(self):
        html = "<p>This candidate view is implemented and current.</p>"
        findings = find_state_collapse(html)
        kinds = [f.kind for f in findings]
        self.assertIn("STATE_COLLAPSE_NEAR_CANDIDATE", kinds)

    def test_backward_order_collapse_flagged(self):
        html = "<p>The interface is now canonical, and remains a candidate.</p>"
        findings = find_state_collapse(html)
        kinds = [f.kind for f in findings]
        self.assertIn("STATE_COLLAPSE_NEAR_CANDIDATE", kinds)

    # Regression fixtures: these exact phrasings were found in the real,
    # live Architecture v1.2 HTML and produced false positives under the
    # first (proximity-only) version of this check — both words present,
    # no claim of equivalence. This version must not flag any of them.
    def test_unrelated_canonical_candidates_phrase_not_flagged(self):
        html = ("<li><b>The knowledge stack is candidate-heavy.</b> Canonical candidates and "
                "Pattern candidates materially exceed promoted/admitted objects.</li>")
        self.assertEqual(find_state_collapse(html), [])

    def test_canonical_count_sentence_not_flagged(self):
        html = "<dd>56 records: 5 promoted, 40 candidate, 4 evidence-conflicted.</dd>"
        self.assertEqual(find_state_collapse(html), [])

    def test_current_objective_sentence_not_flagged(self):
        html = ('<p class="objective"><b>Current objective:</b> verify the Stream A '
                "candidate fileset, then prove one bounded relay.</p>")
        self.assertEqual(find_state_collapse(html), [])

    def test_script_block_content_not_flagged(self):
        html = ("<script>window.x={canonical:{total:56,candidate:40}};</script>"
                '<a href="../../../00_HOME.md">Home</a>')
        self.assertEqual(find_state_collapse(html), [])

    def test_extract_window_hook_parses_simple_object(self):
        html = "window.navigatorStatus={integrity:{green:1,partial:6,held:1,full:false},ppv:'Potential'};"
        hook = extract_window_hook(html, "navigatorStatus")
        self.assertIsNotNone(hook)
        self.assertEqual(hook["integrity"]["green"], 1)
        self.assertEqual(hook["ppv"], "Potential")

    def test_extract_window_hook_skips_arrow_function_valued_keys(self):
        html = ("window.navigatorStatus={currentPanel:()=>document.querySelector('.panel.active')?.id,"
                "integrity:{green:1,partial:6},ppv:'Potential'};")
        hook = extract_window_hook(html, "navigatorStatus")
        self.assertIsNotNone(hook)
        self.assertNotIn("currentPanel", hook)
        self.assertEqual(hook["integrity"]["green"], 1)
        self.assertEqual(hook["ppv"], "Potential")

    def test_extract_window_hook_returns_none_for_missing_name(self):
        html = "window.somethingElse={a:1};"
        self.assertIsNone(extract_window_hook(html, "navigatorStatus"))

    def test_compare_hook_matching_reports_nothing(self):
        hook = {"integrity": {"green": 1, "partial": 6}}
        expected = {"integrity.green": 1, "integrity.partial": 6}
        self.assertEqual(compare_hook_to_expected(hook, expected), [])

    def test_compare_hook_mismatch_reported(self):
        hook = {"integrity": {"green": 2, "partial": 6}}
        expected = {"integrity.green": 1, "integrity.partial": 6}
        findings = compare_hook_to_expected(hook, expected)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "TEST_HOOK_FIELD_MISMATCH")

    def test_compare_hook_missing_field_reported(self):
        hook = {"integrity": {"green": 1}}
        expected = {"integrity.held": 1}
        findings = compare_hook_to_expected(hook, expected)
        self.assertEqual(findings[0].kind, "TEST_HOOK_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
