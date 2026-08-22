"""Narrow read-only adapter over Home Assistant Logbook/Recorder."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.logbook.helpers import (
    async_determine_event_types,
    async_filter_entities,
)
from homeassistant.components.logbook.processor import EventProcessor
from homeassistant.components.recorder import get_instance
from homeassistant.core import HomeAssistant


class HomeAssistantLogbookProvider:
    """Fetch Logbook data without issuing service calls or changing HA state."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get_logbook(
        self,
        *,
        entity_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Return humanized logbook rows for one entity."""
        entity_ids = async_filter_entities(self._hass, [entity_id])
        if not entity_ids:
            return []

        event_types = async_determine_event_types(
            self._hass,
            entity_ids,
            None,
        )
        processor = EventProcessor(
            self._hass,
            event_types,
            entity_ids,
            None,
            None,
            timestamp=True,
            include_entity_name=False,
        )

        rows = await get_instance(self._hass).async_add_executor_job(
            processor.get_events,
            start_time,
            end_time,
        )
        return [self._normalize_row(row) for row in rows if isinstance(row, dict)]

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        """Convert numeric Logbook timestamps to ISO strings for the engine."""
        normalized = dict(row)
        when = normalized.get("when")
        if isinstance(when, (int, float)):
            normalized["when"] = datetime.fromtimestamp(
                when,
                tz=start_tz(),
            ).isoformat()
        return normalized


def start_tz():
    """UTC helper kept isolated for straightforward compatibility tests."""
    from datetime import UTC
    return UTC
