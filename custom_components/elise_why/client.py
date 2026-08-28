"""Read-only client for the local Élise Investigator app."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONFIG_TEST_TIMEOUT_SECONDS,
    INVESTIGATOR_ENTITIES_PATH,
    INVESTIGATOR_PORT,
    INVESTIGATOR_WHY_PATH,
    REQUEST_TIMEOUT_SECONDS,
)
from .transport import investigator_url, validate_investigation_result


class InvestigatorClientError(Exception):
    """Base Investigator client error."""


class InvestigatorAuthenticationError(InvestigatorClientError):
    """Investigator rejected the configured token."""


class InvestigatorUnavailableError(InvestigatorClientError):
    """Investigator could not be reached or Home Assistant was unavailable."""


class InvestigatorRequestError(InvestigatorClientError):
    """Investigator rejected a structured request."""


class InvestigatorResponseError(InvestigatorClientError):
    """Investigator returned an invalid response."""


class InvestigatorClient:
    """Minimal authenticated client for the deterministic Investigator API."""

    def __init__(self, hass: HomeAssistant, *, slug: str, token: str) -> None:
        self._session = async_get_clientsession(hass)
        self._slug = slug
        self._token = token

    def _url(self, path: str) -> str:
        return investigator_url(self._slug, path, port=INVESTIGATOR_PORT)

    @property
    def slug(self) -> str:
        """Return the full installed app slug."""
        return self._slug

    async def async_validate_connection(self) -> None:
        """Validate reachability and bearer authentication without changing HA."""
        try:
            async with self._session.get(
                self._url(INVESTIGATOR_ENTITIES_PATH),
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=ClientTimeout(total=CONFIG_TEST_TIMEOUT_SECONDS),
            ) as response:
                if response.status in (401, 403):
                    raise InvestigatorAuthenticationError(
                        "Élise Investigator refused the API token"
                    )
                if response.status != 200:
                    raise InvestigatorUnavailableError(
                        f"Élise Investigator returned HTTP {response.status}"
                    )
        except InvestigatorClientError:
            raise
        except (ClientError, asyncio.TimeoutError) as err:
            raise InvestigatorUnavailableError(
                "Unable to reach Élise Investigator"
            ) from err

    async def async_investigate(
        self,
        entity_id: str,
        *,
        observed_time: str | None = None,
        observed_value: Any = None,
        attribute: str | None = None,
        user_declaration: str | None = None,
        window_minutes: int | None = None,
    ) -> dict[str, Any]:
        """Ask Investigator's journal-first causal endpoint and return its compact result."""
        data: dict[str, Any] = {"entity_id": entity_id}
        if observed_time is not None:
            data["observed_time"] = observed_time
        if observed_value is not None:
            data["observed_value"] = observed_value
        if attribute is not None:
            data["attribute"] = attribute
        if user_declaration is not None:
            data["user_declaration"] = user_declaration
        if window_minutes is not None:
            data["window_minutes"] = window_minutes

        try:
            async with self._session.post(
                self._url(INVESTIGATOR_WHY_PATH),
                headers={"Authorization": f"Bearer {self._token}"},
                json=data,
                timeout=ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
            ) as response:
                if response.status in (401, 403):
                    raise InvestigatorAuthenticationError(
                        "Élise Investigator refused the API token"
                    )

                try:
                    payload: Any = await response.json(content_type=None)
                except Exception as err:
                    raise InvestigatorResponseError(
                        "Élise Investigator returned invalid JSON"
                    ) from err

                if response.status == 400:
                    detail = (
                        str(payload.get("error") or "invalid structured request")
                        if isinstance(payload, dict)
                        else "invalid structured request"
                    )
                    raise InvestigatorRequestError(detail)
                if response.status == 503:
                    raise InvestigatorUnavailableError(
                        "Élise Investigator cannot currently read Home Assistant"
                    )
                if response.status != 200:
                    raise InvestigatorUnavailableError(
                        f"Élise Investigator returned HTTP {response.status}"
                    )
        except InvestigatorClientError:
            raise
        except (ClientError, asyncio.TimeoutError) as err:
            raise InvestigatorUnavailableError(
                "Unable to reach Élise Investigator"
            ) from err

        try:
            return validate_investigation_result(
                payload, expected_entity_id=entity_id
            )
        except ValueError as err:
            raise InvestigatorResponseError(str(err)) from err
