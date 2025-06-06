"""Config flow for Reqnet Recuperator integration."""
import logging
import json

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession # ZMIENIONY IMPORT!

from .const import DOMAIN, API_PATH_API

_LOGGER = logging.getLogger(__name__)

# Schemat danych dla użytkownika (tylko host)
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
})

class ReqnetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Reqnet Recuperator."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            mac_address = None

            # Spróbuj pobrać MAC address z API przez HTTP
            try:
                # Używamy sesji klienta aiohttp Home Assistant
                session = async_get_clientsession(self.hass)
                api_url = f"http://{host}{API_PATH_API}"
                _LOGGER.debug(f"Attempting to connect to Reqnet API at: {api_url}")
                
                # Czasami URL z API może być wrażliwy na końcowe slash/jego brak.
                # Upewnijmy się, że jest poprawny.
                response = await session.get(api_url, timeout=10)
                
                response.raise_for_status() # Rzuć wyjątek dla kodów statusu 4xx/5xx

                api_data = await response.json() # Ważne: używamy await response.json() dla aiohttp
                _LOGGER.debug(f"Received API response: {api_data}")

                if not api_data.get("APIResult") or "MAC" not in api_data:
                    _LOGGER.error(f"Unexpected API response structure from {host}: {api_data}")
                    errors["base"] = "invalid_response"
                else:
                    mac_address = api_data["MAC"]
                    _LOGGER.info(f"Successfully discovered MAC address: {mac_address} for host: {host}")

            except Exception as e: # Zmieniono na ogólny Exception na potrzeby diagnostyki
                response_text = "N/A"
                if 'response' in locals() and hasattr(response, 'text'):
                    try:
                        response_text = await response.text() # Spróbuj pobrać tekst odpowiedzi
                    except Exception:
                        response_text = "Could not retrieve response text"
                
                _LOGGER.exception(f"An error occurred during API call to {host}. Response: {response_text}. Error type: {type(e).__name__}, Message: {e}")
                
                if isinstance(e, (TimeoutError, httpx.ConnectError)): # Uwaga: httpx.ConnectError może nadal być rzucony, jeśli jest w buforze
                    errors["base"] = "cannot_connect"
                elif isinstance(e, json.JSONDecodeError):
                    errors["base"] = "invalid_json"
                elif isinstance(e, httpx.RequestError): # Uwaga: httpx.RequestError może nadal być rzucony
                     errors["base"] = "http_error"
                else:
                    errors["base"] = "unknown"

            if not errors and mac_address:
                unique_id = mac_address.replace(":", "").lower()
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Reqnet ({mac_address})",
                    data={
                        CONF_HOST: host,
                        CONF_MAC: mac_address
                    }
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @callback
    def _async_current_entries(self):
        """Return current entries."""
        return self._async_get_current_entries(include_ignore=False)