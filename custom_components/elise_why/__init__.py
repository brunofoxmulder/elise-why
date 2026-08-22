"""Élise Why - read-only causal explanations for Home Assistant."""

from __future__ import annotations

from datetime import UTC, datetime
import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_EXPLAIN
from .engine import WhyEngine
from .logbook_provider import HomeAssistantLogbookProvider

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional("at_time"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the response-only service."""
    engine = WhyEngine(HomeAssistantLogbookProvider(hass))

    async def async_explain(call: ServiceCall) -> ServiceResponse:
        """Return a causal explanation without changing Home Assistant."""
        at_time = None
        if raw_at_time := call.data.get("at_time"):
            try:
                at_time = datetime.fromisoformat(raw_at_time.replace("Z", "+00:00"))
            except ValueError as err:
                raise ServiceValidationError("at_time must be ISO-8601") from err
            if at_time.tzinfo is None:
                at_time = at_time.replace(tzinfo=UTC)

        return await engine.explain(
            call.data[ATTR_ENTITY_ID],
            at_time=at_time,
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPLAIN,
        async_explain,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up the config entry; no devices or entities are created."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload the config entry."""
    return True
