"""Working Memory expected-return retrieval hardening.

Encodes, in pure zero-I/O logic, the mandatory retrieval sequence and
failure-classification doctrine already defined by the synapsys-state-
transfer-control skill (v1.3, references/connector-fallback-and-progressive-
execution.md, references/state-schema.md) -- plus the additional discovery
states this module was commissioned to add after a real 2026-08-18 failure:
the Hub treated an indexed-search miss for the expected D009 return
(NAVIGATOR_WAVE4_SIGNAL485_RAW_POSITIVE_D009_CHALLENGE_v1.0) as proof of
absence, in violation of the doctrine's own exact-path-first rule, before a
Steward-supplied sharing link resolved to a different file (the dispatch,
not the return).

This module never calls a connector itself. Every retrieval attempt
(SharePoint direct fetch, SynapSys sp_read, bounded folder enumeration,
indexed search, sharing-link resolution) is performed by the caller and
handed in as plain data; this module only classifies retrieval state and
recommends the next bounded step. It does not judge whether a resolved
file's body content is itself complete/partial against expected fields --
that is the state-transfer-control skill's own return-matching protocol
(EXPECTED_RETURN_COMPLETE / PARTIAL / etc.), a distinct, downstream concern
this module deliberately does not duplicate.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

# The doctrine's own existing failure-class vocabulary
# (connector-fallback-and-progressive-execution.md), reused verbatim --
# this module does not invent replacements for what already exists.
EXISTING_FAILURE_CLASSES = frozenset({
    "PRIMARY_CONNECTOR_UNAVAILABLE",
    "PRIMARY_CONTENT_EXTRACTION_FAILED",
    "BACKUP_MCP_UNAVAILABLE",
    "BACKUP_MCP_CALL_BLOCKED",
    "SEARCH_MISS_NOT_ABSENCE",
    "FILE_PRESENT_CONTENT_PENDING",
    "FILE_ABSENT_WITH_EVIDENCE",
    "PERMISSION_DENIED",
    "RUNTIME_UNAVAILABLE",
    "REGISTRY_UNAVAILABLE",
    "STALE_REVISION",
    "SCOPE_CONFLICT",
    "AUTHORITY_HELD",
})

# The state-schema doc's own existing return-classification vocabulary
# includes CONFLICTING_RETURN_HOLD -- reused here for the retrieval-level
# case of two candidate files both declaring the same expected identity.
EXISTING_RETURN_CLASSES = frozenset({"CONFLICTING_RETURN_HOLD"})

# New states this hardening adds, per the commissioning dispatch's required
# behaviour items 4 and 9. EXACT_PATH_RESOLVED is this module's own plain
# success terminal -- distinct from SEARCH_MISS_NOT_ABSENCE, which is
# reserved for the case where a search was actually attempted and missed
# while the exact-path route still succeeded (matching the doctrine's own
# named regression check verbatim, not stretched to cover every success).
NEW_DISCOVERY_CLASSES = frozenset({
    "EXACT_PATH_ABSENT_PENDING_DISCOVERY",
    "EXPECTED_RETURN_FOUND_NONCANONICAL_PATH",
    "LINK_RESOLVED_UNRELATED_FILE_REJECTED",
    "EXACT_PATH_RESOLVED",
})

ALL_CLASSES = EXISTING_FAILURE_CLASSES | EXISTING_RETURN_CLASSES | NEW_DISCOVERY_CLASSES


@dataclass(frozen=True)
class ExpectedReturn:
    """The identity a caller is trying to retrieve -- always known before
    retrieval starts, per the state-transfer-control skill's own
    mandatory-first-action rule (retrieve canonical state, then compare
    against expected_return before doing anything else)."""

    return_id: str
    filename: str
    parent_folder: str
    required_state_revision: int
    expected_lane: Optional[str] = None


@dataclass(frozen=True)
class RouteResult:
    """One caller-performed retrieval-route attempt, reported as plain
    data. `found` means the route resolved to *a* file identity (not
    necessarily the right one) -- content_available separately tracks
    whether that file's body was actually extracted."""

    attempted: bool = False
    found: bool = False
    content_available: Optional[bool] = None


@dataclass(frozen=True)
class DiscoveryResult:
    """A folder-enumeration or indexed-search attempt: a set of candidate
    filenames observed, never itself proof of absence when empty."""

    attempted: bool = False
    candidate_filenames: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SharingLinkResult:
    """A Steward-supplied sharing link, resolved through the SharePoint
    connector to one concrete file identity."""

    attempted: bool = False
    resolved: bool = False
    resolved_filename: Optional[str] = None
    resolved_return_id: Optional[str] = None
    resolved_state_revision: Optional[int] = None


