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
    @property
    def options(self) -> list[str]:
        return self.coordinator.visualizer_names

    def _index(self, option: str) -> int:
        return self.options.index(option)

    def _name(self, index: int | None) -> str | None:
        names = self.options
        return names[index] if index is not None and 0 <= index < len(names) else None


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
        return self._name(self.coordinator.data.get("visualizer", {}).get("active"))

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
        await self.coordinator.client.set_visualizer(self._index(option))
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
        await self.coordinator.client.edit_config("visualizer.active", self._index(option))
        await self.coordinator.async_request_refresh()
