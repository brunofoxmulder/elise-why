"""LLM tools contributed by Élise Why."""

from __future__ import annotations

from typing import Any, override

import voluptuous as vol

from homeassistant.components.homeassistant import async_should_expose
from homeassistant.components.llm import LLMTools
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.helpers.llm import LLM_API_ASSIST, LLMContext, Tool, ToolInput
from homeassistant.util.json import JsonObjectType

from .client import InvestigatorClient, InvestigatorClientError
from .const import (
    CONF_RESPONSE_STYLE,
    CONF_STYLE_PROMPT,
    DATA_CLIENT,
    DOMAIN,
    MAX_LLM_TARGETS,
)
from .presentation import DEFAULT_RESPONSE_STYLE, build_prompt


class InvestigateWhyTool(Tool):
    """Resolve exposed HA targets, then ask deterministic Investigator."""

    name = "InvestigateWhy"
    description = (
        "Get read-only causal evidence from Élise Investigator for one or more "
        "Home Assistant entities. Use this only for causal 'why' questions, never "
        "for commands or device control. Use entity_id when known; otherwise "
        "resolve by name/domain/area. Set all_matches=true for explicit plural requests."
    )
    parameters = vol.Schema(
        {
            vol.Optional("entity_id", description="Exact Home Assistant entity_id."): cv.entity_id,
            vol.Optional("name", description="Entity name or alias to resolve."): cv.string,
            vol.Optional("domain", description="Home Assistant domain such as cover, light or climate."): cv.string,
            vol.Optional("area", description="Home Assistant area name or alias."): cv.string,
            vol.Optional(
                "all_matches",
                default=False,
                description=(
                    "True when the user explicitly asks about several/all matching "
                    "entities, including natural plural wording."
                ),
            ): cv.boolean,
            vol.Optional("observed_time", description="Observed ISO-8601 date/time when the user specifies one."): cv.string,
            vol.Optional("observed_value", description="Observed state or attribute value when explicitly relevant."): vol.Any(str, int, float, bool),
            vol.Optional("attribute", description="Attribute name when observed_value refers to an attribute."): cv.string,
            vol.Optional("window_minutes", description="Investigator lookback window, from 5 to 180 minutes."): vol.All(
                vol.Coerce(int), vol.Range(min=5, max=180)
            ),
        }
    )

    @override
    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> JsonObjectType:
        """Resolve targets using Home Assistant and return raw Investigator proofs."""
        args = self.parameters(tool_input.tool_args)
        client = _get_client(hass)
        if client is None:
            return {"success": False, "error": "Élise Why is not configured or loaded"}

        entity_ids = _resolve_targets(hass, llm_context, args)
        if isinstance(entity_ids, str):
            return {"success": False, "error": entity_ids}

        results: list[dict[str, Any]] = []
        for entity_id in entity_ids:
            try:
                result = await client.async_investigate(
                    entity_id,
                    observed_time=args.get("observed_time"),
                    observed_value=args.get("observed_value"),
                    attribute=args.get("attribute"),
                    window_minutes=args.get("window_minutes"),
                )
            except InvestigatorClientError as err:
                return {
                    "success": False,
                    "error": str(err),
                    "failed_entity_id": entity_id,
                    "results": results,
                }
            results.append(result)

        return {"success": True, "count": len(results), "results": results}


def _get_client(hass: HomeAssistant) -> InvestigatorClient | None:
    data = hass.data.get(DOMAIN)
    if not isinstance(data, dict):
        return None
    client = data.get(DATA_CLIENT)
    return client if isinstance(client, InvestigatorClient) else None


def _get_prompt(hass: HomeAssistant) -> str:
    """Build the presentation prompt from current config-entry options."""
    entries = hass.config_entries.async_entries(DOMAIN)
    options = entries[0].options if entries else {}
    return build_prompt(
        options.get(CONF_RESPONSE_STYLE, DEFAULT_RESPONSE_STYLE),
        options.get(CONF_STYLE_PROMPT, ""),
    )


def _resolve_targets(
    hass: HomeAssistant, llm_context: LLMContext, args: dict[str, Any]
) -> list[str] | str:
    """Resolve only entities exposed to this assistant; never guess ambiguity."""
    exact_entity_id = args.get("entity_id")
    exposed_states = [
        state
        for state in hass.states.async_all()
        if async_should_expose(hass, llm_context.assistant, state.entity_id)
    ]
    exposed_ids = {state.entity_id for state in exposed_states}

    if exact_entity_id:
        if exact_entity_id not in exposed_ids:
            return f"Entity {exact_entity_id} is not exposed to this assistant"
        return [exact_entity_id]

    name = args.get("name")
    domain = args.get("domain")
    area = args.get("area")
    if not any((name, domain, area)):
        return "Provide entity_id or at least one of name, domain, area"

    domains = [str(domain).strip().lower()] if domain else None
    match_result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            name=name,
            area_name=area,
            domains=domains,
            allow_duplicate_names=True,
        ),
        states=exposed_states,
    )
    if not match_result.is_match:
        return "No exposed Home Assistant entity matches the requested target"

    entity_ids = sorted({state.entity_id for state in match_result.states})
    if not args["all_matches"] and len(entity_ids) != 1:
        candidates = ", ".join(entity_ids[:MAX_LLM_TARGETS])
        return f"Target is ambiguous; matching entities: {candidates}"

    if len(entity_ids) > MAX_LLM_TARGETS:
        return (
            f"Too many matching entities ({len(entity_ids)}); narrow the target by name or area"
        )

    return entity_ids


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> LLMTools | None:
    """Expose one causal tool to the built-in Assist LLM API."""
    if api_id != LLM_API_ASSIST or _get_client(hass) is None:
        return None
    return LLMTools(tools=[InvestigateWhyTool()], prompt=_get_prompt(hass))
