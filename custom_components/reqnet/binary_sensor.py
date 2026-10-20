"""Platform for binary_sensor integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ReqnetDataCoordinator

async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry[ReqnetDataCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Reqnet binary sensor platform."""
    del _hass
    coordinator: ReqnetDataCoordinator = config_entry.runtime_data

    binary_sensors = [
        # Indeks 0: Status urządzenia (1 - włączone, 0 - wyłączone)
        ReqnetBinarySensor(
            coordinator,
            0,
            BinarySensorEntityDescription(
                key="device_status",
                translation_key="device_status",
                icon="mdi:power",
            ),
            "Rekuperator - Status urządzenia",
            "mdi:power",
            "mdi:power-off",
        ),
    ]

    async_add_entities(binary_sensors)


class ReqnetBinarySensor(
    CoordinatorEntity[ReqnetDataCoordinator], BinarySensorEntity
):
    """Representation of a Reqnet Binary Sensor."""
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        index: int,
        entity_description: BinarySensorEntityDescription,
        legacy_name: str,
        on_icon: str | None,
        off_icon: str | None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._index = index
        self._on_icon = on_icon
        self._off_icon = off_icon

        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{legacy_name.lower().replace(' ', '_')}"
        self._attr_device_info = coordinator.device_info

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