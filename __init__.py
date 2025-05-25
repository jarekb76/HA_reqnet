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
    host = entry.data.get(CONF_HOST)

    if not mac_address or not host:
        _LOGGER.error("MAC address or Host not found in config entry data.")
        raise ConfigEntryNotReady("MAC address or Host is missing.")

    session = async_get_clientsession(hass) # <<< POBIERZ SESJĘ AIOHTTP

    # Przekaż 'host' i 'session' do konstruktora koordynatora
    coordinator = ReqnetDataCoordinator(hass, session, host, mac_address) # <<< ZMODYFIKOWANA INICJALIZACJA
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.error(f"Failed to fetch initial data for Reqnet device {mac_address} (Host: {host}): {ex}")
        raise ConfigEntryNotReady(f"Failed to connect to Reqnet device: {ex}") from ex

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Reqnet integration from config entry")

    # Usunięto odwołanie do koordynatora, ponieważ `async_forward_entry_unloads` powinno sobie z tym poradzić
    # coordinator = hass.data[DOMAIN].get(entry.entry_id)
    # if coordinator:
    # await coordinator.async_shutdown() # Jeśli masz specjalną logikę zamykania w koordynatorze

    unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None) # Dodano None, aby uniknąć KeyError, jeśli wpis już nie istnieje

    return unload_ok