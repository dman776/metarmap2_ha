"""Boolean config.json settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MetarMapConfigEntry
from .entity import MetarMapEntity

PARALLEL_UPDATES = 1

# key == config.json path; settings marked "restart" only apply after a restart
SWITCHES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="lightning.animation",
        translation_key="lightning_animation",
        icon="mdi:weather-lightning",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="display_screen.locate_active",
        translation_key="display_locate_active",
        icon="mdi:map-marker-radius",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="display_screen.enabled",
        translation_key="display_enabled",
        icon="mdi:monitor",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="visualizer.auto_rotate.enabled",
        translation_key="auto_rotate",
        icon="mdi:rotate-right",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="led.inittest",
        translation_key="led_inittest",
        icon="mdi:led-strip-variant",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MetarMapConfigSwitch(coordinator, d)
        for d in SWITCHES
        if d.key in coordinator.data.get("config", {})
    )


class MetarMapConfigSwitch(MetarMapEntity, SwitchEntity):
    def __init__(self, coordinator, description: SwitchEntityDescription) -> None:
        super().__init__(coordinator, description.key.replace(".", "_"))
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self.config.get(self.entity_description.key)
        return None if value is None else bool(value)

    async def _set(self, value: bool) -> None:
        await self.coordinator.client.edit_config(self.entity_description.key, value)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
