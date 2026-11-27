"""Mutation controls: inject one fault at a time into a COPY of the source, run every suite, a mutant must be KILLED (some suite fails).
Run:  python3 -I run_mutants.py   (from this directory). Exit 1 if any mutant survives or any pattern no longer applies."""
import os, shutil, subprocess, sys, tempfile
SRC = os.path.dirname(os.path.abspath(__file__))
F = {"router": "kda_router.py", "loader": "service_ctxss_link_loader.py", "crosswalk": "gvgov004_crosswalk.py"}
SUITES = ("test_kda_route.py", "test_p0_bindings.py", "test_p0_adversarial.py", "test_p0_loader_recovery.py", "test_p0_loader_regressions.py")
M = [
 # --- router (the original 27, patterns kept where the text is unchanged) ---
 ("router", 'if not trusted(verifier):\n        return "NO_TRUSTED_VERIFIER", None', 'if False:\n        return "NO_TRUSTED_VERIFIER", None'),
 ("router", 'if got.get("issuer") != "D007" or got.get("status") != "RELEASED":', 'if False:'),
 ("router", 'or body.get("scope_digest") != mine:', 'or False:'),
 ("router", 'if body.get("fields") != effect.get("fields") or body.get("target_ids") != effect.get("target_ids"):', 'if False:'),
 ("router", 'if state[0] == "RESERVED" and (run_id is None or state[1] != run_id):', 'if False:'),
 ("router", 'state[0] not in ("AVAILABLE", "RESERVED")', 'False'),
 ("router", 'if effect.get("pins") != verifier.current_pins():', 'if False:'),
 ("router", 'not (nb <= now <= ex)', 'False'),
 ("router", 'ap.get("can_write") is True and bool(ap.get("actor")) and ap.get("actor") == body.get("actor_id")', 'True'),
 ("router", 'ex.get("backup_restore_verified") is True and ', 'True and '),
 ("router", '(not route.get("needs_chg") or bool(body.get("chg")))', 'True'),
 ("router", 'elif isinstance(ch, dict) and ch.get("provider") == bp:', 'elif False:'),
 ("router", 'ch.get("verdict") == "PASS" and ', 'True and '),
 ("router", 'gates = GATES', 'gates = ("seat_release",)'),
 ("router", 'if any(e.get(k) for k in SENSITIVE_READ):\n            return "F2"', 'if False:\n            return "F2"'),
 ("router", 'raise ClassificationHold("CONTRADICTORY_READ_ONLY_WITH_MUTATION")', 'pass'),
 ("router", 'raise ClassificationHold("MUTATES_NOT_EXPLICIT_BOOL")', 'pass'),
 ("router", 'not _allowed(connector, effect["model"]):\n        st["actor_permission"] = "MODEL_NOT_IN', 'False:\n        st["actor_permission"] = "MODEL_NOT_IN'),
 ("router", 'return isinstance(verifier, Verifier) and verifier.identity() in PINNED_VERIFIER_IDS', 'return isinstance(verifier, Verifier)'),
 # --- loader (original 6 re-expressed for v3, plus the recovery / journal / boundary / all-or-nothing controls) ---
 ("loader", 'if not isinstance(admission, Admission):\n        raise Hold("APPLY_REQUIRES_ADMISSION")', 'pass'),
 ("loader", 'adm.journal.append("ROW", id=r["id"], prior=r["prior"] or False, new=ctx.id)   # write-ahead', 'pass'),
 ("loader", 'if phase == "pre_write" and prestate_digest(env) != adm.prestate:', 'if False:'),
 ("loader", 'if getattr(adm.lock, "held", False) is not True:\n        raise Hold("RUN_LOCK_NOT_HELD_AT_WRITE_BOUNDARY")', 'pass'),
 ("loader", 'adm.verifier.finalize_consume(adm.rid, adm.run_id)', 'pass'),
 ("loader", 'if d["disposition"] != "APPLY_ADMITTED":\n        raise Hold("NOT_ADMITTED:', 'if False:\n        raise Hold("NOT_ADMITTED:'),
 ("loader", 'if r.exists() and _ref(r, "context_id") == ctx_id:', 'if r.exists():'),
 ("loader", 'if conflicts:\n                raise Hold("SCOPE_CONFLICT_ALL_OR_NOTHING', 'if False:\n                raise Hold("SCOPE_CONFLICT_ALL_OR_NOTHING'),
 ("loader", 'if d["disposition"] != "APPLY_ADMITTED":\n        raise Hold("REVALIDATION_FAILED:', 'if False:\n        raise Hold("REVALIDATION_FAILED:'),
 ("loader", 'if v.receipt_state(adm.rid) != ("RESERVED", adm.run_id):', 'if False:'),
 ("loader", '_revalidate(env, adm, "pre_commit")', 'pass'),
 ("loader", '_typed_readback(env, ctx.id, total_before, others_before)', 'pass'),
 ("loader", 'if not isinstance(adm.journal, DurableJournal) or not adm.journal.ready() or adm.journal.run_id != adm.run_id:', 'if False:'),
 ("loader", 'if not isinstance(journal, DurableJournal) or not journal.ready() or journal.entries():', 'if not isinstance(journal, DurableJournal):'),
 ("loader", 'os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW', 'os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW'),
 ("loader", 'or (st.st_mode & 0o077) or st.st_uid != os.getuid():', 'or st.st_uid != os.getuid():'),
 ("loader", '(self.run_id and r.get("run_id") != self.run_id):', 'False):'),
 ("loader", 'if r.get("prev") != prev or r.get("seq") != i + 1 or hashlib', 'if False or hashlib'),
 ("loader", 'if verifier.reserve(rid, journal.run_id) is not True:', 'if False:'),
 ("loader", 'adm.verifier.release_reservation(adm.rid, adm.run_id)\n    except Exception as e:\n        errs.append("release_reservation', 'pass\n    except Exception as e:\n        errs.append("release_reservation'),
 ("loader", 'finally:\n        try:\n            adm.lock.release()', 'finally:\n        try:\n            pass'),
 ("loader", 'if cls == "NOT_COMMITTED":\n                errs = _abort(env, adm, "COMMIT_FAILED', 'if False:\n                errs = _abort(env, adm, "COMMIT_FAILED'),
 ("loader", 'if cls != "COMMITTED":\n                try:\n                    adm.journal.append("COMMIT_UNKNOWN"', 'if False:\n                try:\n                    adm.journal.append("COMMIT_UNKNOWN"'),
 ("loader", 'raise ReconcilePending("COMMITTED_UNCONSUMED", adm.run_id, "receipt reservation kept; run reconcile()")', 'return'),
 ("loader", 'env.cr.rollback()          # classify COMMITTED data only', 'pass          # classify COMMITTED data only'),
 ("loader", 'if cls == "MIXED":\n            journal.append("ESCALATED_MIXED")\n            raise Hold("MIXED_STATE_ESCALATE_TO_D007")', 'if False:\n            raise Hold("MIXED_STATE_ESCALATE_TO_D007")'),
 ("loader", 'if cur == e["new"]:\n            n_new += 1', 'if cur == e["new"] and False:\n            n_new += 1'),
 ("loader", 'if cr is None or not callable(getattr(cr, "commit", None)) or not callable(getattr(cr, "rollback", None)):', 'if False:'),
 ("crosswalk", 'out["method"] = {"state": "UNOBSERVED_HOLD"', 'out["method"] = {"state": "RESOLVED"'),
 ("crosswalk", 'len(str(context_ruling.get("ruling_sha256", ""))) == 64', 'True'),
]
# Equivalent mutants, kept as documented defence-in-depth: a second guard on the same path already refuses (these are EXPECTED to survive).
EQUIV = [("loader", 'if not K.trusted(v):\n        raise Hold("NO_TRUSTED_VERIFIER_AT_WRITE_BOUNDARY")', 'pass', "K.decide() inside _revalidate refuses an unpinned verifier"),
         ("loader", 'if j["run_id"] != journal.run_id:\n            continue', 'pass', "journal.entries() already rejects any record from another run")]
