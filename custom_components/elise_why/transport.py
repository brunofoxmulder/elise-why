"""Pure transport helpers for the Élise Investigator boundary."""

from __future__ import annotations

from typing import Any

VALID_STATUSES = frozenset({"confirmed", "probable", "indeterminate"})


def find_investigator_slug(
    apps: list[dict[str, Any]], suffix: str
) -> str | None:
    """Return the installed Investigator app slug, including repository prefix."""
    for app in apps:
        slug = app.get("slug")
        if isinstance(slug, str) and (
            slug == suffix or slug.endswith(f"_{suffix}")
        ):
            return slug
    return None


def investigator_url(slug: str, path: str, *, port: int) -> str:
    """Build the Supervisor internal-network URL for an app endpoint."""
    if not path.startswith("/"):
        raise ValueError("Investigator API path must start with '/'")
    hostname = slug.replace("_", "-")
    return f"http://{hostname}:{port}{path}"


def validate_investigation_result(
    payload: Any, *, expected_entity_id: str
) -> dict[str, Any]:
    """Validate the minimum immutable Investigator result contract."""
    if not isinstance(payload, dict):
        raise ValueError("Investigator response must be a JSON object")

    status = payload.get("status")
    if status not in VALID_STATUSES:
        raise ValueError("Investigator returned an unknown certainty status")

    entity_id = payload.get("entity_id")
    if entity_id != expected_entity_id:
        raise ValueError("Investigator response entity_id does not match the request")

    return payload
