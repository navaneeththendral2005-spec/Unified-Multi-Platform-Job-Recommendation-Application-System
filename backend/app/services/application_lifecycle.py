"""Application lifecycle rules.

This module owns the normalized status vocabulary and valid state transitions.
It contains no database or FastAPI logic so platform adapters and notification
services can reuse the same rules later.
"""

from __future__ import annotations

# Canonical, persisted status values.
APPLICATION_STATUSES: tuple[str, ...] = (
    "applied",
    "application_viewed",
    "screening",
    "shortlisted",
    "assessment",
    "interview_scheduled",
    "interview_completed",
    "offer",
    "selected",
    "rejected",
    "withdrawn",
    "expired",
)

# Backward-compatible aliases for values used by the first implementation.
STATUS_ALIASES: dict[str, str] = {
    "interview": "interview_scheduled",
}

# A status can only move forward through these controlled transitions,
# except that active applications may end in rejected/withdrawn/expired.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "applied": frozenset(
        {"application_viewed", "screening", "rejected", "withdrawn", "expired"}
    ),
    "application_viewed": frozenset(
        {"screening", "rejected", "withdrawn", "expired"}
    ),
    "screening": frozenset(
        {"shortlisted", "assessment", "interview_scheduled", "rejected", "withdrawn", "expired"}
    ),
    "shortlisted": frozenset(
        {"assessment", "interview_scheduled", "rejected", "withdrawn", "expired"}
    ),
    "assessment": frozenset(
        {"interview_scheduled", "interview_completed", "rejected", "withdrawn", "expired"}
    ),
    "interview_scheduled": frozenset(
        {"interview_completed", "rejected", "withdrawn", "expired"}
    ),
    "interview_completed": frozenset(
        {"offer", "rejected", "withdrawn", "expired"}
    ),
    "offer": frozenset(
        {"selected", "rejected", "withdrawn", "expired"}
    ),
    "selected": frozenset(),
    "rejected": frozenset(),
    "withdrawn": frozenset(),
    "expired": frozenset(),
}


def normalize_status(status: str) -> str:
    """Return the canonical status or raise ValueError for an unknown value."""

    if not isinstance(status, str):
        raise ValueError("Application status must be a string")

    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    normalized = STATUS_ALIASES.get(normalized, normalized)

    if normalized not in APPLICATION_STATUSES:
        allowed = ", ".join(APPLICATION_STATUSES)
        raise ValueError(
            f"Invalid application status. Allowed statuses: {allowed}"
        )

    return normalized


def validate_status_transition(old_status: str, new_status: str) -> tuple[str, str]:
    """Normalize both statuses and enforce the lifecycle state machine."""

    old = normalize_status(old_status)
    new = normalize_status(new_status)

    if old == new:
        return old, new

    allowed = ALLOWED_TRANSITIONS.get(old, frozenset())

    if new not in allowed:
        raise ValueError(
            f"Invalid application status transition: {old} -> {new}"
        )

    return old, new


def get_allowed_next_statuses(status: str) -> list[str]:
    """Return sorted canonical statuses reachable from the given status."""

    normalized = normalize_status(status)
    return sorted(ALLOWED_TRANSITIONS[normalized])


def is_terminal_status(status: str) -> bool:
    """Return True when no further lifecycle transitions are permitted."""

    normalized = normalize_status(status)
    return not ALLOWED_TRANSITIONS[normalized]
