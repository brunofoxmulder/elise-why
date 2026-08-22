"""Config flow for Élise Why."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class EliseWhyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single local Élise Why config entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create Élise Why after the user explicitly adds the integration."""
        return self.async_create_entry(title="Élise Why", data={})
