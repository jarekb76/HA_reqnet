from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReqnetDataCoordinator

_LOGGER = logging.getLogger(__name__)

WORK_MODE = SelectEntityDescription(
    key="work_mode",
    translation_key="work_mode",
    icon="mdi:cog-outline",
)
BYPASS_MODE = SelectEntityDescription(
    key="bypass_mode",
    translation_key="bypass_mode",
    icon="mdi:valve",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Reqnet work mode selector."""
    coordinator = config_entry.runtime_data
    async_add_entities([
        ReqnetWorkModeSelect(coordinator),
        ReqnetBypassModeSelect(coordinator),
    ])


class ReqnetWorkModeSelect(
    CoordinatorEntity[ReqnetDataCoordinator], SelectEntity
):
    """Select the intelligent or manual work mode."""

    _attr_has_entity_name = True
    _attr_options = ["intelligent", "manual"]

    def __init__(self, coordinator: ReqnetDataCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = WORK_MODE
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_work_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator",
        }

    @property
    def available(self) -> bool:
        """Return whether the device is available."""
        return self.coordinator.last_update_success

    @property
    def current_option(self) -> str | None:
        """Return the work mode reported by the device."""
        data = self.coordinator.data
        if not isinstance(data, list) or len(data) <= 10:
            return None

        return {8: "manual", 9: "intelligent"}.get(data[10])

    async def async_select_option(self, option: str) -> None:
        """Send the selected work mode to the device."""
        if option == "intelligent":
            success = await self.coordinator.async_set_automatic_mode()
            event = "reqnet_automatic_mode"
            mode_name = "inteligentny"
        else:
            success = await self.coordinator.async_set_manual_mode()
            event = "reqnet_manual_mode"
            mode_name = "manualny"

        result = "activated" if success else "failed"
        message = (
            f"Tryb {mode_name} został włączony"
            if success
            else f"Nie udało się włączyć trybu {mode_name}"
        )
        self.hass.bus.fire(f"{event}_{result}", {
            "device_id": self.coordinator.mac_address,
            "message": message,
        })
        if success:
            _LOGGER.info("Włączono tryb %s", mode_name)
        else:
            _LOGGER.error("Nie udało się włączyć trybu %s", mode_name)


class ReqnetBypassModeSelect(
    CoordinatorEntity[ReqnetDataCoordinator], SelectEntity
):
    """Select the bypass operating mode."""

    _attr_has_entity_name = True
    _attr_options = ["closed", "open", "automatic"]

    def __init__(self, coordinator: ReqnetDataCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = BYPASS_MODE
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_bypass_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator",
        }

    @property
    def available(self) -> bool:
        """Return whether the device is available."""
        return self.coordinator.last_update_success

    @property
    def current_option(self) -> str | None:
        """Return the bypass mode reported by the device."""
        data = self.coordinator.data
        if not isinstance(data, list) or len(data) <= 39:
            return None

        return {0: "closed", 1: "open", 2: "automatic", 3: "automatic"}.get(
            data[39]
        )

    async def async_select_option(self, option: str) -> None:
        """Send the selected bypass mode to the device."""
        mode = {"closed": 0, "open": 1, "automatic": 2}[option]
        success = await self.coordinator.async_set_bypass_mode(mode)
        if success:
            _LOGGER.info("Ustawiono tryb bypassu: %s", option)
        else:
            _LOGGER.error("Nie udało się ustawić trybu bypassu: %s", option)