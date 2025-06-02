# /config/custom_components/reqnet/__init__.py
"""The Reqnet Recuperator integration."""
import asyncio
import logging
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_MAC, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession # <<< DODAJ TEN IMPORT

from .const import DOMAIN
from .coordinator import ReqnetDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Reqnet Recuperator from a configuration entry."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Reqnet Recuperator from a config entry."""
    _LOGGER.debug("Setting up Reqnet integration from config entry")

    mac_address = entry.data.get(CONF_MAC)
    host = entry.data.get(CONF_HOST) # 'host' może być nadal potrzebny do logowania lub innych funkcji, ale nie dla tego koordynatora

    if not mac_address: # 'host' może nie być krytyczny, jeśli komunikacja jest tylko MQTT
        _LOGGER.error("MAC address not found in config entry data.")
        raise ConfigEntryNotReady("MAC address is missing.")
    
    # Jeśli 'host' jest używany tylko do logowania lub przyszłych funkcji,
    # możesz go nadal wczytywać, ale nie przekazuj do koordynatora MQTT.
    if not host:
        _LOGGER.warning("Host not found in config entry data, may affect some functionalities if HTTP is used elsewhere.")


    # Prawidłowa inicjalizacja dla Twojego koordynatora MQTT:
    coordinator = ReqnetDataCoordinator(hass, mac_address) 
    
    try:
        # Pierwsze odświeżenie danych (dla koordynatora MQTT to wyśle żądanie i ustawi subskrypcję)
        await coordinator.async_config_entry_first_refresh() 
    except Exception as ex:
        _LOGGER.error(f"Failed to fetch initial data for Reqnet device {mac_address} (Host: {host}): {ex}")
        raise ConfigEntryNotReady(f"Failed to connect to Reqnet device: {ex}") from ex

    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.info("INIT.PY: Przed wywołaniem async_forward_entry_setups dla platform: %s", PLATFORMS) # KLUCZOWY LOG
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("INIT.PY: Po wywołaniu async_forward_entry_setups") # KLUCZOWY LOG


        
    return True



async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Reqnet integration from config entry")

    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator: # Sprawdź, czy koordynator istnieje
        await coordinator.async_shutdown() # <<< WYWOŁAJ METODĘ ZAMKNIĘCIA Z KOORDYNATORA

    unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


