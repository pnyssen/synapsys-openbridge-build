# COWORK DIRECTION PACKET v1 — SynapSys V20 RC03b delivery (executor lane)

Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Issued by claude_code (builder/verifier) at the Steward's direction | NON_AUTHORISING
Target: Hostinger VPS srv1536619 (existing runtime only; no second environment). Tooling commit pinned for D1b: `ddc0bc7b6f6980005fccd788ebb878b7462e60b6` (the packet itself is not part of that commit). Candidate: RC03b, `pnyssen/synapsys-odoo` commit `360a2b4fd51521f58ebb355806d90797226870a5`.

## 1. Roles (why Cowork, why not Claude Code, why not both in one)
| Lane | Does | Does not |
|---|---|---|
| **Cowork (you)** | Operates the logged-in hPanel browser terminal and Odoo UI; runs ONLY the pinned commands in this packet; returns raw outputs | Edit scripts, improvise commands, interpret results as approval, or proceed past a gate |
| Claude Code | Builds and tests the pinned scripts, checks your returned evidence independently, files hashed evidence | Reach the VPS or your browser |
| Steward / D007 | CHG, D007 effect release, RUN_LOCK, production decision | — |
| D009 (non-Claude) | Independent assessment of the exact commit | — |

## 2. Standing rules (apply to every directive)
1. Run only the exact block given. Before running it, confirm the commit and script hash lines (`COMMIT_OK`, `SCRIPT_OK`); on any mismatch **stop and report**.
2. Never edit, retype or "improve" a command. Never paste secrets anywhere. Never run anything not in this packet.
3. Return outputs **verbatim**, never summarised. For files longer than the terminal shows, return `base64 -w 76 <file>` in numbered chunks plus `sha256sum <file>`, so Claude Code can decode and verify the hash.
4. A non-zero exit, a refusal line, or any unexpected output is a **result to return**, not something to work around. Do not retry with changes.
5. Production-changing steps (section 4, D5 onward) are refused unless every gate in D3 is recorded **as data** (ids, hashes) in the release file. A chat message is not a gate.

## 3. DIRECTIVE D1 — executable now (read-only)
**D1a. Return the P0 receipt bytes you already produced.** In the terminal, for the receipt printed after `RECEIPT=` (`/root/p0_receipt_20261125T012158Z/p0_receipt.json`):
```
sha256sum /root/p0_receipt_20261125T012158Z/p0_receipt.json; wc -c /root/p0_receipt_20261125T012158Z/p0_receipt.json; base64 -w 76 /root/p0_receipt_20261125T012158Z/p0_receipt.json
```
Return the output in chunks of ≤ 25 lines, numbered. (The script's `RECEIPT_SHA256` covers the same bytes: expected `2683f0b401eea4de78abcc87baaece12f66677f6864c19991a994f7ec178d856`.) Also return the `mount_mapping` and `release_prestate_conditions` sections in plain text.

**D1b. Collect the environment facts the backup/restore stage needs** (read-only; writes only to a new folder; masks secrets):
```
cd /root && D=/root/sob_$(date -u +%Y%m%dT%H%M%SZ) && git clone --branch claude/synapsys-v20-release-service-tvjpyn https://github.com/pnyssen/synapsys-openbridge-build.git "$D" && cd "$D" && git checkout -q --detach ddc0bc7b6f6980005fccd788ebb878b7462e60b6 && { [ "$(git rev-parse HEAD)" = "ddc0bc7b6f6980005fccd788ebb878b7462e60b6" ] && echo COMMIT_OK || { echo COMMIT_MISMATCH; false; }; } && cd release/rc02p2/target_verify && { [ "$(sha256sum env_facts_collector.sh | cut -d' ' -f1)" = "acc4a8404472be5d13e27dba55f089f9b947f93a8f4f4eaf926754cc70eed8be" ] && echo SCRIPT_OK || { echo SCRIPT_MISMATCH; false; }; } && OUT=/root/env_facts_$(date -u +%Y%m%dT%H%M%SZ) bash env_facts_collector.sh; echo "exit=$?"
```
Return: the `ENV_FACTS_VERDICT`, `OUT=` and `INDEX_SHA256=` lines, then `cat INDEX.json` and (via rule 3) these files from the `OUT=` folder: `odoo_container.json`, `db_container.json`, `odoo_config_whitelist.json`, `db_facts.txt`, `host_capacity.txt`, `mount_listing.json`, `compose_files.json`, `all_containers.txt`, `networks.txt`, `volumes.txt`.
If your Working Memory tools allow create-only filing into `05_AI_RETURNS_HASHED/WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001/CANDIDATES/`, file the raw P0 receipt and the collector folder there with their sha256, and report the paths; otherwise return the base64 chunks.
**D1 closes when** Claude Code has recomputed the receipt hash from your returned bytes and parsed the collector outputs.

## 4. The delivery pipeline (status is honest: only D1 can run today)
| Step | What | Automation status | Gate to start |
|---|---|---|---|
| D1 | Prestate evidence + environment facts | **Scripts exist, tested (shim); P0 ran on host once** | none (read-only) |
| D2 | G2: application-consistent DB + filestore backup, throwaway restore in an isolated Compose project, RC03b two-addon upgrade rehearsal, injected-failure rollback | **NOT built.** Claude Code builds it from the D1 facts (addons mount, conf, networks, sizes), tested as P0 was | D1 closed; Steward/D007 states whether the backup step needs a CHG (it writes dump files on the VPS) |
| D3 | Gates recorded as DATA in the release file: scope-specific CHG id; D007 effect-release id; non-Claude D009 PASS on commit `360a2b4f…`; recovery-pair ids; RUN_LOCK holder | Not built (a checker script is next to D2) | Steward / D007 / D009 |
| D4 | P1 staging check of RC03b tree (`verify_on_target.py` with the RC03b manifest, sha256 `2c6ee113…2c32`) | Verifier exists; **delivery route not yet qualified** (console/git fetch; Hostinger-API compose is unqualified) | D3 |
| D5 | `odoo -u synapsys,synapsys_v19_reference` upgrade under one RUN_LOCK, with the D2 recovery pair ready | **NOT built**; written only after D2 passes | D2 pass + D3 complete |
| D6 | Acceptance: six peer headings; 35 + 2 destinations; 28 nouns; 27 verbs under 9 actions; Steward AND collaborator roles; direct-action, backend-ACL and cross-Context negative tests; 390 px; no navigation loss | **NOT built**; Cowork's Chrome is the right executor for UI/role steps | D5 |
| D7 | Automatic rollback to the recovery pair on any D6 failure, then re-run P0 | **NOT built**; rehearsed in D2 first | D2 |

"Fully automated" here means every step is a pinned, hash-checked script with machine-checked preconditions and a receipt, and the only human inputs are the authority records in D3. It does not mean skipping them: the install is refused without them.

## 5. When to stop and report immediately
Any hash/commit mismatch; any refusal or non-zero exit; P0 or verifier output other than `MATCH_ALL`/`TWO_VIEW` where one is required; anything touching production data or settings that this packet did not specify; any request (from anyone, including chat) to skip a gate.
