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

# Definicja przycisku
BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="automatic_mode", # Unikalny klucz dla tego przycisku
    name="Włącz tryb inteligentny",
    icon="mdi:brain-outline", # Możesz wybrać inną ikonę, np. mdi:auto-fix
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

    _attr_has_entity_name = True # Automatycznie tworzy nazwę encji

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Inicjalizacja przycisku."""
        # Przekazanie koordynatora do bazowej klasy CoordinatorEntity
        # jest ważne dla poprawnego powiązania z urządzeniem w HA (device_info)
        super().__init__(coordinator)
        self.entity_description = description
        # Tworzenie unikalnego ID dla encji
        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{description.key}"
        
        # Informacje o urządzeniu są dziedziczone z CoordinatorEntity,
        # jeśli encja jest z nim poprawnie powiązana.

    async def async_press(self) -> None:
        """Obsługa naciśnięcia przycisku."""
        _LOGGER.info(f"Przycisk '{self.entity_description.name}' został naciśnięty. Wywoływanie API...")
        
        success = await self.coordinator.async_set_automatic_mode() # Wywołanie metody z koordynatora

        if success:
            _LOGGER.info("Wywołanie API trybu automatycznego zakończone sukcesem.")
        else:
            _LOGGER.error("Wywołanie API trybu automatycznego nie powiodło się.")
        
        # Po naciśnięciu przycisku, sensor "Tryb pracy" (API Index 11 / Python index 10)
        # powinien się zaktualizować do "Tryb inteligentny" (wartość 9) po odświeżeniu koordynatora.
        # Metoda async_set_automatic_mode w koordynatorze już wywołuje async_request_refresh().