bad, na = [], []
for i, (f, a, b) in enumerate(M):
    d = tempfile.mkdtemp()
    for x in os.listdir(SRC):
        if x.endswith(".py"): shutil.copy(os.path.join(SRC, x), d)
    p = os.path.join(d, F[f]); s = open(p).read()
    if a not in s:
        print("M%02d NOT-APPLICABLE %s" % (i, a[:60].replace("\n", " "))); na.append(i); continue
    open(p, "w").write(s.replace(a, b, 1))
    killed = any(subprocess.run([sys.executable, "-I", t], cwd=d, capture_output=True, text=True).returncode != 0 for t in SUITES)
    print("M%02d %s %s" % (i, "KILLED  " if killed else "SURVIVED", a[:60].replace("\n", " ")))
    if not killed: bad.append(i)
for f, a, b, why in EQUIV:
    d = tempfile.mkdtemp()
    for x in os.listdir(SRC):
        if x.endswith(".py"): shutil.copy(os.path.join(SRC, x), d)
    p = os.path.join(d, F[f]); s = open(p).read(); assert a in s; open(p, "w").write(s.replace(a, b, 1))
    k = any(subprocess.run([sys.executable, "-I", t], cwd=d, capture_output=True, text=True).returncode != 0 for t in SUITES)
    print("EQUIV %s (%s): %s" % ("killed" if k else "survives as expected", why, a[:40].replace("\n", " ")))
print("mutants=%d survivors=%s not_applicable=%s" % (len(M), bad, na)); sys.exit(1 if bad or na else 0)
