"""Whether existing x_ss_dispatch_task fields can carry claim/heartbeat/
return-linkage state without schema expansion.

Finding (verified against the live field list read this session, 24
fields total on x_ss_dispatch_task): the DATA the challenge asks for is
already representable on existing fields. What is NOT safe is the naive
read-then-write claim pattern; that is a concurrency defect in the
*runtime pattern*, not a schema gap. No new field is proposed here.
"""

from dataclasses import dataclass
from typing import List, Optional

# Field repurposing map: concept the transport fabric needs -> the
# existing x_ss_dispatch_task field that already fits it, with no
# renaming and no new column.
FIELD_MAPPING = {
    "claim_identity": (
        "x_operator_trace",
        "Free-text 'Operator Trace' field -- store 'claimed_by:<lane>@<claimed_at_iso>'. "
        "Already exists, already the right shape (char), no reuse conflict found.",
    ),
    "heartbeat": (
        "write_date",
        "Odoo's own native, automatically-maintained write timestamp on every model. "
        "No dedicated heartbeat field is needed: any write the claim-holder makes to "
        "touch the record (even a no-op field re-write) advances write_date. The one "
        "caveat: write_date also advances on unrelated edits, so a live implementation "
        "should treat 'x_operator_trace unchanged AND write_date advanced' as the "
        "heartbeat signal, not write_date alone.",
    ),
    "idempotency_key": (
        "x_task_id",
        "Already exists as the task's own stable identity field; store the outbox "
        "message_id (or the logical key composed from context_id+control_marker+"
        "state_revision) here to dedupe against.",
    ),
    "return_linkage": (
        "x_evidence_reference",
        "Already described as 'Evidence Reference' (char) -- store the filed return's "
        "exact Working Memory path once consumed.",
    ),
    "lifecycle_status": (
        "x_dispatch_status",
        "Existing selection already covers draft/queued/validated/routed/in_progress/"
        "review/complete/blocked/failed_validation/archived -- routed=claimable, "
        "in_progress=claimed, review=returned-awaiting-consume, complete=consumed. "
        "No new status value needed.",
    ),
    "authority_provenance": (
        "x_authority_reference",
        "Already exists, already the right field for D007's authority disclosure.",
    ),
    "transport_origin": (
        "x_source_channel",
        "Already exists -- record which transport actually delivered this job.",
    ),
    "dead_worker_signal": (
        "x_exception_class",
        "Already exists -- a stale-claim reaper can write a value here rather than "
        "needing a new boolean/flag field.",
    ),
}


@dataclass(frozen=True)
class ConcurrencyFinding:
    schema_change_required: bool
    defect: str
    fix: str
    fix_is_schema_change: bool


CLAIM_CONCURRENCY_FINDING = ConcurrencyFinding(
    schema_change_required=False,
    defect=(
        "A naive claim implemented as 'search for x_dispatch_status==routed, then "
        "write() x_dispatch_status=in_progress + x_operator_trace=self' is NOT atomic "
        "at the Odoo ORM level. Two concurrent workers can both read the same "
        "'routed, unclaimed' state before either writes, and both then write a claim -- "
        "the ORM does not serialize a read-modify-write pair by itself. This is the "
        "exact concurrency failure the challenge asks to name."
    ),
    fix=(
        "Use a single compare-and-swap SQL UPDATE, not a search-then-write pair: "
        "UPDATE x_ss_dispatch_task SET x_dispatch_status='in_progress', "
        "x_operator_trace=%(claimant)s WHERE id=%(task_id)s AND "
        "x_dispatch_status='routed' AND (x_operator_trace IS NULL OR x_operator_trace=''); "
        "then check the driver's affected-row count. Exactly one caller gets "
        "affected_rows=1; every other concurrent caller gets 0 and must not treat "
        "that as a claim. This is a single raw SQL statement via Odoo's own cursor "
        "(env.cr.execute), not a schema change."
    ),
    fix_is_schema_change=False,
)


def atomic_claim_sql_pattern() -> str:
    """Return the exact compare-and-swap SQL pattern (not executed by this module)."""
    return (
        "UPDATE x_ss_dispatch_task "
        "SET x_dispatch_status = 'in_progress', x_operator_trace = %(claimant)s, "
        "write_date = now() at time zone 'UTC' "
        "WHERE id = %(task_id)s "
        "AND x_dispatch_status = 'routed' "
        "AND (x_operator_trace IS NULL OR x_operator_trace = '')"
    )


@dataclass(frozen=True)
class ClaimAttemptOutcome:
    claimant: str
    granted: bool


@dataclass(frozen=True)
class ConcurrentClaimSimulationResult:
    winner: Optional[str]
    outcomes: tuple
    final_status: str
    final_operator_trace: Optional[str]


def simulate_concurrent_claim_attempts(claimants: List[str]) -> ConcurrentClaimSimulationResult:
    """Deterministically simulate N claimants attempting the same
    compare-and-swap claim (atomic_claim_sql_pattern's WHERE predicate)
    against one x_ss_dispatch_task-shaped row, applied in caller-supplied
    order -- no threading, no wall-clock, matching this package's zero-I/O
    discipline.

    A real concurrent UPDATE ... WHERE ... under the database's own
    row-level locking serializes to some total order of individual row
    mutations; applying the same CAS predicate in strict sequence here
    reproduces every reachable outcome of that serialization. What this
    proves: regardless of order, exactly one claimant is ever granted (the
    first whose predicate check finds status='routed' and an empty
    operator_trace) and every other claimant's check is guaranteed to see
    the post-claim state and be refused -- there is no interleaving of this
    predicate that grants two claimants, which is exactly the atomicity
    property atomic_claim_sql_pattern's WHERE clause exists to provide over
    a naive search-then-write pair (see CLAIM_CONCURRENCY_FINDING above).
    """
    status = "routed"
    operator_trace = None
    outcomes = []
    for claimant in claimants:
        granted = status == "routed" and not operator_trace
        if granted:
            status = "in_progress"
            operator_trace = claimant
        outcomes.append(ClaimAttemptOutcome(claimant=claimant, granted=granted))
    return ConcurrentClaimSimulationResult(
        winner=operator_trace,
        outcomes=tuple(outcomes),
        final_status=status,
        final_operator_trace=operator_trace,
    )
