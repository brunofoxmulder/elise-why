"""Config flow for Élise Why."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.hassio import HassioNotReadyError, get_apps_list
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client import (
    InvestigatorAuthenticationError,
    InvestigatorClient,
    InvestigatorUnavailableError,
)
from .const import (
    CONF_INVESTIGATOR_SLUG,
    CONF_INVESTIGATOR_TOKEN,
    CONF_RESPONSE_STYLE,
    CONF_STYLE_PROMPT,
    DOMAIN,
    INVESTIGATOR_SLUG_SUFFIX,
)
from .presentation import (
    DEFAULT_RESPONSE_STYLE,
    MAX_CUSTOM_STYLE_PROMPT_LENGTH,
    RESPONSE_STYLES,
    normalize_custom_style_prompt,
    normalize_response_style,
)
from .transport import find_investigator_slug

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INVESTIGATOR_TOKEN): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
                autocomplete="current-password",
            )
        )
    }
)


class EliseWhyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the single local Élise Why facade."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EliseWhyOptionsFlow:
        """Create the presentation options flow."""
        return EliseWhyOptionsFlow()

    async def _validate_token(
        self, token: str
    ) -> tuple[dict[str, str], dict[str, str] | None]:
        """Find Investigator and validate one token."""
        errors: dict[str, str] = {}
        try:
            apps = get_apps_list(self.hass)
        except HassioNotReadyError:
            return {"base": "supervisor_not_ready"}, None

        slug = find_investigator_slug(apps, INVESTIGATOR_SLUG_SUFFIX)
        if slug is None:
            return {"base": "investigator_not_found"}, None

        client = InvestigatorClient(self.hass, slug=slug, token=token)
        try:
            await client.async_validate_connection()
        except InvestigatorAuthenticationError:
            errors["base"] = "invalid_auth"
        except InvestigatorUnavailableError:
            errors["base"] = "cannot_connect"

        if errors:
            return errors, None
        return {}, {
            CONF_INVESTIGATOR_TOKEN: token,
            CONF_INVESTIGATOR_SLUG: slug,
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Find Investigator and validate the local bearer token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = str(user_input[CONF_INVESTIGATOR_TOKEN]).strip()
            if not token:
                errors["base"] = "invalid_auth"
            else:
                errors, data = await self._validate_token(token)
                if data is not None:
                    await self.async_set_unique_id(DOMAIN)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title="Élise Why", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Request the Investigator token for a legacy or rejected config entry."""
        self._reauth_entry = self._get_reauth_entry()
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Validate and store a replacement Investigator token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = str(user_input[CONF_INVESTIGATOR_TOKEN]).strip()
            if not token:
                errors["base"] = "invalid_auth"
            else:
                errors, data = await self._validate_token(token)
                if data is not None:
                    return self.async_update_reload_and_abort(
                        self._reauth_entry,
                        data=data,
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class EliseWhyOptionsFlow(config_entries.OptionsFlow):
    """Manage response presentation without changing causal behavior."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure response detail and an optional style-only prompt."""
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_custom = str(user_input.get(CONF_STYLE_PROMPT) or "").strip()
            if len(raw_custom) > MAX_CUSTOM_STYLE_PROMPT_LENGTH:
                errors["base"] = "style_prompt_too_long"
            else:
                return self.async_create_entry(
                    data={
                        CONF_RESPONSE_STYLE: normalize_response_style(
                            user_input.get(CONF_RESPONSE_STYLE)
                        ),
                        CONF_STYLE_PROMPT: normalize_custom_style_prompt(raw_custom),
                    }
                )

        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RESPONSE_STYLE,
                    default=current.get(
                        CONF_RESPONSE_STYLE, DEFAULT_RESPONSE_STYLE
                    ),
                ): vol.In(RESPONSE_STYLES),
                vol.Optional(
                    CONF_STYLE_PROMPT,
                    default=current.get(CONF_STYLE_PROMPT, ""),
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
