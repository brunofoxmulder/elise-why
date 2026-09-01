"""Élise Why - read-only LLM facade to Élise Investigator."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.hassio import HassioNotReadyError, get_apps_list
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .client import (
    InvestigatorAuthenticationError,
    InvestigatorClient,
    InvestigatorClientError,
    InvestigatorUnavailableError,
)
from .const import (
    CONF_INVESTIGATOR_SLUG,
    CONF_INVESTIGATOR_TOKEN,
    DATA_CLIENT,
    DOMAIN,
    INVESTIGATOR_SLUG_SUFFIX,
    SERVICE_EXPLAIN,
)
from .transport import find_investigator_slug

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional("at_time"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain; config-entry setup owns the client."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the local Investigator client and compatibility service."""
    token = str(entry.data.get(CONF_INVESTIGATOR_TOKEN) or "").strip()
    if not token:
        raise ConfigEntryAuthFailed("Élise Investigator API token is required")

    try:
        apps = get_apps_list(hass)
    except HassioNotReadyError as err:
        raise ConfigEntryNotReady("Home Assistant Supervisor is not ready") from err

    slug = find_investigator_slug(apps, INVESTIGATOR_SLUG_SUFFIX)
    if slug is None:
        raise ConfigEntryNotReady("Élise Investigator app is not installed")

    if entry.data.get(CONF_INVESTIGATOR_SLUG) != slug:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_INVESTIGATOR_SLUG: slug},
        )

    client = InvestigatorClient(hass, slug=slug, token=token)
    try:
        await client.async_validate_connection()
    except InvestigatorAuthenticationError as err:
        raise ConfigEntryAuthFailed("Élise Investigator rejected the API token") from err
    except InvestigatorUnavailableError as err:
        raise ConfigEntryNotReady("Élise Investigator is not reachable") from err

    hass.data.setdefault(DOMAIN, {})[DATA_CLIENT] = client

    async def async_explain(call: ServiceCall) -> ServiceResponse:
        """Proxy the legacy response-only action to Investigator."""
        observed_time = None
        if raw_at_time := call.data.get("at_time"):
            raw_at_time = str(raw_at_time).strip()
            if not raw_at_time:
                raise ServiceValidationError("at_time must not be empty")
            observed_time = raw_at_time

        try:
            return await client.async_investigate(
                call.data[ATTR_ENTITY_ID], observed_time=observed_time
            )
        except InvestigatorClientError as err:
            raise ServiceValidationError(str(err)) from err

    if not hass.services.has_service(DOMAIN, SERVICE_EXPLAIN):
        hass.services.async_register(
            DOMAIN,
            SERVICE_EXPLAIN,
            async_explain,
            schema=SERVICE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Élise Why without touching Investigator or Home Assistant state."""
    domain_data: dict[str, Any] = hass.data.get(DOMAIN, {})
    domain_data.pop(DATA_CLIENT, None)
    if hass.services.has_service(DOMAIN, SERVICE_EXPLAIN):
        hass.services.async_remove(DOMAIN, SERVICE_EXPLAIN)
    return True
