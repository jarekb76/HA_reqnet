from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ReqnetDataCoordinator

REPLACE_FILTERS = ButtonEntityDescription(
    key="replace_filters",
    translation_key="replace_filters",
    icon="mdi:air-filter",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Reqnet filter replacement button."""
    del hass
    async_add_entities([ReqnetReplaceFiltersButton(config_entry.runtime_data)])


class ReqnetReplaceFiltersButton(
    CoordinatorEntity[ReqnetDataCoordinator], ButtonEntity
):
    """Reset the filter replacement counter."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ReqnetDataCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = REPLACE_FILTERS
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_replace_filters"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Return whether the device is available."""
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Mark the filters as replaced."""
        if not await self.coordinator.async_replace_filters():
            raise HomeAssistantError("Nie udało się zresetować licznika filtrów")