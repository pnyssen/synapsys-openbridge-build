"""RC06i real-browser layout tests (Playwright / Chromium) over the REAL route output in a MOCK Odoo-shaped shell (verify/rc06i_service_1_3_1).
The shell follows the DOM probe on dev (viewport-height flex column: navbar 46 px, flexible .o_action_manager, .o-main-components-container with the panel).
It is structural evidence, not Odoo: it cannot prove correct placement or btn-sm sizing in the signed-in app. Skipped (never passed) without node, chromium, or the git objects of the older commits."""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY = os.path.abspath(os.path.join(HERE, "..", "verify", "rc06i_service_1_3_1"))
sys.path.insert(0, VERIFY)


def _have(c):
    return subprocess.run(["git", "cat-file", "-e", c + "^{commit}"], cwd=HERE, capture_output=True).returncode == 0


class Matrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("node") or not shutil.which("git") or not (_have("88eb331") and _have("e5322c9")):
            raise unittest.SkipTest("node, git or the RC06g/RC06h commits are not available: browser matrix NOT run")
        import run_matrix
        cls.tmp = tempfile.mkdtemp(prefix="rc06i_matrix_")
        cls.res = run_matrix.run(cls.tmp, True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, "tmp", ""), ignore_errors=True)

    def failing(self, ver, check, *, rendered_only=True, width=None):
        v = self.res[ver]
        out = []
        for c in v["cases"]:
            if rendered_only and "|".join(c["case"].rsplit("_", 1)) in v["not_rendered"]:
                continue
            if width and c["w"] != width:
                continue
            if c["checks"].get(check) is False:
                out.append((c["case"], c["w"]))
        return out

    # ---- RC06i must pass everything, on all cases (Service 297, Measures 189, one RULED noun; 390 and 1024; three depths)
    def test_rc06i_passes_every_check_on_every_case(self):
        v = self.res["rc06i"]
        self.assertEqual(len(v["cases"]), 18); self.assertEqual(v["not_rendered"], [])
        bad = [(c["case"], c["w"], k) for c in v["cases"] for k, ok in c["checks"].items() if ok is False]
        self.assertEqual(bad, [])

    def test_rc06i_values_behind_the_checks(self):
        rows = {(x["file"], x["w"]): x["m"] for x in self.res["rc06i"]["raw"]}
        for (f, w), m in rows.items():
            self.assertLessEqual(m["docScrollW"], m["vw"], (f, w))          # no horizontal scroll
            self.assertEqual(m["truncated"], [], (f, w))                   # no ellipsis, no clipped leaf
            self.assertEqual(m["scrollContainers"], 0, (f, w))             # no scroll container inside the panel
            self.assertEqual(m["controlCount"], 1, (f, w))                 # exactly one depth control
            self.assertEqual(m["smallTargets"], [], (f, w))                # every interactive target >= 44 px
            self.assertTrue(m["keyboard"]["reached"], (f, w))              # Tab reaches the control
            self.assertNotEqual(m["keyboard"]["outline"]["style"], "none", (f, w))  # and focus is visible
            self.assertLessEqual(m["gapRecordsToNative"], 8, (f, w))       # no blank band between the Records heading and the native view
            self.assertGreaterEqual(m["nativeHeight"], 0.7 * (m["vh"] - 46), (f, w))  # the list is not squeezed (dev's viewport-height column)
            self.assertLessEqual(m["unreachablePx"], 1, (f, w))            # everything reachable by scrolling the page
            if f.endswith("enrich") and m["sourceRows"]:
                self.assertEqual(m["sourceVisible"], m["sourceRows"], (f, w))  # Source visible, also at 390
        s = [x for x in self.res["rc06i"]["raw"] if x["file"].startswith("service")]
        for x in s:
            m = x["m"]
            self.assertEqual(m["apertures"], ["form", "flow", "evolve"]); self.assertTrue(m["valueBand"])
            self.assertEqual(set(k.replace("px", "") for k in m["fonts"]), {"14", "12", "10"})
            t = m["tops"]
            self.assertTrue(t["answer"] < t["apertures"] < t["value"] < t["records"] < t["native"])  # Answer, apertures, Value band, Records heading, native view
        for x in s:
            if x["file"] == "service_enable" and x["w"] == 390:
                self.assertLessEqual(x["m"]["recordsBottom"], 844)          # default head fits one 844 px viewport at 390

    def test_pressed_state_follows_the_served_depth(self):
        for x in self.res["rc06i"]["raw"]:
            self.assertEqual(x["m"]["pressed"], [x["file"].rsplit("_", 1)[1]], x["file"])

    # ---- original-failure regression: these MUST fail on RC06g and RC06h (the same tests, their real output)
    def test_rc06h_fails_first_column_clipping_hidden_source_nested_scroll_no_ffe_no_value_and_a_squeezed_list(self):
        self.assertTrue(self.failing("rc06h", "no_truncated_cell"))                 # first-column clipping (Measures / Service Enrich)
        self.assertTrue(self.failing("rc06h", "source_visible", width=390))         # Source hidden at 390
        self.assertTrue(self.failing("rc06h", "no_nested_scroll"))                  # the 60vh inner scroll
        self.assertEqual(len(self.failing("rc06h", "apertures_ffe")), 6)            # no Form / Flow / Evolve
        self.assertEqual(len(self.failing("rc06h", "value_band")), 6)               # no Value band
        self.assertEqual(len(self.failing("rc06h", "font_14_12_10")), 6)
        self.assertTrue(self.failing("rc06h", "one_accessible_control"))            # control present but not accessible / not in the answer band
        self.assertTrue(self.failing("rc06h", "targets_44"))                        # 21 px buttons
        self.assertTrue(self.failing("rc06h", "list_not_squeezed"))                 # dev's viewport-height column squeezes the list under a tall panel

    def test_rc06g_fails_placement_has_no_control_no_apertures_no_value_band_and_serves_only_enable(self):
        self.assertEqual(len(self.failing("rc06g", "dom_order")), 6)                # panel below the native view (rendered cases)
        self.assertTrue(self.failing("rc06g", "one_accessible_control"))            # the control is missing
        self.assertTrue(self.failing("rc06g", "value_band", rendered_only=False))
        self.assertEqual(self.res["rc06g"]["not_rendered"], ["measures|enhance", "measures|enrich", "noun_ruled|enhance", "noun_ruled|enrich", "service|enhance", "service|enrich"])  # no route for Enhance / Enrich

    def test_the_same_checks_pass_on_rc06i_and_the_failing_set_is_not_empty_for_the_older_versions(self):
        for ver in ("rc06g", "rc06h"):
            self.assertTrue(any(v is False for c in self.res[ver]["cases"] for v in c["checks"].values()), ver)
        self.assertFalse(any(v is False for c in self.res["rc06i"]["cases"] for v in c["checks"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
