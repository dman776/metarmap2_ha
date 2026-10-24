"""LED brightness as a light entity, plus the locate service."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_AIRPORT, ATTR_PIXEL, SERVICE_LOCATE
from .coordinator import MetarMapConfigEntry
from .entity import MetarMapEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MetarMapLight(entry.runtime_data)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_LOCATE,
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Exclusive(ATTR_AIRPORT, "target"): cv.string,
                    vol.Exclusive(ATTR_PIXEL, "target"): vol.All(
                        vol.Coerce(int), vol.Range(min=0)
                    ),
                }
            ),
            cv.has_at_least_one_key(ATTR_AIRPORT, ATTR_PIXEL),
        ),
        "async_locate",
    )


class MetarMapLight(MetarMapEntity, LightEntity):
    """The map's LED strip. Brightness only; colours belong to the visualizer."""

    _attr_translation_key = "leds"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "leds")
        self._last_level: float | None = None

    @property
    def _level(self) -> float:
        return float(self.coordinator.data.get("brightness", 0))

    @property
    def is_on(self) -> bool:
        return self._level > 0

    @property
    def brightness(self) -> int:
        return round(self._level * 255)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            level = kwargs[ATTR_BRIGHTNESS] / 255
        elif self.is_on:
            return
        else:
            level = self._last_level or self.config.get("led.brightness.normal", 0.5)
        await self.coordinator.client.set_brightness(level)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.is_on:
            self._last_level = self._level
        await self.coordinator.client.set_brightness(0)
        await self.coordinator.async_request_refresh()

    async def async_locate(self, airport: str | None = None, pixel: int | None = None) -> None:
        if airport is not None:
            info = self.coordinator.airport(airport.upper())
            if info is None:
                raise ServiceValidationError(f"Unknown airport {airport}")
            pixel = info["pixel"]
        await self.coordinator.client.locate(pixel)
