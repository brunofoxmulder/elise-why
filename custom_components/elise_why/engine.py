"""Read-only causal explanation engine for Élise Why V0.1."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

WhyStatus = Literal["confirmed", "probable", "indeterminate"]
SourceType = Literal["automation", "script", "user", "integration", "unknown"]

LOOKBACK_WINDOWS = (
    timedelta(minutes=5),
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(hours=24),
)
CAUSAL_FALLBACK_GAP = timedelta(minutes=2)

_ENTITY_ID_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_STATE_SOURCE_RE = re.compile(r"^state of (?P<entity_id>[a-z0-9_]+\.[a-z0-9_]+)$")
_NUMERIC_SOURCE_RE = re.compile(
    r"^numeric state of (?P<entity_id>[a-z0-9_]+\.[a-z0-9_]+)$"
)
_CANNOT_DETERMINE = "Je ne peux pas déterminer précisément la raison de cette dernière action."


class LogbookProvider(Protocol):
    async def get_logbook(
        self,
        *,
        entity_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Return Logbook rows for one entity."""


class WhyEngine:
    """Explain only the latest causal action of an entity."""

    def __init__(self, provider: LogbookProvider) -> None:
        self._provider = provider

    async def explain(
        self,
        entity_id: str,
        *,
        at_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Return a conservative causal explanation."""
        entity_id = entity_id.strip().lower()
        if not _ENTITY_ID_RE.fullmatch(entity_id):
            return self._result(entity_id, "indeterminate", _CANNOT_DETERMINE)

        now = (at_time or datetime.now(UTC)).astimezone(UTC)
        entries = await self._get_recent_entity_logbook(entity_id, now)
        action = self._find_latest_causal_action(entries, entity_id)
        if action is None:
            return self._result(entity_id, "indeterminate", _CANNOT_DETERMINE)

        action_time = self._parse_when(action.get("when"))

        context_entity = str(action.get("context_entity_id") or "")
        context_domain = str(action.get("context_domain") or "")
        source_name = action.get("context_name")

        automation_linked = (
            str(action.get("context_event_type") or "") == "automation_triggered"
            or context_domain == "automation"
            or context_entity.startswith("automation.")
        )
        raw_source = self._automation_trigger_source(action, entries)
        if raw_source:
            reason, status = await self._reason_from_trigger_source(
                raw_source,
                action,
                action_time,
            )
            return self._result(
                entity_id,
                status,
                reason,
                source_type="automation",
                source_entity_id=context_entity if context_entity.startswith("automation.") else None,
                source_name=source_name,
                trigger_source=raw_source,
                action_time=action_time,
            )

        if automation_linked:
            return self._result(
                entity_id,
                "probable",
                _CANNOT_DETERMINE,
                source_type="automation",
                source_entity_id=context_entity if context_entity.startswith("automation.") else None,
                source_name=source_name,
                action_time=action_time,
            )

        if context_domain == "script" or context_entity.startswith("script."):
            return self._result(
                entity_id,
                "confirmed",
                f"Parce que le script {source_name or context_entity} l'a commandé.",
                source_type="script",
                source_entity_id=context_entity or None,
                source_name=source_name,
                action_time=action_time,
            )

        # Automation attribution has priority: a child automation context can
        # legitimately retain a parent user id.
        if action.get("context_user_id"):
            return self._result(
                entity_id,
                "confirmed",
                "Parce qu'il a été commandé directement.",
                source_type="user",
                action_time=action_time,
            )

        if action.get("context_domain") or action.get("context_service"):
            return self._result(
                entity_id,
                "probable",
                _CANNOT_DETERMINE,
                source_type="integration",
                action_time=action_time,
            )

        return self._result(
            entity_id,
            "indeterminate",
            _CANNOT_DETERMINE,
            source_type="unknown",
            action_time=action_time,
        )

    async def _get_recent_entity_logbook(
        self,
        entity_id: str,
        now: datetime,
    ) -> list[dict[str, Any]]:
        last_response: list[dict[str, Any]] = []
        for window in LOOKBACK_WINDOWS:
            response = await self._provider.get_logbook(
                entity_id=entity_id,
                start_time=now - window,
                end_time=now,
            )
            last_response = [row for row in response if isinstance(row, dict)]
            if self._find_latest_causal_action(last_response, entity_id):
                return last_response
        return last_response

    def _find_latest_causal_action(
        self,
        entries: list[dict[str, Any]],
        entity_id: str,
    ) -> dict[str, Any] | None:
        target = [row for row in entries if row.get("entity_id") == entity_id]
        if not target:
            return None

        target.sort(
            key=lambda row: self._parse_when(row.get("when")) or datetime.min.replace(tzinfo=UTC)
        )
        latest = target[-1]
        if self._has_causal_context(latest, entries):
            return latest

        latest_time = self._parse_when(latest.get("when"))
        if latest_time is None:
            return None

        for candidate in reversed(target[:-1]):
            candidate_time = self._parse_when(candidate.get("when"))
            if candidate_time is None:
                continue
            if latest_time - candidate_time > CAUSAL_FALLBACK_GAP:
                break
            if self._has_causal_context(candidate, entries):
                return candidate
        return None

    @staticmethod
    def _has_causal_context(
        entry: dict[str, Any],
        entries: list[dict[str, Any]],
    ) -> bool:
        if any(
            entry.get(key)
            for key in (
                "context_event_type",
                "context_entity_id",
                "context_source",
                "context_user_id",
                "context_domain",
                "context_service",
            )
        ):
            return True

        context_id = entry.get("context_id")
        if not context_id:
            return False
        return any(
            other.get("context_id") == context_id
            and str(other.get("entity_id") or "").startswith("automation.")
            for other in entries
        )

    @staticmethod
    def _automation_trigger_source(
        action: dict[str, Any],
        entries: list[dict[str, Any]],
    ) -> str | None:
        event_type = str(action.get("context_event_type") or "")
        context_domain = str(action.get("context_domain") or "")
        context_entity = str(action.get("context_entity_id") or "")

        linked = (
            event_type == "automation_triggered"
            or context_domain == "automation"
            or context_entity.startswith("automation.")
        )

        if linked and action.get("context_source"):
            return str(action["context_source"])

        context_id = action.get("context_id")
        if not context_id:
            return None

        for row in reversed(entries):
            if row.get("context_id") != context_id:
                continue
            if str(row.get("entity_id") or "").startswith("automation.") and row.get("source"):
                return str(row["source"])
        return None

    async def _reason_from_trigger_source(
        self,
        raw_source: str,
        action: dict[str, Any],
        action_time: datetime | None,
    ) -> tuple[str, WhyStatus]:
        source = raw_source.strip().lower()

        state_match = _STATE_SOURCE_RE.match(source)
        if state_match:
            trigger_entity = state_match.group("entity_id")
            state = action.get("context_state")
            if state is None:
                state = await self._state_near_action(trigger_entity, action_time)
            return (
                self._state_reason(trigger_entity, state),
                "confirmed" if state is not None else "probable",
            )

        numeric_match = _NUMERIC_SOURCE_RE.match(source)
        if numeric_match:
            return self._numeric_reason(numeric_match.group("entity_id")), "confirmed"

        if source == "sun event sunset":
            return await self._sun_reason("sunset", action_time)
        if source == "sun event sunrise":
            return await self._sun_reason("sunrise", action_time)

        if source == "time" or source.startswith("time set in "):
            return "Parce que l'heure programmée a été atteinte.", "confirmed"
        if source == "time pattern":
            return "Parce que la condition horaire programmée a été atteinte.", "confirmed"

        return _CANNOT_DETERMINE, "probable"

    async def _state_near_action(
        self,
        entity_id: str,
        action_time: datetime | None,
    ) -> Any | None:
        if action_time is None:
            return None

        rows = await self._provider.get_logbook(
            entity_id=entity_id,
            start_time=action_time - timedelta(hours=6),
            end_time=action_time,
        )
        for row in reversed(rows):
            if row.get("entity_id") == entity_id and row.get("state") is not None:
                return row["state"]
        return None

    async def _sun_reason(
        self,
        event: Literal["sunset", "sunrise"],
        action_time: datetime | None,
    ) -> tuple[str, WhyStatus]:
        if action_time is None:
            return _CANNOT_DETERMINE, "probable"

        target_state = "below_horizon" if event == "sunset" else "above_horizon"
        rows = await self._provider.get_logbook(
            entity_id="sun.sun",
            start_time=action_time - timedelta(hours=3),
            end_time=action_time,
        )

        transition_time = None
        for row in reversed(rows):
            if row.get("entity_id") != "sun.sun":
                continue
            if str(row.get("state") or "").lower() != target_state:
                continue
            transition_time = self._parse_when(row.get("when"))
            if transition_time:
                break

        if transition_time is None:
            return _CANNOT_DETERMINE, "probable"

        minutes = max(0, round((action_time - transition_time).total_seconds() / 60))
        if event == "sunset":
            verb = "couché"
        else:
            verb = "levé"
        suffix = "minute" if minutes == 1 else "minutes"
        return f"Parce que le soleil s'est {verb} il y a {minutes} {suffix}.", "confirmed"

    @staticmethod
    def _state_reason(entity_id: str, state: Any) -> str:
        object_id = entity_id.split(".", 1)[-1].replace("_", " ")
        value = str(state or "").lower()

        if "fenetre" in object_id or "window" in object_id:
            if value in {"on", "open", "opened"}:
                return "Parce que la fenêtre est ouverte."
            if value in {"off", "closed"}:
                return "Parce que la fenêtre est fermée."

        if "porte" in object_id or "door" in object_id:
            if value in {"on", "open", "opened"}:
                return "Parce que la porte est ouverte."
            if value in {"off", "closed"}:
                return "Parce que la porte est fermée."

        if "mouvement" in object_id or "motion" in object_id:
            if value in {"on", "detected"}:
                return "Parce qu'un mouvement a été détecté."

        if state is not None:
            return f"Parce que {entity_id} est passé à l'état {state}."
        return f"Parce qu'un changement de {entity_id} a déclenché l'action."

    @staticmethod
    def _numeric_reason(entity_id: str) -> str:
        object_id = entity_id.split(".", 1)[-1].lower()
        if any(word in object_id for word in ("lux", "lumiere", "illuminance")):
            return "Parce que la luminosité a franchi le seuil prévu."
        if "temperature" in object_id:
            return "Parce que la température a franchi le seuil prévu."
        return "Parce qu'une valeur a franchi le seuil prévu."

    @staticmethod
    def _parse_when(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.astimezone(UTC)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _result(
        entity_id: str,
        status: WhyStatus,
        reason: str,
        *,
        source_type: SourceType = "unknown",
        source_entity_id: str | None = None,
        source_name: str | None = None,
        trigger_source: str | None = None,
        action_time: datetime | None = None,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "entity_id": entity_id,
            "status": status,
            "reason": reason,
            "source_type": source_type,
            "source_entity_id": source_entity_id,
            "source_name": source_name,
            "trigger_source": trigger_source,
            "action_time": action_time.isoformat() if action_time else None,
        }
