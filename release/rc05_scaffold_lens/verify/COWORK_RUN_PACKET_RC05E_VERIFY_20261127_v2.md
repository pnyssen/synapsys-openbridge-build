# COWORK RUN PACKET v2: verify RC05e on dev V20 (27 Nov 2026), read-only. Supersedes v1 (sha256 c9242a85...b14a), which stays filed. Changes: step 3 now hash-checks the script it runs and returns the full file list so Claude Code can recompute the tree hash; return fallback added.
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Issued by claude_code at the Steward's direction | NON_AUTHORISING. You execute only the steps below and return raw output. You do not edit scripts, change settings, install anything or create users. The Steward is already logged in to Odoo and to hPanel in this browser; never type, read or return a password, token or cookie.

## Step 1: UI checks (Odoo tab)
1. Read the script from Working Memory: 05_AI_RETURNS_HASHED/WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001/CANDIDATES/ui_verify_console_v1.js.txt (6,123 bytes). Its sha256 must be f8e1e97a97a75b41edd4f1f46e932886d5ca5964abc302bd084697d50c22bd1e; compute it over the exact text (for example crypto.subtle.digest in the page) before running. If it differs, stop and report both hashes.
2. Open https://odoo20.srv1536619.hstgr.cloud in the logged-in tab (the Steward is user "admin"), hard reload (Cmd+Shift+R), then run the script in the page context (DevTools console or your JavaScript tool). It only POSTs to /synapsys/lenses/data, /synapsys/scaffold/view and /synapsys/scaffold/context and prints ONE line of JSON.
3. Return that line verbatim.
Expected on a correct RC05e install: "checks":31,"passed":31,"failed":[]. Any failed item is a result to return, not something to fix.

## Step 2: screenshots (same tab)
Architecture > Lenses (level 1); then click "Context scaffold (read-only)" and capture it at Enrich with the "Technical details" line opened. Return both images. Do not resize the window.

## Step 3: installed-file check (hPanel Web console, read-only on the addon)
Open hPanel > VPS srv1536619 > Web console and paste exactly:
cd /root/rc04g_run/sob && echo "SCRIPT=$(sha256sum release/rc04g_baseline/rc04g_baseline_hash_20261126_v3.sh | cut -d' ' -f1)" && R=/root/verify_$(date -u +%H%M%S).txt && OUT=$R bash release/rc04g_baseline/rc04g_baseline_hash_20261126_v3.sh /opt/odoo20/addons/synapsys > /dev/null && echo "REPORT=$R" && sed -n '/## all source files/,/## completeness/p' $R && T=$(sed -n '/## tree hash/{n;p}' $R) && echo "TREE=$T" && { [ "$T" = "15c37960d1707be2be9b1dbdf18e623d82c97f78f1b009e02af34e46a5837e4b" ] && echo TREE_MATCHES_RC05E || echo TREE_DIFFERS; } && sha256sum $R
Expected: SCRIPT=fe9e401c949348b91093458c20949bb6ff9871271a78d9699c3d122270ba3469 (the filed v3 script; if it differs, stop and return the line), the 54-line file list, TREE=15c37960d1707be2be9b1dbdf18e623d82c97f78f1b009e02af34e46a5837e4b, TREE_MATCHES_RC05E, then the report's own sha256. Return ALL of it verbatim so Claude Code can recompute the tree hash from the list. The command reads the addon folder only and writes one report file under /root (not in the addon folder); that file is the only change on the box.

## Return and stop rules
File your return to the same CANDIDATES folder as RETURN_COWORK_RC05E_VERIFY_20261127_v1.md with the three outputs, the images and your own sha256 of the returned text; Claude Code recomputes and compares. If you cannot write to Working Memory, paste the return into the chat instead. Always use the hashes written in this packet, never a hash quoted in chat. Stop and report if: the script hash differs, any step asks for a credential, the page looks different from what the steps describe, or any output is unexpected. This packet authorises no install, upgrade, user, rights or data change.
