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
# (display_screen.enabled applies right away on newer maps, with /display; older maps need a restart)
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
    entities: list[SwitchEntity] = [
        MetarMapConfigSwitch(coordinator, d)
        for d in SWITCHES
        if d.key in coordinator.data.get("config", {})
    ]
    if "display" in coordinator.data:  # newer maps: the OLED screen can be turned on and off
        entities.append(MetarMapDisplaySwitch(coordinator))
    async_add_entities(entities)


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


class MetarMapDisplaySwitch(MetarMapEntity, SwitchEntity):
    """The OLED screen on or off now, like the map's Home page switch. Not saved: the screen is on again when the
    map restarts. Unavailable while the screen is turned off in the map's config ("OLED screen enabled")."""

    _attr_translation_key = "display"
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "display")

    @property
    def _display(self) -> dict[str, Any]:
        return self.coordinator.data.get("display") or {}

    @property
    def available(self) -> bool:
        return super().available and bool(self._display.get("enabled"))

    @property
    def is_on(self) -> bool | None:
        return bool(self._display.get("on"))

    async def _set(self, value: bool) -> None:
        await self.coordinator.client.set_display(value)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
