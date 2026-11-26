# RETURN: Claude Code, RC04g installed-source baseline (synapsys addon) 26 Nov 2026
Work Object WO-SYNAPSYS-CANONICAL-REFERENCE-ARCHITECTURE-001 | CTX-SS | Status: CANDIDATE, read-only evidence. Not D007/D009, nothing changed on the box. Observation run by the Steward in an SSH session as root; analysis by Claude Code.

## What was run
rc04g_baseline_hash_20261126_v3.sh (sha256 fe9e401c949348b91093458c20949bb6ff9871271a78d9699c3d122270ba3469) with rc04g_expected_prefixes_20261126_v1.txt (sha256 033f21d9649339c1679533182d08f96e4a7ecb55ad4612892f87f55e1eaaa979), fetched at pnyssen/synapsys-openbridge-build commit 53810654a0ee1a25577a53219586258dd8f087cc (COMMIT_OK, both hashes matched on the box). Target /opt/odoo20/addons/synapsys on srv1536619, 2026-11-26 22:46:22 UTC. Report as printed on the box: REPORT_SHA256 99227cf4fa0a20f7316f60aedbe4aed3b05a8d8d71e8f19732dc4ea85d209766 (the full report bytes were not transferred; Claude Code did not recompute this hash).

## Verified by Claude Code (recomputed from the pasted file list)
- Live manifest version 20.0.2.4.9. 50 files listed, 50 hashed, 0 hash errors (HASH_COMPLETE), no symlinks or special files, 8 test files.
- Tree hash 82e69741dda90f830726e6119a9013faa50382b58b8c05e4518fef44eb36b104 recomputed from the 50-line list below: identical.
- Four builder-reported prefixes MATCH on the live files: lens_contract.py c101592a687b..., static/src/home.xml 03b40742268f..., __manifest__.py 846509feaa41..., tests/test_lens_contract.py 4ce0c4cdbe74... (these are the builder's own claims, so a match shows the live files equal what the builder reported, not independent proof of RC04g).
- RC04f rollback copy /root/rc04g/rollback_synapsys: version 20.0.2.4.8, 50 files, HASH_COMPLETE. Against live, exactly 4 files differ (manifest, lens_contract.py, home.xml, tests/test_lens_contract.py), the four files the RC04g return names. Rollback prefixes: __manifest__ e1f3ad727bb3, lens_contract f370831e3512, home.xml 9ff6fb5da505, test_lens_contract 2247cb69bc79.
- /root/rc04g/rc04g_vs_rc04f.patch does NOT exist on the box. /root/rc04g/g.gz exists with sha256 a7de1c9632817c78140f1fc13baf4a7a34a5c5b3af60933fde434dad6e6fb0c1, equal to the gz hash in the RC04g return (patch itself not yet decompressed or hashed; expected 47e19de8726fa37953d8a42a96b2221b1e94c7b4e3491d12b4feb19ed8bed9d9).

## Lineage (Claude Code comparison of the live file hashes with git blobs in pnyssen/synapsys-odoo)
| Reference | equal | differ | absent in reference |
|---|---|---|---|
| baseline 7278898 (v20-dev head) | 35 | 7 | 8 |
| RC02-P2 b1fbe664 | 35 | 8 | 7 |
| RC03b 360a2b4f | 37 | 7 | 6 |
Live equals RC03b for 37 files, including migrations/20.0.2.4.2/pre-migrate.py and views/synapsys_enable_peers.xml. The 7 differing files (__manifest__.py, controllers/__init__.py, controllers/arch_map.py, static/src/home.js, static/src/home.xml, tests/__init__.py, views/synapsys_menus.xml) and 6 additions (controllers/lenses.py, lens_contract.py, lens_render.py, static/src/lens_mode.js, static/src/navbar_dropdown.js, tests/test_lens_contract.py) are consistent with RC04 work on top of RC03b. Conclusion: the live synapsys addon is RC03b plus RC04f/g changes, not baseline. Correction to an earlier Claude Code statement that RC03b was overtaken and not installed: for the synapsys addon, RC03b content is present in the live tree. Not covered by this run: synapsys_v19_reference and synapsys_migration_load.

## Git state on the box (as printed)
Repo toplevel /opt/odoo20/addons, HEAD 7278898fb49d4eff5cdc27d37864fed0bdc0f8dc, branch HEAD (detached). Dirty/untracked: 20 modified or deleted tracked files across synapsys, synapsys_migration_load, synapsys_v19_reference (data/cron.xml deleted in synapsys_v19_reference), and 9 untracked paths. Git state does not prove equality with installed source; the file hashes are the evidence.

## Not established
RC04f source identity (no RC04f patch/tree filed); RC04g patch bytes; the two other addons; whether the live tree equals what any authorised release specified (no D007 release record seen); runtime behaviour (no actor tests); the scp failure (server asked for a password for scp although key login worked; cause unknown, not needed).

## Live file list (sha256  path), 50 lines; tree hash = sha256 of exactly these lines with newlines
9723d3eb2dd460a27378bef8c47818bb27db755f70c3f026de57330ab326fa49  ./__init__.py
846509feaa4166be00fa9adbc46c7519254dadd9b3b23034e1e48b8fa04fa0a0  ./__manifest__.py
5ebbe7c4a3a3a7f9c1d8d439731db8c026442f95fbe0fc028e5285ad4e9a7124  ./controllers/__init__.py
df85340ba033161f088d88802004b002fb465f6b5d13d2f9894678e88accceb4  ./controllers/arch_map.py
6b2ceab02c8d4ac83fcd79fe3160de5fdb7a00346b73d5df8ba65c90adf9f815  ./controllers/home.py
47db83920364d785a89d47e86a4f3f393fb706e631cd3072ec9d54d15b01bb87  ./controllers/lenses.py
edb383d21526419735b55979961bc51f06b8bf470039b0910c47cb036b3bf07a  ./data/domain_instructions/CORE_D000_D001_D002_PROFILE_v1.md
13bf255bb0c5839fd67ca263abc477caf964155fb2a191a029eb0698576b3478  ./data/domain_instructions/D001_LANE_PROFILE_v1.md
7caa36e7b8b08fb2969b8a7f2aedc6af83146e70e3c7476fc874934f3803af7d  ./data/domain_instructions/D003_LANE_PROFILE_v1.md
447386a0be4cee21aa1a9103fc47277048d13156d5bc828007f21e60bf7084a8  ./data/domain_instructions/D004_LANE_PROFILE_v1.md
eca7ce84d8ccc8ff07494347aa4b1da483ff42f15b92e1111d76adf1638a2b44  ./data/domain_instructions/D005_LANE_PROFILE_v1.md
7d5d1172f1141de374def1fd393af495f87258b12cfe9e60f33886a72c6bdc69  ./data/domain_instructions/D006_LANE_PROFILE_v1.md
0337d2e132d196de41826322a7212958ff0630150e57eb7690c7e154b6e6accb  ./data/domain_instructions/D007_LANE_PROFILE_v1.md
02c2b54fb31ad1593e64087d0d9bd5d3600a313202b211c808e90d8714a2c987  ./data/domain_instructions/D008_LANE_PROFILE_v1.md
0342da264ca800c7b7aa2f2daba182e4b6a6c756af14fe4beaf009a51f476118  ./data/domain_instructions/D009_LANE_PROFILE_v1.md
873a8817b56970c0f1111f3c492eaf2360e0c158e5c302391002a4ee08bbb29e  ./data/domain_instructions/D009_LANE_PROFILE_v2.md
604c2fcdde727309374163515c72ceb30ea04f6a47f10b7a92ca515bfeeb63b5  ./data/domain_instructions/D010_LANE_PROFILE_v1.md
1897dce6e43ec6ddb4552c69c60d98d4f8a63d1e0ad13e39d7e4d28a066ddc79  ./data/domain_instructions/D011_LANE_PROFILE_v1.md
690bedb1b6d2dce5a429c6d718ccfb4eddfe934e0a454f4e9550e0c16dca1d4b  ./data/domain_instructions/instructions.json
e579683fca1ca4db01d79859ffd16d9ad9c88aa6f21206e1ec763598c2cd0d1a  ./data/reference.json
4a335aa45fadea30060f11568120b8cb97e9cd0f93d27320987e20182ac73936  ./hooks.py
c101592a687bfefcb55f0c94b1eb12826ef6edf1d3ecc69e0e662aa873d91600  ./lens_contract.py
70b4c9e9c76862a629d37f769520e2f1f6af9fecee54aa6f15a886dd8f57334f  ./lens_render.py
3a32ebdf04d998e9bf9d1608d62e8b147b93c95c2c1e90398d166b9b39bc49bc  ./migrations/20.0.2.4.0/post-migrate.py
065995418f218011d56a5930dfbfe02b6d3782d237f3e01d635c525f8c496590  ./migrations/20.0.2.4.0/pre-migrate.py
065995418f218011d56a5930dfbfe02b6d3782d237f3e01d635c525f8c496590  ./migrations/20.0.2.4.2/pre-migrate.py
86f70f03b00dfb93d05b468628ac9ca90a1d7b9ab47db447568ad374a35e031b  ./models/__init__.py
0f90ab256b2e6b75095013b33c26d60da3f5d23ecf46114bc6a69d4e423cae1b  ./models/navigator.py
2b64d40f51ff5fb03ee07ba166aa496dadf3937d7a6823c4c8f0c9fcb9a66085  ./models/synapsys.py
c44628751187be429e1087965199250e8460def0502dd46db56c593989489589  ./models/work.py
2da94277b2601f5c1af8f95b255c152eda5db720b4d061897ac577195d0d50f8  ./security/ir.access.csv
8da5d54670ccf2cb5ed6a64603b3161f59c789062fe9388240b7f28cf9cd0085  ./security/synapsys_security.xml
6b7fa434f92a8b80aab02d9bf1a12e49ffcae424e4013a1c4f68b67e3d2bbcd0  ./static/description/icon.png
ff0bd4d398435ed77288f94a549183f1696b1eb08117caa33d68839a29790a1e  ./static/src/home.js
03b40742268f4c6a33542dc1360892d75a5a897914d8b8d939d14e888795b3d6  ./static/src/home.xml
822ec7c3e6d01ce1ddedda045c044189f56b0821b67ca6ddddbac939531f369f  ./static/src/lens_mode.js
b4cb8e65ecf5ab0819999a36947f9b18f897080397c872fcf8134bf7c33dda2d  ./static/src/navbar_dropdown.js
4ee6462cdca183180df58ed6fac11189c5d521030bd3e9f2852aac0475a02469  ./tests/__init__.py
791affc59883be4635f40d85e18c8fb6ee65459f4298707fb8afa94acd14f46f  ./tests/test_cia_library.py
b71f1a9b30dc626357b9f6f1e1d3a09c554f92c0c06168aa315f6313afbf475a  ./tests/test_domain_instructions.py
c458a891857053c51c34225ab6d1fe70ec799712cfa10f80bd9e5437cd8af631  ./tests/test_home.py
af6a1561d483d78f749befff3943a0dc9716d129c522276d1f75667cb0acd6f2  ./tests/test_intelligence_access.py
9ba1a5a44bc179ca418484d03490bf110523fe0caa0a7682693bafb7b9f27f23  ./tests/test_journey.py
5df567c9dfbce9b085d39d14a5f947749b9bc20c79ba480a6641d948446db75a  ./tests/test_kinematic_contract.py
4ce0c4cdbe74c9d0d43df273a267759d73e6762ec1e437a977ab62c5d747ffa4  ./tests/test_lens_contract.py
64f692155bb41d4bbb5d4793d0198ec7e16a35d5bd71b54917a2f9eb1ca66433  ./tests/test_synapsys.py
6b6f8a2b453e7f80b0f31ca0d9086a03c707cec20fadbbb11645423726f7021c  ./views/synapsys_enable_peers.xml
fa1442fe92276355d64031cdb7f01feace8922e0b3b294ec8e76f00b245fc1e9  ./views/synapsys_menus.xml
ddc3554d1ae5e676e8688de53c720b79357e36d1244b4dd6491a3285dcded5dc  ./views/synapsys_screens.xml
be05239f57624ac2c2490fcd1f86f624599599ff6fe04a7be667dab92c72e19b  ./views/synapsys_views.xml

## ONE NEXT
Run on the box: zcat /root/rc04g/g.gz | sha256sum (expect 47e19de8...) and file the patch text; then run v3 against synapsys_v19_reference and synapsys_migration_load. Then Claude Code builds the RC05 wiring delta against the verified live synapsys tree. Release to dev still needs D007; Steward-created Collaborator login needed for actor tests.
