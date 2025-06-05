# /config/custom_components/reqnet/button.py
from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReqnetDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Definicje przycisków
BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="automatic_mode",
        name="Reqnet Włącz tryb inteligentny",
        icon="mdi:brain",
    ),
    ButtonEntityDescription(
        key="manual_mode",
        name="Reqnet Włącz tryb ręczny",
        icon="mdi:hand-back-right",
    ),
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja platformy przycisków Reqnet."""
    coordinator: ReqnetDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    buttons = []
    for description in BUTTON_DESCRIPTIONS:
        if description.key == "automatic_mode":
            buttons.append(ReqnetAutomaticModeButton(coordinator, description))
        elif description.key == "manual_mode":
            buttons.append(ReqnetManualModeButton(coordinator, description))
    
    async_add_entities(buttons)


class ReqnetAutomaticModeButton(CoordinatorEntity[ReqnetDataCoordinator], ButtonEntity):
    """Reprezentacja przycisku Reqnet do włączania trybu automatycznego."""

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Inicjalizacja przycisku."""
        super().__init__(coordinator)
        self.entity_description = description
        
        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{description.key}"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator",
        }

    @property
    def available(self) -> bool:
        """Sprawdź czy przycisk jest dostępny."""
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku."""
        _LOGGER.info(f"Przycisk '{self.entity_description.name}' został naciśnięty. Wywoływanie API AutomaticMode przez MQTT...")
        
        try:
            success = await self.coordinator.async_set_automatic_mode()

            if success:
                _LOGGER.info("Wywołanie API trybu automatycznego (AutomaticMode) zakończone sukcesem.")
                self.hass.bus.fire("reqnet_automatic_mode_activated", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Tryb inteligentny został włączony"
                })
            else:
                _LOGGER.error("Wywołanie API trybu automatycznego (AutomaticMode) nie powiodło się.")
                self.hass.bus.fire("reqnet_automatic_mode_failed", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Nie udało się włączyć trybu inteligentnego"
                })
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas wywoływania AutomaticMode: {e}")


class ReqnetManualModeButton(CoordinatorEntity[ReqnetDataCoordinator], ButtonEntity):
    """Reprezentacja przycisku Reqnet do włączania trybu ręcznego."""

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Inicjalizacja przycisku."""
        super().__init__(coordinator)
        self.entity_description = description
        
        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{description.key}"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator",
        }

    @property
    def available(self) -> bool:
        """Sprawdź czy przycisk jest dostępny."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict:
        """Zwraca dodatkowe atrybuty stanu."""
        attributes = {}
        
        # Dodaj aktualne wartości jako atrybuty
        if self.coordinator.data and len(self.coordinator.data) > 6:
            attributes["current_airflow_manual"] = self.coordinator.data[5]  # API Index 6
            attributes["current_extraction_manual"] = self.coordinator.data[6]  # API Index 7
            attributes["current_airflow_actual"] = self.coordinator.data[3]  # API Index 4
            attributes["current_extraction_actual"] = self.coordinator.data[4]  # API Index 5
        
        attributes["info"] = "Użyj service reqnet.set_manual_mode z parametrami airflow_value i air_extraction_value"
        
        return attributes

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku - użyje aktualnych wartości ręcznych."""
        _LOGGER.info(f"Przycisk '{self.entity_description.name}' został naciśnięty. Wywoływanie API ManualMode przez MQTT...")
        
        try:
            # Użyj aktualnych wartości trybu ręcznego z API (Index 6 i 7)
            success = await self.coordinator.async_set_manual_mode()

            if success:
                _LOGGER.info("Wywołanie API trybu ręcznego (ManualMode) zakończone sukcesem.")
                self.hass.bus.fire("reqnet_manual_mode_activated", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Tryb ręczny został włączony"
                })
            else:
                _LOGGER.error("Wywołanie API trybu ręcznego (ManualMode) nie powiodło się.")
                self.hass.bus.fire("reqnet_manual_mode_failed", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Nie udało się włączyć trybu ręcznego"
                })
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas wywoływania ManualMode: {e}")