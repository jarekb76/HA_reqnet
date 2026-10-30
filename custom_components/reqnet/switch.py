from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ReqnetDataCoordinator

DEVICE_POWER = SwitchEntityDescription(
    key="device_power",
    translation_key="device_power",
    icon="mdi:power",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Reqnet power switch."""
    del hass
    async_add_entities([ReqnetPowerSwitch(config_entry.runtime_data)])


class ReqnetPowerSwitch(CoordinatorEntity[ReqnetDataCoordinator], SwitchEntity):
    """Control the recuperator power state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ReqnetDataCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = DEVICE_POWER
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_device_power"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Return whether the device status is available."""
        return (
            self.coordinator.last_update_success
            and isinstance(self.coordinator.data, list)
            and len(self.coordinator.data) > 0
        )

    @property
    def is_on(self) -> bool:
        """Return the power state reported by the device."""
        data = self.coordinator.data
        return isinstance(data, list) and bool(data) and data[0] == 1

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the recuperator on."""
        if not await self.coordinator.async_set_device_power(True):
            raise HomeAssistantError("Nie udało się włączyć rekuperatora")

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the recuperator off."""
        if not await self.coordinator.async_set_device_power(False):
            raise HomeAssistantError("Nie udało się wyłączyć rekuperatora")