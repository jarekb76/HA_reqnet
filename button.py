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
from homeassistant.helpers.update_coordinator import CoordinatorEntity # Dla powiązania z urządzeniem

from .const import DOMAIN # Upewnij się, że DOMAIN jest zdefiniowane w const.py
from .coordinator import ReqnetDataCoordinator # Importuj swój koordynator

_LOGGER = logging.getLogger(__name__)

# Definicja przycisku - ZMIANA: dodanie przedrostka do nazwy
BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="automatic_mode", # Unikalny klucz dla tego przycisku
    name="Reqnet Włącz tryb inteligentny",  # KLUCZOWA ZMIANA: dodany przedrostek "Reqnet"
    icon="mdi:brain", # Zmieniona ikona na bardziej odpowiednią
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja platformy przycisków Reqnet."""
    coordinator: ReqnetDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([
        ReqnetAutomaticModeButton(coordinator, BUTTON_DESCRIPTION)
    ])


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
        
        # Tworzenie unikalnego ID dla encji
        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{description.key}"
        
        # OPCJONALNE: Można także bezpośrednio ustawić nazwę
        # self._attr_name = "Reqnet Włącz tryb inteligentny"
        
        # Informacje o urządzeniu - powiązanie z tym samym urządzeniem co sensory
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator",
        }

    @property
    def available(self) -> bool:
        """Sprawdź czy przycisk jest dostępny."""
        # Przycisk jest dostępny jeśli koordynator jest dostępny
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku."""
        _LOGGER.info(f"Przycisk '{self.entity_description.name}' został naciśnięty. Wywoływanie API AutomaticMode przez MQTT...")
        
        try:
            success = await self.coordinator.async_set_automatic_mode()

            if success:
                _LOGGER.info("Wywołanie API trybu automatycznego (AutomaticMode) zakończone sukcesem.")
                # Opcjonalnie można pokazać powiadomienie w HA
                self.hass.bus.fire("reqnet_automatic_mode_activated", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Tryb inteligentny został włączony"
                })
            else:
                _LOGGER.error("Wywołanie API trybu automatycznego (AutomaticMode) nie powiodło się.")
                # Opcjonalnie można pokazać błąd w HA
                self.hass.bus.fire("reqnet_automatic_mode_failed", {
                    "device_id": self.coordinator.mac_address,
                    "message": "Nie udało się włączyć trybu inteligentnego"
                })
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas wywoływania AutomaticMode: {e}")
        
        # Po naciśnięciu przycisku, sensor "Tryb pracy" (API Index 11 / Python index 10)
        # powinien się zaktualizować do "Tryb inteligentny" (wartość 9) po odświeżeniu koordynatora.
        # Metoda async_set_automatic_mode w koordynatorze już wywołuje async_request_refresh().