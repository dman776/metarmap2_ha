"""Visualizer selects."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MetarMapConfigEntry
from .entity import MetarMapEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetarMapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [ActiveVisualizerSelect(coordinator), DefaultVisualizerSelect(coordinator)]
    )


class _VisualizerSelect(MetarMapEntity, SelectEntity):
    """
    Newer maps give each visualizer an id, which never changes, and save visualizer.active as it; older
    ones only have the visualizer's number. Both are sent the way the map knows them.
    """

    @property
    def options(self) -> list[str]:
        return self.coordinator.visualizer_names

    def _key(self, option: str) -> str | int:
        """The id (or, on an older map, the number) of the visualizer named `option`."""
        number = self.options.index(option)
        vis = self.coordinator.data.get("visualizers", [])[number]
        return vis.get("id", vis.get("index", number))

    def _name(self, key: str | int | None) -> str | None:
        """The name of the visualizer with id or number `key`."""
        if key is None:
            return None
        for number, vis in enumerate(self.coordinator.data.get("visualizers", [])):
            if key == vis.get("id") or (isinstance(key, int) and key == vis.get("index", number)):
                return vis["name"]
        return None


class ActiveVisualizerSelect(_VisualizerSelect):
    """Currently running visualizer (not persisted)."""

    _attr_translation_key = "visualizer"
    _attr_icon = "mdi:palette"
    # static per visualizer; no need to store them in the recorder on every change
    _unrecorded_attributes = frozenset({"description", "legend"})

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "visualizer")

    @property
    def current_option(self) -> str | None:
        vis = self.coordinator.data.get("visualizer", {})
        return self._name(vis.get("id", vis.get("active")))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Exclusive flag, plus the description and LED legend (map 2.1+)."""
        vis = self.coordinator.data.get("visualizer", {})
        attrs: dict[str, Any] = {"exclusive": vis.get("exclusive", False)}
        for key in ("description", "legend"):
            if key in vis:
                attrs[key] = vis[key]
        return attrs

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_visualizer(self._key(option))
        await self.coordinator.async_request_refresh()


class DefaultVisualizerSelect(_VisualizerSelect):
    """Visualizer used at startup (config.json visualizer.active)."""

    _attr_translation_key = "default_visualizer"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:palette-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "default_visualizer")

    @property
    def current_option(self) -> str | None:
        return self._name(self.config.get("visualizer.active"))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.edit_config("visualizer.active", self._key(option))
        await self.coordinator.async_request_refresh()
