"""SYNAPSYS.md kernel distribution/freshness tracking -- an extension of
this package, not a parallel mechanism.

Written against dispatch `CLAUDE_CODE_SYNAPSYS_MD_CONTROLLER_DISTRIBUTION_FRESHNESS_v0.1`
(filed at `05_AI_RETURNS_HASHED/WO-NAVIGATOR-MVP-INTEGRATION-AND-VISUAL-COMPLETION-001/
CLAUDE_CODE_DISPATCHES/`) and Hub's accepted architecture/prewrites
(`20260821--chatgpt-hub--design--synapsys-md-enterprise-orientation-
distribution-and-canonical-resolution--v0-1.md`, T1-T7 rebased prewrite
`...synapsys-md-common-gate-service-controller-integration--v0-2.md`). This
module answers T4's controller-preflight bullets 4-5 ("verify current
kernel/manifest consumption for REQUIRED_NOW participants only") with
concrete, testable logic -- it does not re-decide the architecture Hub
already produced, and it does not perform the Common Gate Service D009
assurance verdict (that remains a separate, independent return).

Why this lives here and not as a new module/package: `registry_resolver.py`
already resolves a target_lane to an authorised, activation-eligible
registry entry; `health_projection.py` already aggregates registry+jobs+
claims into a Navigator-facing per-domain status row with an
`authority_boundary` field that is always a verbatim echo, never an
upgrade; `replay_validator.py` already distinguishes a clean new event from
a duplicate. Kernel freshness is the same shape of problem -- "is this
recipient's last-known state current, and does that block anything" -- one
layer up (kernel/manifest identity instead of job claims). Building a
second registry/health/replay engine for it would be exactly the
"parallel mechanism" dispatch Q1 asks this module to rule out.

Zero I/O: no network, filesystem, subprocess, or wall-clock call anywhere
in this module, matching every other module in this package. Callers
(a controller preflight node, a test, or a Navigator projection builder)
supply all identities and timestamps and perform the actual sp_read/
list_workflows/etc. calls themselves.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

RECIPIENT_CLASS_VALUES = frozenset({"REQUIRED_NOW", "INFORM_ONLY", "FUTURE", "NOT_RELEVANT"})
FRESHNESS_STATES = frozenset({"FRESH", "STALE", "MISSING", "UNVERIFIABLE"})


@dataclass(frozen=True)
class KernelIdentity:
    """The currently-released SYNAPSYS.md + manifest identity. There is
    exactly one of these live at a time -- constructing a second one to
    represent a competing "current" is a caller-level modelling error this
    type does not itself prevent (that authority question belongs to
    D001/D007, not this module)."""

    version_label: str
    sha256: str
    manifest_sha256: str


@dataclass(frozen=True)
class RecipientConsumption:
    """What one environment/recipient has proven about its own consumption
    state, as of the last time anyone checked.

    `consumption_verifiable=False` is not a placeholder -- it is a real,
    permanent property of some distribution surfaces. The Claude/Cowork
    "Settings -> Cowork -> Global Instructions" box is the concrete example
    found this session: the WM-hosted CLAUDE.md's own header states it
    "must be manually replaced with a redirect pointer" and is "never
    auto-synced from any file." No controller can sp_read that box's
    contents. A recipient in this state can never resolve to FRESH or
    STALE -- only UNVERIFIABLE -- and that must surface as visible
    deployment debt, not be silently treated as either compliant or
    blocking."""

    target_lane: str
    recipient_class: str
    native_consumption_mechanism: str
    consumption_verifiable: bool
    last_consumed_sha256: Optional[str] = None
    last_consumed_manifest_sha256: Optional[str] = None
    last_consumed_at_iso: Optional[str] = None

    def __post_init__(self) -> None:
        if self.recipient_class not in RECIPIENT_CLASS_VALUES:
            raise ValueError(
                f"recipient_class {self.recipient_class!r} is not one of "
                f"{sorted(RECIPIENT_CLASS_VALUES)}"
            )


@dataclass(frozen=True)
class FreshnessResult:
    target_lane: str
    recipient_class: str
    state: str
    blocks_required_now_transaction: bool
    reason: str


def assess_freshness(current: KernelIdentity, recipient: RecipientConsumption) -> FreshnessResult:
    """Pure comparison: does this recipient's last-proven consumption match
    the currently released kernel identity?

    Only a REQUIRED_NOW recipient in STALE or MISSING state blocks its own
    transaction -- per the dispatch's explicit test requirement ("REQUIRED_NOW
    stale recipient blocks only its transaction" / "FUTURE/INFORM_ONLY debt
    does not block unrelated work"). UNVERIFIABLE never blocks (there is
    nothing a retry or a controller action can do about it), but it is
    never silently reported as FRESH either."""
    if not recipient.consumption_verifiable:
        state = "UNVERIFIABLE"
        reason = (
            f"{recipient.native_consumption_mechanism} has no programmatic "
            f"readback path -- staleness can be neither proven nor disproven"
        )
    elif recipient.last_consumed_sha256 is None:
        state = "MISSING"
        reason = "no recorded consumption of any kernel identity"
    elif (
        recipient.last_consumed_sha256 != current.sha256
        or recipient.last_consumed_manifest_sha256 != current.manifest_sha256
    ):
        state = "STALE"
        reason = (
            f"last consumed kernel {recipient.last_consumed_sha256!r} / "
            f"manifest {recipient.last_consumed_manifest_sha256!r}; "
            f"current released is {current.sha256!r} / {current.manifest_sha256!r}"
        )
    else:
        state = "FRESH"
        reason = "last consumed identity matches current released identity"

    blocks = recipient.recipient_class == "REQUIRED_NOW" and state in ("STALE", "MISSING")
    return FreshnessResult(
        target_lane=recipient.target_lane,
        recipient_class=recipient.recipient_class,
        state=state,
        blocks_required_now_transaction=blocks,
        reason=reason,
    )


def assess_all(current: KernelIdentity, recipients: List[RecipientConsumption]) -> List[FreshnessResult]:
    """Assesses every recipient independently -- one recipient's state
    never affects another's, matching the dispatch's "only deficient
    recipient is targeted" requirement without this function needing to
    know anything about routing or notification."""
    return [assess_freshness(current, r) for r in recipients]


def select_required_now_blockers(results: List[FreshnessResult]) -> List[FreshnessResult]:
    """The list a controller preflight actually needs: which REQUIRED_NOW
    recipients are currently blocking, and why. Never includes FUTURE/
    INFORM_ONLY/NOT_RELEVANT recipients regardless of their state."""
    return [r for r in results if r.blocks_required_now_transaction]


@dataclass(frozen=True)
class NavigatorKernelStatus:
    """The one Navigator-facing status row this module produces -- deliberately
    the same shape of object as `health_projection.HealthProjectionEntry`
    (sparse, pre-aggregated, no raw recipient list dumped into Navigator),
    so this does not become a second dashboard. Detail per recipient is
    available from `assess_all`'s return for an Architect/Steward audit
    view; this is the summary row."""

    released_version_label: str
    released_sha256: str
    required_now_total: int
    required_now_fresh: int
    coverage_percent: float
    stale_or_missing_required_now: List[str]
    unverifiable_required_now: List[str]
    last_checked_iso: str
    next_action: str


def build_navigator_status(
    current: KernelIdentity,
    results: List[FreshnessResult],
    now_iso: str,
) -> NavigatorKernelStatus:
    """Aggregates per-recipient results into the one sparse status row.
    Coverage is computed only over REQUIRED_NOW recipients -- a FUTURE/
    INFORM_ONLY environment being stale or entirely unconfigured never
    moves this number, matching the dispatch's non-blocking-debt
    requirement. An UNVERIFIABLE REQUIRED_NOW recipient counts against
    coverage (it is not proven fresh) but is reported in its own list, not
    conflated with a stale/missing one that the controller could plausibly
    still fix by re-dispatching."""
    required_now = [r for r in results if r.recipient_class == "REQUIRED_NOW"]
    fresh = [r for r in required_now if r.state == "FRESH"]
    stale_or_missing = [r.target_lane for r in required_now if r.state in ("STALE", "MISSING")]
    unverifiable = [r.target_lane for r in required_now if r.state == "UNVERIFIABLE"]

    coverage = (len(fresh) / len(required_now) * 100.0) if required_now else 100.0

    if stale_or_missing:
        next_action = (
            f"Re-dispatch current kernel {current.version_label} to: "
            f"{', '.join(sorted(stale_or_missing))}"
        )
    elif unverifiable:
        next_action = (
            f"Manually confirm/update unverifiable recipient(s): "
            f"{', '.join(sorted(unverifiable))} (no programmatic readback exists)"
        )
    else:
        next_action = "No action -- all REQUIRED_NOW recipients current"

    return NavigatorKernelStatus(
        released_version_label=current.version_label,
        released_sha256=current.sha256,
        required_now_total=len(required_now),
        required_now_fresh=len(fresh),
        coverage_percent=coverage,
        stale_or_missing_required_now=sorted(stale_or_missing),
        unverifiable_required_now=sorted(unverifiable),
        last_checked_iso=now_iso,
        next_action=next_action,
    )


def should_recheck(
    last_checked_iso: Optional[str],
    now_iso: str,
    min_recheck_interval_seconds: float,
) -> bool:
    """Recursive-loop guard: a controller preflight node calls this before
    running a fresh freshness pass. Returns True only if enough time has
    elapsed since the last check (or no check has ever run). This is the
    single debounce point -- callers must not run `assess_all` on every
    controller tick without consulting this first, or a kernel-identity
    change combined with a short health-tick interval could cause the
    controller to re-evaluate and re-dispatch every cycle indefinitely.

    An unparseable timestamp is treated as "always recheck" (fail toward
    checking again, not toward silently skipping forever), matching this
    package's existing "surface, don't guess" convention (see
    `outbox.detect_stale_claims`'s identical rule for unparseable
    `claimed_at_iso`)."""
    if last_checked_iso is None:
        return True
    try:
        last = datetime.fromisoformat(last_checked_iso)
        now = datetime.fromisoformat(now_iso)
    except (TypeError, ValueError):
        return True
    return (now - last).total_seconds() >= min_recheck_interval_seconds


def trigger_recheck_reason(
    kernel_changed: bool,
    manifest_changed: bool,
    new_environment_registered: bool,
    explicit_health_check: bool,
    substantive_job_starting: bool,
) -> Optional[str]:
    """Answers dispatch Q7 ("what controller event should trigger
    re-check") as a pure decision function rather than prose: given which
    of the five candidate trigger conditions are true this cycle, returns
    the single reason a recheck is warranted, or None if none apply.
    Priority order matters only for the returned label, not for whether a
    recheck happens -- any true input triggers one."""
    if kernel_changed:
        return "KERNEL_IDENTITY_CHANGED"
    if manifest_changed:
        return "MANIFEST_IDENTITY_CHANGED"
    if new_environment_registered:
        return "NEW_ENVIRONMENT_REGISTERED"
    if substantive_job_starting:
        return "SUBSTANTIVE_JOB_START"
    if explicit_health_check:
        return "EXPLICIT_HEALTH_CHECK"
    return None
