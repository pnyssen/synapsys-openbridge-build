"""RC06h: the two renderer changes the contract requires, expressed so the earlier tests keep pinning their own golden files byte for byte.
R5: one CSS rule changes (trust table cells after the first now wrap instead of clipping). R6: an answer that opens with its own status word and a
colon drops that prefix; in the whole declaration set only SCR.PRODUCT.NOUN has the pattern ("OPEN: placed at ..."). Nothing else differs, which the
tests that use these helpers prove by comparing against the unchanged RC06a / RC06e golden files."""
OLD_RULE = ".syn-sc .tt td>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
NEW_RULE = (".syn-sc .tt td:first-child>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
            ".syn-sc .tt td:not(:first-child)>div{white-space:normal;overflow-wrap:anywhere}")
PREFIXED = {"SCR.PRODUCT.NOUN": "OPEN: "}


def undo_r5(h):
    assert NEW_RULE in h or "<style>" not in h
    return h.replace(NEW_RULE, OLD_RULE)


def undo_r6(sid, h):
    p = PREFIXED.get(sid)
    return h.replace('data-slot="answer">', 'data-slot="answer">' + p, 1) if p else h


def undo(sid, h):
    return undo_r6(sid, undo_r5(h))
