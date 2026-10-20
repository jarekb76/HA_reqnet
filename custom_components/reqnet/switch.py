"""Switch platform for the Reqnet integration."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ReqnetDataCoordinator

MANUAL_MODE = 8
AUTOMATIC_MODE = 9
MODE_INDEX = 10


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry[ReqnetDataCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Reqnet mode switch."""
    del _hass
    async_add_entities([ReqnetModeSwitch(config_entry.runtime_data)])


class ReqnetModeSwitch(CoordinatorEntity[ReqnetDataCoordinator], SwitchEntity):
    """Switch between automatic and manual operating modes."""

    _attr_has_entity_name = True
    _attr_name = "Tryb ręczny"
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: ReqnetDataCoordinator) -> None:
        """Initialize the mode switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_mode"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Return whether the current mode is known."""
        data = self.coordinator.data
        return (
            self.coordinator.last_update_success
            and isinstance(data, list)
            and len(data) > MODE_INDEX
            and data[MODE_INDEX] in (MANUAL_MODE, AUTOMATIC_MODE)
        )

    @property
    def is_on(self) -> bool:
        """Return whether manual mode is active."""
        data = self.coordinator.data
        return (
            isinstance(data, list)
            and len(data) > MODE_INDEX
            and data[MODE_INDEX] == MANUAL_MODE
        )

    async def async_turn_on(self, **kwargs: object) -> None:
        """Switch the recuperator to manual mode."""
        if not await self.coordinator.async_set_manual_mode():
            raise HomeAssistantError("Nie udało się włączyć trybu ręcznego")

    async def async_turn_off(self, **kwargs: object) -> None:
        """Switch the recuperator to automatic mode."""
        if not await self.coordinator.async_set_automatic_mode():
            raise HomeAssistantError("Nie udało się włączyć trybu automatycznego")