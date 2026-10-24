"""Data update coordinator for METARMap."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MetarMapAuthError, MetarMapClient, MetarMapError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type MetarMapConfigEntry = ConfigEntry[MetarMapCoordinator]


class MetarMapCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /api/status."""

    config_entry: MetarMapConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: MetarMapConfigEntry, client: MetarMapClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_status()
        except MetarMapAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except MetarMapError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def visualizer_names(self) -> list[str]:
        return [v["name"] for v in self.data.get("visualizers", [])]

    def airport(self, code: str) -> dict[str, Any] | None:
        return next((a for a in self.data.get("airports", []) if a["code"] == code), None)