@dataclass(frozen=True)
class CandidateFileIdentity:
    """A candidate file's own declared identity, read from its body --
    required before any misnamed/misfiled or link-resolved file is trusted
    as the expected return (required-behaviour item 9: never silently
    rename/mutate, never accept on filename proximity alone)."""

    filename: str
    return_id: Optional[str] = None
    consumed_state_revision: Optional[int] = None
    lane: Optional[str] = None


@dataclass(frozen=True)
class RetrievalOutcome:
    classification: str
    resolved_filename: Optional[str]
    reason: str
    next_action: str

    def __post_init__(self) -> None:
        if self.classification not in ALL_CLASSES:
            raise ValueError(f"unrecognised retrieval classification: {self.classification!r}")


def resolve_expected_return(
    expected: ExpectedReturn,
    sharepoint_direct: RouteResult,
    sp_read_fallback: RouteResult,
    exact_path_candidate_identity: Optional[CandidateFileIdentity] = None,
    folder_enumeration: DiscoveryResult = DiscoveryResult(),
    indexed_search: DiscoveryResult = DiscoveryResult(),
    discovery_candidate_identities: Tuple[CandidateFileIdentity, ...] = (),
    sharing_link: SharingLinkResult = SharingLinkResult(),
) -> RetrievalOutcome:
    """The full hardened sequence, required-behaviour items 1-10, in one
    call. Caller performs each route in the doctrine's required order
    (direct fetch -> sp_read fallback -> bounded enumeration -> supplementary
    search -> sharing-link resolution if supplied) and reports every
    attempted result here; attempts never made are left at their `attempted
    =False` default and are simply skipped by this classifier, not treated
    as failures.

    Item 11 (never advance A2+/PPV/authority/mutation merely because a
    candidate return is found) is a caller-side obligation this module
    cannot enforce directly -- it is documented here and tested by the
    regression suite asserting this module returns no field resembling an
    authority or mutation grant under any input.
    """

    # Steps 1-2: exact-path dual-route attempt (direct, then sp_read fallback).
    for route in (sharepoint_direct, sp_read_fallback):
        if not route.attempted:
            continue
        if route.found and route.content_available is False:
            return RetrievalOutcome(
                classification="FILE_PRESENT_CONTENT_PENDING",
                resolved_filename=expected.filename,
                reason="Exact-path route resolved a file identity but its content could not be extracted.",
                next_action="RETRY_CONTENT_EXTRACTION_ON_SAME_RESOLVED_IDENTITY",
            )
        if route.found:
            # Present at the exact path. A prior indexed-search miss, if one
            # was also attempted and came back empty, is reported explicitly
            # as SEARCH_MISS_NOT_ABSENCE rather than silently ignored --
            # matching the doctrine's own named regression check verbatim.
            # If no search was attempted at all, this is plain success.
            if indexed_search.attempted and not indexed_search.candidate_filenames:
                return RetrievalOutcome(
                    classification="SEARCH_MISS_NOT_ABSENCE",
                    resolved_filename=expected.filename,
                    reason="Indexed search returned no results, but the exact-path route resolved the file directly -- the search miss is not evidence of absence.",
                    next_action="CONSUME_RESOLVED_FILE_AT_EXACT_PATH",
                )
            return RetrievalOutcome(
                classification="EXACT_PATH_RESOLVED",
                resolved_filename=expected.filename,
                reason="Exact-path route resolved the file directly.",
                next_action="CONSUME_RESOLVED_FILE_AT_EXACT_PATH",
            )

    # Both exact-path routes attempted (or unattempted) and neither found the
    # file. This is a pending-discovery state, never a terminal absence.
    exact_path_absent = RetrievalOutcome(
        classification="EXACT_PATH_ABSENT_PENDING_DISCOVERY",
        resolved_filename=None,
        reason="Both exact-path routes (SharePoint direct fetch, SynapSys sp_read) failed to resolve the expected filename -- discovery continues, this is not yet absence.",
        next_action="RUN_BOUNDED_FOLDER_ENUMERATION_AND_SUPPLEMENTARY_SEARCH",
    )

    if not folder_enumeration.attempted and not indexed_search.attempted and not sharing_link.attempted:
        return exact_path_absent

    # Steps 5-7: bounded enumeration + supplementary search, deduped,
    # exact-filename check first (case A precondition inverted: exact path
    # failed here, but enumeration/search might still directly show it,
    # e.g. after a transient exact-path error).
    all_candidates = tuple(folder_enumeration.candidate_filenames) + tuple(indexed_search.candidate_filenames)
    if expected.filename in all_candidates:
        return RetrievalOutcome(
            classification="SEARCH_MISS_NOT_ABSENCE",
            resolved_filename=expected.filename,
            reason="Expected filename found by bounded folder enumeration/search despite the earlier exact-path routes failing -- retry direct retrieval on this exact path rather than declaring absence.",
            next_action="RETRY_EXACT_PATH_RETRIEVAL",
        )

    all_identities = tuple(discovery_candidate_identities)
    if exact_path_candidate_identity is not None:
        all_identities = all_identities + (exact_path_candidate_identity,)

    exact_matches = [
        c for c in all_identities
        if c.return_id == expected.return_id and c.consumed_state_revision == expected.required_state_revision
    ]
    if len(exact_matches) > 1:
        return RetrievalOutcome(
            classification="CONFLICTING_RETURN_HOLD",
            resolved_filename=None,
            reason=(
                f"{len(exact_matches)} distinct candidate files declare return_id "
                f"{expected.return_id!r} at the required revision {expected.required_state_revision!r} -- "
                "cannot select one without Hub arbitration."
            ),
            next_action="HOLD_FOR_HUB_ARBITRATION",
        )
    if len(exact_matches) == 1:
        match = exact_matches[0]
        return RetrievalOutcome(
            classification="EXPECTED_RETURN_FOUND_NONCANONICAL_PATH",
            resolved_filename=match.filename,
            reason=(
                f"File {match.filename!r} declares the exact expected return_id and required "
                f"state_revision but is not at the expected canonical filename {expected.filename!r} -- "
                "not silently renamed or consumed automatically."
            ),
            next_action="ROUTE_TO_HUB_FOR_IDENTITY_READBACK_DECISION",
        )

    stale = [c for c in all_identities if c.return_id == expected.return_id]
    if stale:
        return RetrievalOutcome(
            classification="STALE_REVISION",
            resolved_filename=stale[0].filename,
            reason=(
                f"Candidate file {stale[0].filename!r} declares return_id {expected.return_id!r} but "
                f"consumed_state_revision {stale[0].consumed_state_revision!r} does not match the "
                f"required {expected.required_state_revision!r}."
            ),
            next_action="DO_NOT_ADVANCE_QUEUE_HOLD_FOR_CORRECT_REVISION",
        )

    # Step 8: sharing-link resolution, only if the Steward supplied one.
    if sharing_link.attempted:
        if not sharing_link.resolved:
            pass  # falls through to bounded-discovery-exhausted below
        elif (
            sharing_link.resolved_return_id == expected.return_id
            and sharing_link.resolved_state_revision == expected.required_state_revision
        ):
            return RetrievalOutcome(
                classification="EXACT_PATH_RESOLVED"
                if sharing_link.resolved_filename == expected.filename
                else "EXPECTED_RETURN_FOUND_NONCANONICAL_PATH",
                resolved_filename=sharing_link.resolved_filename,
                reason="Sharing link resolved to a file whose declared return_id and consumed_state_revision match the expected return exactly.",
                next_action="CONSUME_RESOLVED_FILE_AS_THE_RETURN",
            )
        else:
            return RetrievalOutcome(
                classification="LINK_RESOLVED_UNRELATED_FILE_REJECTED",
                resolved_filename=sharing_link.resolved_filename,
                reason=(
                    f"Sharing link resolved to {sharing_link.resolved_filename!r} "
                    f"(return_id={sharing_link.resolved_return_id!r}), which does not match the "
                    f"expected return_id {expected.return_id!r} -- rejecting the link as the return "
                    "and continuing bounded discovery rather than accepting it."
                ),
                next_action="CONTINUE_BOUNDED_DISCOVERY_REJECT_LINK_AS_RETURN",
            )

    # Step 10: only after exact dual-route + bounded enumeration + bounded
    # identity search (+ sharing-link, if supplied) all fail.
    if folder_enumeration.attempted or indexed_search.attempted or sharing_link.attempted:
        return RetrievalOutcome(
            classification="FILE_ABSENT_WITH_EVIDENCE",
            resolved_filename=None,
            reason=(
                "Exact dual-route retrieval, bounded parent-folder enumeration and bounded "
                "identity search all failed to locate a file matching the expected return_id/revision."
            ),
            next_action="ONLY_NOW_MAY_STEWARD_BE_ASKED_FOR_RE_UPLOAD_OR_LOCATION",
        )

    return exact_path_absent
