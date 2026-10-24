"""Numeric config.json settings."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MetarMapConfigEntry
from .entity import MetarMapEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class MetarMapNumberDescription(NumberEntityDescription):
    # device value = HA value * scale
    scale: float = 1.0
    as_int: bool = False


NUMBERS: tuple[MetarMapNumberDescription, ...] = (
    MetarMapNumberDescription(
        key="display_screen.delay",
        translation_key="display_delay",
        icon="mdi:timer-outline",
        native_min_value=0,
        native_max_value=30,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.CONFIG,
    ),
    MetarMapNumberDescription(
        key="visualizer.auto_rotate.delay_seconds",
        translation_key="auto_rotate_delay",
        icon="mdi:timer-sync-outline",
        native_min_value=5,
        native_max_value=3600,
        native_step=1,
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.CONFIG,
        as_int=True,
    ),
    *(
        MetarMapNumberDescription(
            key=f"led.brightness.{level}",
            translation_key=f"brightness_{level}",
            icon="mdi:brightness-6",
            native_min_value=0,
            native_max_value=100,
            native_step=1,
            native_unit_of_measurement=PERCENTAGE,
            entity_category=EntityCategory.CONFIG,
            scale=0.01,
        )
        for level in ("normal", "dimmed", "off")
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MetarMapConfigNumber(coordinator, d)
        for d in NUMBERS
        if d.key in coordinator.data.get("config", {})
    )


class MetarMapConfigNumber(MetarMapEntity, NumberEntity):
    entity_description: MetarMapNumberDescription

    def __init__(self, coordinator, description: MetarMapNumberDescription) -> None:
        super().__init__(coordinator, description.key.replace(".", "_"))
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        value = self.config.get(self.entity_description.key)
        return None if value is None else round(float(value) / self.entity_description.scale, 2)

    async def async_set_native_value(self, value: float) -> None:
        desc = self.entity_description
        device_value = round(value * desc.scale, 2)
        if desc.as_int:
            device_value = int(device_value)
        await self.coordinator.client.edit_config(desc.key, device_value)
        await self.coordinator.async_request_refresh()
