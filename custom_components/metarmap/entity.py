"""Base entity for METARMap."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import MetarMapCoordinator


class MetarMapEntity(CoordinatorEntity[MetarMapCoordinator]):
    """Common device info / naming."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MetarMapCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="METARMap",
            manufacturer=MANUFACTURER,
            model="METAR Map",
            sw_version=coordinator.data.get("version"),
            configuration_url=f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}/",
        )

    @property
    def config(self) -> dict:
        return self.coordinator.data.get("config", {})
