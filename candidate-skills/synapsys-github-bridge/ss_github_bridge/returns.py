"""Navigator return: RETURNS/<task>--return.md (one verb, one tested number,
drill-down) plus an INBOX packet with verb implements_candidate. PPV Potential.

Produces text and a dict only. Filing to Working Memory is a separate, governed
step by whichever lane holds the write route; this module never writes there.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def render_return(task: str, verb: str, tested_number: str, drill: List[str],
                  artefacts: Dict[str, str], held: List[str]) -> str:
    lines = [f"# {task} — return", "",
             f"**Verb:** {verb}", f"**Tested number:** {tested_number}",
             "**PPV:** Potential · authority HELD · no Odoo, N8N, canon, registry or PPV change", "",
             "## Drill-down", *[f"- {d}" for d in drill], "",
             "## Artefacts (sha256)", *[f"- `{p}` `{h}`" for p, h in sorted(artefacts.items())], "",
             "## Held", *[f"- {h}" for h in held], ""]
    return "\n".join(lines)


def inbound_packet(packet_id: str, task: str, tested_number: str, artefacts: Dict[str, str],
                   created: str) -> Dict[str, Any]:
    return {
        "id": packet_id, "from": "claude-code", "verb": "implements_candidate",
        "work_object_id": "WO-NAVIGATOR-AUTONOMOUS-GOAL-PORTFOLIO-CONTROL-001",
        "context": "CTX-SS", "release_class": "RC-00",
        "job": f"{task}: dry-run candidate for CAP-009 (scan) and CAP-010 (GitHub mirror)",
        "ppv": "Potential",
        "authority": "Candidate only. No ACCEPT row for writes. No Odoo, N8N, canon, registry or PPV movement.",
        "artefacts": [{"path": p, "sha256": h} for p, h in sorted(artefacts.items())],
        "tested_number": tested_number,
        "excluded": ["GitHub or Working Memory write", "connector or configuration change (D007)",
                     "outsider contact"],
        "priority": "WATCH", "created": created,
    }


def packet_text(packet: Dict[str, Any]) -> str:
    return json.dumps(packet, indent=1, sort_keys=True) + "\n"
