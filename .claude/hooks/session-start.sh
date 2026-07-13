#!/bin/bash
set -euo pipefail

pip install --ignore-installed fastmcp || true

cat <<'EOF'
SYNAPSYS ECOSYSTEM STATE-AWARENESS REMINDER (from .claude/hooks/session-start.sh)

Before making ANY claim about SynapSys ecosystem state this session
(D001/Steward decisions, other AI lanes' status, whether something is
filed, current problem/contribution status) — fetch it fresh. Do not
answer from assumption or from anything that isn't a tool result obtained
in THIS session.

Canonical live sources, read via the SynapSys SharePoint MCP tools
(mcp__SynapSys_SharePoint__sp_read / sp_list):
  - 11_WORKING_MEMORY/05_AI_RETURNS_HASHED/AI_LANE_ALIGNMENT_REGISTER_v0.1.md
    (living, update-in-place register: ecosystem problems, lane roles,
    contribution ledger — the single most current cross-lane status source)
  - 11_WORKING_MEMORY/00_INDEX_AND_PROTOCOLS/WM_CURRENT_STATE_INDEX_v0.2.md
  - 11_WORKING_MEMORY/00_INDEX_AND_PROTOCOLS/WM_UNIVERSAL_AI_BOOT_INSTRUCTION_v0.1.md
    (defines required boot reads before producing durable artefacts)

Rule of thumb carried over from this session's own hard-learned lesson: a
parallel "Claude (Cowork)" session was independently updating that register
in real time, unnoticed for a long stretch, because nothing prompted a
fresh check. Don't repeat that — re-fetch, don't assume, and re-fetch again
before citing any hash or state as "current," since it may have moved again
since the last read even within one session.
EOF
