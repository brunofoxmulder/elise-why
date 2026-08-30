"""LLM tools contributed by Élise Why to Home Assistant Assist."""

from __future__ import annotations

from typing import override

import aiohttp
import voluptuous as vol

from homeassistant.components.llm import LLMTools
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.llm import LLM_API_ASSIST, LLMContext, Tool, ToolInput
from homeassistant.util.json import JsonObjectType

THERMAL_ANALYSIS_URL = "http://127.0.0.1:8099/analyse/natural"


class ThermalAnalysisTool(Tool):
    """Run a deterministic thermal analysis in the local HAOS app."""

    name = "AnalyseThermique"
    description = (
        "Analyse thermiquement une période à partir du moteur déterministe local. "
        "Utilise cet outil pour les demandes comme 'analyse thermique d'hier', "
        "'de la semaine dernière' ou 'compare hier avec avant-hier'."
    )
    parameters = vol.Schema(
        {
            vol.Required("period"): str,
            vol.Optional("compare"): vol.In(
                ["previous_period", "j-1", "s-1", "m-1"]
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
        """Call the local read-only thermal analysis app."""
        request_body: dict[str, str] = {"period": tool_input.tool_args["period"]}
        if compare := tool_input.tool_args.get("compare"):
            request_body["compare"] = compare

        session = async_get_clientsession(hass)
        try:
            async with session.post(
                THERMAL_ANALYSIS_URL,
                json=request_body,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    detail = payload.get("detail") if isinstance(payload, dict) else None
                    raise HomeAssistantError(
                        f"Analyse thermique indisponible: {detail or response.status}"
                    )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(
                "Impossible de joindre l'app locale Maison Élise — Analyse thermique"
            ) from err

        if not isinstance(payload, dict) or not isinstance(payload.get("llm_input"), dict):
            raise HomeAssistantError("Réponse thermique locale invalide")

        # Ne jamais exposer les données brutes au LLM. Le moteur prépare déjà
        # un contrat borné contenant uniquement les faits déterministes autorisés.
        return {
            "period_request": payload.get("period_request", {}),
            "thermal_analysis": payload["llm_input"],
        }


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> LLMTools | None:
    """Expose the thermal tool only on the built-in Assist LLM API."""
    if api_id != LLM_API_ASSIST:
        return None

    return LLMTools(
        tools=[ThermalAnalysisTool()],
        prompt=(
            "Pour toute demande d'analyse thermique passée ou comparative, utilise "
            "AnalyseThermique. Pour comparer hier à avant-hier, appelle period='hier' "
            "avec compare='j-1'. Pour comparer une semaine à la précédente, utilise "
            "compare='s-1'. Formule ensuite uniquement à partir de thermal_analysis; "
            "ne recalcule rien et n'invente aucune causalité."
        ),
    )
