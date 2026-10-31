"""CLI: python -m ss_github_bridge run ...   (dry run; --commit is refused)

Writes only under --out (a local directory laid out like the Working Memory
folders it would later be filed to). Nothing is sent to GitHub or Working Memory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import inbound, mirror, returns, scan
from .cards import build_cards, validate_card

TASK = "github-bridge-dry-run"


def _write(root: str, rel: str, text: str, receipts: dict) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    receipts[rel] = returns.sha256_text(text)


def run(args: argparse.Namespace) -> int:
    if args.commit:
        print("REFUSED: commit/write flag is OFF until Steward ACCEPT is recorded.", file=sys.stderr)
        return 3
    try:
        signals = inbound.load_fixture(args.fixture) if args.fixture else inbound.fetch_live(args.repo)
    except inbound.NeedsCredential as exc:
        print(f"NEEDS YOU: {exc}", file=sys.stderr)
        return 2

    built = build_cards(signals, args.cap)
    cards = built["cards"]
    problems = [(c["id"], e) for c in cards for e in validate_card(c)]
    if problems:
        print(f"INVALID CARDS: {problems}", file=sys.stderr)
        return 1

    receipts: dict = {}
    for c in cards:
        _write(args.out, f"MESH_QUEUE/STREAMS/DRAFTS/{c['id']}--v0-1.json", mirror.card_bytes(c).decode(), receipts)
    plan = mirror.plan(cards)
    _write(args.out, "RETURNS/github-mirror-plan.json", json.dumps(plan, indent=1, sort_keys=True) + "\n", receipts)

    scores = [scan.score_lane(json.load(open(p, encoding="utf-8"))) for p in args.calllog]
    _write(args.out, "RETURNS/capability-scan.json", json.dumps(scores, indent=1, sort_keys=True) + "\n", receipts)

    tested = f"{len(signals)} signals -> {len(cards)} cards"
    drill = [f"deleted {len(built['deleted'])}, merged {len(built['merged'])}, over cap "
             f"{len(built['deferred_over_cap'])}; {len(plan['issues'])} mirror issues planned, writes 0; "
             f"{len(scores)} lane logs scored",
             f"cards: {', '.join(c['id'] + ' ' + c['category'] for c in cards) or 'none'}",
             f"deleted: {built['deleted'] or 'none'}", f"merged: {built['merged'] or 'none'}",
             f"deferred over cap: {built['deferred_over_cap'] or 'none'}",
             f"not mirrored (category): {plan['skipped_not_mirrored'] or 'none'}"]
    drill += [f"scan {s['lane']}: layers before first search {s['layers_read_before_first_search_n']}, "
              f"probes {s['probes_passed']}, calls {s['calls_used']}" for s in scores]
    held = ["GitHub issue creation (needs Steward ACCEPT, release class, token)",
            "Working Memory filing of these files (needs the common filing protocol)",
            "standard_refs checked_on: all '[n]' until checked against the publisher"]
    _write(args.out, f"RETURNS/{TASK}--return.md",
           returns.render_return(TASK, "implements_candidate", tested, drill, dict(receipts), held), receipts)
    packet = returns.inbound_packet(args.packet_id, TASK, tested, dict(receipts), args.date)
    _write(args.out, f"INBOX/{args.packet_id}.json", returns.packet_text(packet), receipts)
    print(tested)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ss_github_bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="inbound + mirror plan + scan + return (dry run)")
    src = r.add_mutually_exclusive_group(required=True)
    src.add_argument("--fixture", help="recorded API payload (JSON)")
    src.add_argument("--repo", help="owner/name; live read-only, needs GITHUB_TOKEN")
    r.add_argument("--calllog", action="append", default=[], help="lane call-log JSON (repeatable)")
    r.add_argument("--out", required=True)
    r.add_argument("--cap", type=int, default=5, help="max cards per run")
    r.add_argument("--packet-id", default="PKT-20261031-GHB-001")
    r.add_argument("--date", default="2026-10-31")
    r.add_argument("--commit", action="store_true", help="refused until Steward ACCEPT")
    r.set_defaults(fn=run)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
