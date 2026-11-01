import argparse, json, pathlib, sys
from . import report, rules


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ss_scaffold")
    p.add_argument("context_json", nargs="+", help="one Context document per file")
    p.add_argument("--out", required=True, help="directory for report files (created if needed)")
    a = p.parse_args(argv)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for path in a.context_json:
        doc = json.load(open(path, encoding="utf-8"))
        ctx = doc.get("context", pathlib.Path(path).stem)
        (out / f"{ctx}--scaffold-report.md").write_text(report.render(ctx, rules.validate_context(doc)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
