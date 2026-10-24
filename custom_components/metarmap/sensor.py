"""Sensors for METARMap."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import FLIGHT_CATEGORIES
from .coordinator import MetarMapConfigEntry, MetarMapCoordinator
from .entity import MetarMapEntity

PARALLEL_UPDATES = 0


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is not None and parsed.tzinfo is None:
        # the map reports lastFetchTime in its local time; assume it matches HA's
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed


def _category_count(category: str) -> Callable[[dict[str, Any]], int]:
    return lambda data: sum(
        1 for a in data.get("airports", []) if a.get("flightCategory") == category
    )


@dataclass(frozen=True, kw_only=True)
class MetarMapSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[MetarMapSensorDescription, ...] = (
    *(
        MetarMapSensorDescription(
            key=f"airports_{cat.lower()}",
            translation_key=f"airports_{cat.lower()}",
            icon="mdi:airplane",
            native_unit_of_measurement="airports",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=_category_count(cat),
        )
        for cat in FLIGHT_CATEGORIES
    ),
    MetarMapSensorDescription(
        key="last_fetch",
        translation_key="last_fetch",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _parse_dt(d.get("lastFetchTime")),
    ),
    MetarMapSensorDescription(
        key="missing_stations",
        translation_key="missing_stations",
        icon="mdi:map-marker-question",
        native_unit_of_measurement="airports",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: len(d.get("missingStations", [])),
        attrs_fn=lambda d: {"stations": d.get("missingStations", [])},
    ),
    *(
        MetarMapSensorDescription(
            key=f"sun_{phase}",
            translation_key=f"sun_{phase}",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=lambda d, p=phase: _parse_dt(d.get("suntimes", {}).get(p)),
        )
        for phase in ("dawn", "sunrise", "sunset", "dusk")
    ),
)

AIRPORT_ATTRS = {
    "raw": "raw_metar",
    "windDir": "wind_direction",
    "windSpeed": "wind_speed_kt",
    "windGustSpeed": "wind_gust_kt",
    "vis": "visibility_sm",
    "obs": "weather",
    "tempC": "temperature_c",
    "dewpointC": "dewpoint_c",
    "altimHg": "altimeter_inhg",
    "lightning": "lightning",
    "obsTime": "observation_time",
    "pixel": "pixel",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [MetarMapSensor(coordinator, d) for d in SENSORS]
    entities.extend(
        AirportSensor(coordinator, a["code"]) for a in coordinator.data.get("airports", [])
    )
    async_add_entities(entities)


class MetarMapSensor(MetarMapEntity, SensorEntity):
    entity_description: MetarMapSensorDescription

    def __init__(self, coordinator, description: MetarMapSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)


class AirportSensor(MetarMapEntity, SensorEntity):
    """Flight category of one airport on the map. Disabled by default (maps have many)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [*FLIGHT_CATEGORIES, "UNKNOWN"]
    _attr_translation_key = "airport"
    _attr_icon = "mdi:airport"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: MetarMapCoordinator, code: str) -> None:
        super().__init__(coordinator, f"airport_{code.lower()}")
        self._code = code
        self._attr_translation_placeholders = {"code": code}

    @property
    def _info(self) -> dict[str, Any]:
        return self.coordinator.airport(self._code) or {}

    @property
    def native_value(self) -> str:
        cat = self._info.get("flightCategory")
        return cat if cat in FLIGHT_CATEGORIES else "UNKNOWN"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = self._info
        return {name: info.get(src) for src, name in AIRPORT_ATTRS.items()}
