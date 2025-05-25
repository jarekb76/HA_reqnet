import logging
from datetime import timedelta
import json # Upewnij się, że ten import też jest
import asyncio # DODAJ TĘ LINIĘ!

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import mqtt

_LOGGER = logging.getLogger(__name__)

# Częstotliwość odpytywania rekuperatora (np. co 30 sekund)
UPDATE_INTERVAL = timedelta(seconds=30)

class ReqnetDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Reqnet data."""

    def __init__(self, hass: HomeAssistant, mac_address: str):
        """Initialize."""
        self.mac_address = mac_address
        self.request_topic = f"{self.mac_address}/CurrentWorkParameters"
        self.response_topic = f"{self.mac_address}/CurrentWorkParametersResult"
        self.data = None
        self.unsub_mqtt = None

        super().__init__(
            hass,
            _LOGGER,
            name="Reqnet Data",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Reqnet."""
        _LOGGER.debug(f"Requesting data from Reqnet at topic: {self.request_topic}")
        try:
            await mqtt.async_publish(self.hass, self.request_topic, "")

            if not self.unsub_mqtt:
                self.unsub_mqtt = await mqtt.async_subscribe(
                    self.hass,
                    self.response_topic,
                    self._mqtt_message_received,
                    1
                )

            # Czekamy na dane, które zostaną ustawione przez _mqtt_message_received
            # Możemy dodać licznik prób, żeby nie czekać w nieskończoność, jeśli rekuperator nie odpowie
            attempts = 0
            while self.data is None and attempts < 20: # Czekamy max 10 sekund (20*0.5s)
                await asyncio.sleep(0.5)
                attempts += 1

            if self.data is None:
                raise asyncio.TimeoutError("No data received from Reqnet via MQTT after multiple attempts.")

            current_data = self.data
            self.data = None # Reset na następny cykl
            return current_data

        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout awaiting MQTT response from Reqnet on topic {self.response_topic}")
            raise UpdateFailed("Timeout fetching Reqnet data")
        except Exception as err:
            _LOGGER.error(f"Error fetching Reqnet data: {err}")
            raise UpdateFailed(f"Error fetching Reqnet data: {err}")
            
            
    async def async_set_automatic_mode(self) -> bool:
        """Wywołuje funkcję API AutomaticMode na urządzeniu."""
        if not self.host or not hasattr(self, 'websession'):
            _LOGGER.error("Koordynator nie ma skonfigurowanego hosta lub sesji webowej do wysyłania poleceń.")
            return False

        # Zgodnie z dokumentacją API, używamy metody HTTP GET
        url = f"http://{self.host}/API/RunFunction?name=AutomaticMode"
        _LOGGER.debug(f"Wywoływanie AutomaticMode przez HTTP: {url}")

        try:
            async with async_timeout.timeout(10): # Timeout po 10 sekundach
                response = await self.websession.get(url)
                # Sprawdź, czy odpowiedź jest poprawna (status 2xx)
                response.raise_for_status()
                data = await response.json()
                _LOGGER.debug(f"Odpowiedź z AutomaticMode: {data}")

                if data.get("AutomaticModeResult") is True:
                    _LOGGER.info("Pomyślnie włączono tryb inteligentny (Automatic Mode).")
                    # Opcjonalnie, możesz wymusić odświeżenie danych sensorów,
                    # jeśli włączenie tego trybu natychmiast zmienia jakieś stany.
                    await self.async_request_refresh()
                    return True
                else:
                    error_message = data.get("Message", "Nieznany błąd")
                    _LOGGER.error(f"Nie udało się włączyć trybu inteligentnego: {error_message}")
                    return False
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Błąd komunikacji API podczas wywoływania AutomaticMode: {err}")
            return False
        except async_timeout.TimeoutError:
            _LOGGER.error("Timeout podczas wywoływania AutomaticMode API.")
            return False
        except Exception as e: # Ogólny wyjątek dla nieoczekiwanych błędów
            _LOGGER.error(f"Nieoczekiwany błąd podczas wywoływania AutomaticMode: {e}")
            return False
    async def _mqtt_message_received(self, msg):
        """Handle incoming MQTT messages."""
        try:
            if not msg.payload:
                _LOGGER.warning(f"Received empty MQTT payload on {msg.topic}")
                return

            payload_json = json.loads(msg.payload)
            if not payload_json.get("CurrentWorkParametersResult") or "Values" not in payload_json:
                _LOGGER.warning(f"Unexpected JSON structure from Reqnet: {payload_json}")
                return

            self.data = payload_json["Values"]
            _LOGGER.debug(f"Received data from Reqnet: {self.data}")

        except json.JSONDecodeError:
            _LOGGER.error(f"Failed to decode JSON from MQTT message on {msg.topic}. Payload: {msg.payload}")
        except Exception as e:
            _LOGGER.error(f"Error processing MQTT message: {e}")

    async def async_shutdown(self):
        """Unsubscribe from MQTT on shutdown."""
        if self.unsub_mqtt:
            self.unsub_mqtt()
            self.unsub_mqtt = None