"""Action buttons."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MetarMapClient
from .coordinator import MetarMapConfigEntry
from .entity import MetarMapEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class MetarMapButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[MetarMapClient], Awaitable[object]]


async def _update(client: MetarMapClient) -> None:
    _LOGGER.info("METARMap software update output: %s", await client.update_software())


BUTTONS: tuple[MetarMapButtonDescription, ...] = (
    MetarMapButtonDescription(
        key="visualizer_next",
        translation_key="visualizer_next",
        icon="mdi:skip-next",
        press_fn=lambda c: c.next_visualizer(),
    ),
    MetarMapButtonDescription(
        key="visualizer_previous",
        translation_key="visualizer_previous",
        icon="mdi:skip-previous",
        press_fn=lambda c: c.previous_visualizer(),
    ),
    MetarMapButtonDescription(
        key="fetch",
        translation_key="fetch",
        icon="mdi:cloud-download",
        press_fn=lambda c: c.fetch_metars(),
    ),
    MetarMapButtonDescription(
        key="restart",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda c: c.restart(),
    ),
    MetarMapButtonDescription(
        key="update_software",
        translation_key="update_software",
        device_class=ButtonDeviceClass.UPDATE,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        press_fn=_update,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(MetarMapButton(coordinator, d) for d in BUTTONS)


class MetarMapButton(MetarMapEntity, ButtonEntity):
    entity_description: MetarMapButtonDescription

    def __init__(self, coordinator, description: MetarMapButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await self.entity_description.press_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()
