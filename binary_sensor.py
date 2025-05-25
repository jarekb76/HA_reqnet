"""Platform for binary_sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReqnetDataCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Reqnet binary sensor platform."""
    coordinator: ReqnetDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    binary_sensors = [
        # Indeks 0: Status urządzenia (1 - włączone, 0 - wyłączone)
        ReqnetBinarySensor(coordinator, 0, "Rekuperator - Status urządzenia", "mdi:power", "mdi:power-off"),
    ]

    async_add_entities(binary_sensors)


class ReqnetBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Reqnet Binary Sensor."""

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        index: int,
        name: str,
        on_icon: str | None,
        off_icon: str | None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._index = index
        self._name = name
        self._on_icon = on_icon
        self._off_icon = off_icon

        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{name.lower().replace(' ', '_')}"
        self._attr_name = name

        # Powiąż encję z urządzeniem (rekuperatorem)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator (WiFi v113)",
            "via_device": (DOMAIN, coordinator.mac_address),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None or self._index >= len(self.coordinator.data):
            return None
        # Zakładamy, że 1 to True (on), a 0 to False (off)
        return bool(self.coordinator.data[self._index])

    @property
    def icon(self):
        """Return the icon of the binary sensor."""
        if self.is_on:
            return self._on_icon
        return self._off_icon