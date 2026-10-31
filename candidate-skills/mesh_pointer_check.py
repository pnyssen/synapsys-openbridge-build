"""Offline check: the repo CLAUDE.md must carry the Mesh Queue read-first pointer set.

Candidate C1 from PKT-20261031-003. Zero network, zero Working Memory access: it
checks that the entrypoint file *names* the controlling sources, not that those
sources are current (that needs a live read, which CI does not have).
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_POINTERS = (
    "MESH_QUEUE/CURRENT.md",
    "NAVIGATOR_STATE_CAPSULE.json",
    "FOUNDATION_INDEX",
    "MESH_QUEUE_INSTRUCTION_BLOCK_v4.md",
    "NAVIGATOR_WO_SWARM_CONTRACT_v1_2.md",
    "SYNAPSYS_REFERENCE_MANIFEST.json",
    "HANDOVER_QUEUE.json",
    "EXECUTOR: claude_code",
    "24 hours",
)


def missing_pointers(text: str) -> list[str]:
    return [p for p in REQUIRED_POINTERS if p not in text]


def main(argv: list[str] | None = None) -> int:
    path = Path((argv or sys.argv[1:] or [str(Path(__file__).resolve().parent.parent / "CLAUDE.md")])[0])
    missing = missing_pointers(path.read_text(encoding="utf-8"))
    for p in missing:
        print(f"[MISSING] {p}")
    print(f"{len(REQUIRED_POINTERS) - len(missing)}/{len(REQUIRED_POINTERS)} pointers present in {path.name}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
