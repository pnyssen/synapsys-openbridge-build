#!/usr/bin/env python3
"""Generate NODE_PATCH_SPEC_v1_1.json from src/*.js (deterministic). Candidate only: does not touch n8n."""
import json, hashlib, sys, pathlib
root = pathlib.Path(__file__).resolve().parent
prelude = (root/'src/sha256_bytes.js').read_text()
def code(name): return (root/'src'/name).read_text().replace('/*__SHA256_PRELUDE__*/', prelude)
OLD = "ctx.source_checks.map(c=>'- '+c.path+' expected '+c.expected+' observed '+c.observed+' '+(c.match?'MATCH':'MISMATCH'))"
NEW = "ctx.source_checks.map(c=>'- '+c.path+' expected '+c.expected+' observed '+c.observed+' '+(c.match?'MATCH':'MISMATCH')+' bytes '+(c.bytes===undefined?'n/a':c.bytes)+' http '+(c.status===undefined?'n/a':c.status)+(c.mismatch_class?' class '+c.mismatch_class:''))"
RESP = {"fullResponse": True, "neverError": True, "outputPropertyName": "data", "responseFormat": "file"}
spec = {
  "schema": "synapsys.n8n-node-patch/0.1-CANDIDATE",
  "status": "CANDIDATE_NOT_APPLIED__NO_AUTHORITY_TO_DEPLOY",
  "target_workflow": {"id": "pnCEHhZWIDaRfrLe", "name_prefix": "Domain Lane Runner v1",
                      "precondition_versionId": "85db4098-1679-4e04-afd1-9374b6f0af8b", "precondition_active": True},
  "requires": ["attributable CR with x_test_evidence + x_rollback_plan registered BEFORE update_workflow",
               "D007 effect release", "rollback = re-apply versionId 85db4098-1679-4e04-afd1-9374b6f0af8b node definitions (n8n version history)"],
  "http_response_option_replacements": [
    {"node": "Read Packet", "path": "parameters.options.response.response", "replace_with": RESP},
    {"node": "Read Source", "path": "parameters.options.response.response", "replace_with": RESP}],
  "node_code_full_replacements": [
    {"node": "Gate Packets", "jsCode": code('gate_packets.js')},
    {"node": "Assemble Prompt", "jsCode": code('assemble_prompt.js')}],
  "node_code_replacements": [{"node": "Build Return", "find": OLD, "replace": NEW, "expect_count": 1}],
  "unchanged_by_design": ["Accept header", "credentials", "webhook auth", "List INBOX", "Select Lane Packets", "Pick Model", "OpenAI Lane", "File Return (create-only)"],
}
out = root/'NODE_PATCH_SPEC_v1_1.json'
out.write_text(json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False)+"\n")
print(out, hashlib.sha256(out.read_bytes()).hexdigest(), out.stat().st_size)
