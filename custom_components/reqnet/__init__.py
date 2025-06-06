# /config/custom_components/reqnet/__init__.py
"""The Reqnet Recuperator integration."""
import asyncio
import logging
import json
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_MAC, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import ReqnetDataCoordinator

# Dodaj tę linię po imporcie const.py, około linii 17-18:

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]

# Definicja schematu dla serwisu
SERVICE_SET_MANUAL_MODE_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Required("airflow_value"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
    vol.Required("air_extraction_value"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Reqnet Recuperator from a configuration entry."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Reqnet Recuperator from a config entry."""
    _LOGGER.debug("Setting up Reqnet integration from config entry")

    mac_address = entry.data.get(CONF_MAC)
    host = entry.data.get(CONF_HOST)

    if not mac_address:
        _LOGGER.error("MAC address not found in config entry data.")
        raise ConfigEntryNotReady("MAC address is missing.")
    
    if not host:
        _LOGGER.warning("Host not found in config entry data, may affect some functionalities if HTTP is used elsewhere.")

    coordinator = ReqnetDataCoordinator(hass, mac_address) 
    
    try:
        await coordinator.async_config_entry_first_refresh() 
    except Exception as ex:
        _LOGGER.error(f"Failed to fetch initial data for Reqnet device {mac_address} (Host: {host}): {ex}")
        raise ConfigEntryNotReady(f"Failed to connect to Reqnet device: {ex}") from ex

    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.info("INIT.PY: Przed wywołaniem async_forward_entry_setups dla platform: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("INIT.PY: Po wywołaniu async_forward_entry_setups")

    # Rejestracja serwisu
    async def async_set_manual_mode_service(call: ServiceCall) -> None:
        """Obsługa serwisu ustawiania trybu ręcznego."""
        device_id = call.data["device_id"]
        airflow_value = call.data["airflow_value"]
        air_extraction_value = call.data["air_extraction_value"]
        
        _LOGGER.info(f"Serwis set_manual_mode wywołany dla urządzenia {device_id} z wartościami: nawiew={airflow_value}, wyciąg={air_extraction_value}")
        
        # Znajdź odpowiedni koordynator
        target_coordinator = None
        for entry_id, coord in hass.data[DOMAIN].items():
            if isinstance(coord, ReqnetDataCoordinator):
                # Porównaj MAC address (bez dwukropków, uppercase)
                if coord.mac_address == device_id.replace(":", "").upper():
                    target_coordinator = coord
                    break
                # Porównaj też z oryginalnym formatem
                elif coord.mac_for_mqtt_topics == device_id.upper():
                    target_coordinator = coord
                    break
        
        if not target_coordinator:
            _LOGGER.error(f"Nie znaleziono urządzenia o ID: {device_id}")
            return
        
        try:
            success = await target_coordinator.async_set_manual_mode(airflow_value, air_extraction_value)
            if success:
                _LOGGER.info(f"Tryb ręczny ustawiony pomyślnie dla urządzenia {device_id}")
            else:
                _LOGGER.error(f"Nie udało się ustawić trybu ręcznego dla urządzenia {device_id}")
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas ustawiania trybu ręcznego: {e}")

    # Rejestruj serwis tylko jeśli jeszcze nie istnieje
    if not hass.services.has_service(DOMAIN, "set_manual_mode"):
        hass.services.async_register(
            DOMAIN,
            "set_manual_mode",
            async_set_manual_mode_service,
            schema=SERVICE_SET_MANUAL_MODE_SCHEMA,
        )
        _LOGGER.info("Zarejestrowano serwis reqnet.set_manual_mode")
        
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Reqnet integration from config entry")

    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Usuń serwis jeśli to był ostatni entry
        if not hass.data[DOMAIN]:
            if hass.services.has_service(DOMAIN, "set_manual_mode"):
                hass.services.async_remove(DOMAIN, "set_manual_mode")
                _LOGGER.info("Usunięto serwis reqnet.set_manual_mode")

    return unload_ok
