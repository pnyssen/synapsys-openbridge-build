"""Deployment map: local dist file -> SharePoint Working Memory path.

Used by the deploy step (sp_write) and the manifest generator. The vault
root on SharePoint is 'Obsidian/'; Working Memory receipts go under
05_AI_RETURNS_HASHED/.
"""
import pathlib

import model

HERE = pathlib.Path(__file__).parent
DIST = HERE / "dist"
SP_VAULT = "Obsidian/"
CURRENT_REL = "00_SYSTEM/NAVIGATOR_SUPPORT/CURRENT/"

WM_FOLDER = ("05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/"
             "NAVIGATOR_L1_L2_L3_COMPLETE_DEPLOYMENT/")


def deploy_pairs():
    """(local_path, sharepoint_path) for every deployable surface."""
    pairs = [(DIST / "00_HOME.md", SP_VAULT + "00_HOME.md")]
    cur = DIST / "00_SYSTEM" / "NAVIGATOR_SUPPORT" / "CURRENT"
    for p in sorted(cur.rglob("*")):
        if p.is_file():
            rel = p.relative_to(cur).as_posix()
            pairs.append((p, SP_VAULT + CURRENT_REL + rel))
    return pairs


if __name__ == "__main__":
    for lp, sp in deploy_pairs():
        print(f"{lp.relative_to(HERE)} -> {sp}")
