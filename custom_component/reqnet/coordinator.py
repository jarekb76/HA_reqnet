# /config/custom_components/reqnet/coordinator.py
import logging
from datetime import timedelta
import json
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import mqtt
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

class ReqnetDataCoordinator(DataUpdateCoordinator):
    """Zarządza pobieraniem danych Reqnet przez MQTT."""

    def __init__(self, hass: HomeAssistant, mac_address_from_config: str):
        """Inicjalizacja."""
        self.hass = hass
        
        self.mac_for_mqtt_topics = mac_address_from_config.upper() 
        self.mac_address = mac_address_from_config.replace(":", "").upper()

        _LOGGER.debug(f"MAC dla tematów MQTT: {self.mac_for_mqtt_topics}")
        _LOGGER.debug(f"MAC (sformatowany) dla identyfikatorów HA: {self.mac_address}")
        
        # Tematy MQTT
        self.request_cwp_topic = f"{self.mac_for_mqtt_topics}/CurrentWorkParameters"
        self.response_cwp_topic = f"{self.mac_for_mqtt_topics}/CurrentWorkParametersResult"
        
        # Tematy dla trybu automatycznego
        self.command_am_topic = f"{self.mac_for_mqtt_topics}/AutomaticMode"
        self.response_am_topic = f"{self.mac_for_mqtt_topics}/AutomaticModeResult"
        
        # Tematy dla trybu ręcznego
        self.command_mm_topic = f"{self.mac_for_mqtt_topics}/ManualMode"
        self.response_mm_topic = f"{self.mac_for_mqtt_topics}/ManualModeResult"

        self.data = None 
        self._unsub_cwp = None
        self._unsub_am_result = None
        self._unsub_mm_result = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"Reqnet Data ({self.mac_address})",
            update_interval=UPDATE_INTERVAL,
        )

        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, self.mac_address)},
            name="Reqnet",
            manufacturer="Reqnet",
            model=f"Recuperator ({mac_address_from_config})",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Zwraca informacje o urządzeniu dla encji."""
        return self._device_info

    async def _handle_mqtt_message(self, msg):
        _LOGGER.info(f"HANDLER MQTT: Otrzymano wiadomość na temacie '{msg.topic}'")
        payload_str = ""
        try:
            payload_str = msg.payload.decode('utf-8') if isinstance(msg.payload, bytes) else str(msg.payload)
            _LOGGER.debug(f"HANDLER MQTT: Surowy payload dla {msg.topic}: {payload_str}")
            data = json.loads(payload_str)

            if msg.topic == self.response_cwp_topic:
                if data.get("CurrentWorkParametersResult") is True and "Values" in data:
                    _LOGGER.info(f"HANDLER MQTT (CWP): Poprawne dane odebrane. Values: {data['Values']}")
                    self.async_set_updated_data(data["Values"]) 
                else:
                    message = data.get("Message", "Brak wartości 'Values' lub wynik negatywny w odpowiedzi CWP")
                    _LOGGER.error(f"HANDLER MQTT (CWP): Błąd w danych z {self.response_cwp_topic}: {message}. Otrzymane dane: {data}")
                    self.async_set_updated_data(None)
                    
            elif msg.topic == self.response_am_topic:
                if data.get("AutomaticModeResult") is True:
                    _LOGGER.info(f"Potwierdzenie ({self.response_am_topic}): Tryb automatyczny włączony. Wiadomość: {data.get('Message', '')}")
                else:
                    _LOGGER.warning(f"Potwierdzenie ({self.response_am_topic}): Nie udało się włączyć trybu automatycznego. Wiadomość: {data.get('Message', 'Brak wiadomości')}")
                    
            elif msg.topic == self.response_mm_topic:
                if data.get("ManualModeResult") is True:
                    _LOGGER.info(f"Potwierdzenie ({self.response_mm_topic}): Tryb ręczny włączony. Wiadomość: {data.get('Message', '')}")
                else:
                    _LOGGER.warning(f"Potwierdzenie ({self.response_mm_topic}): Nie udało się włączyć trybu ręcznego. Wiadomość: {data.get('Message', 'Brak wiadomości')}")
                    
            else:
                _LOGGER.warning(f"Otrzymano wiadomość na nieobsługiwanym temacie MQTT: {msg.topic}")

        except json.JSONDecodeError:
            _LOGGER.error(f"Błąd dekodowania JSON z tematu {msg.topic}: {payload_str}")
            if msg.topic == self.response_cwp_topic: 
                self.async_set_updated_data(None)
        except Exception as e:
            _LOGGER.exception(f"Nieoczekiwany błąd podczas przetwarzania wiadomości MQTT z {msg.topic}: {e}")
            if msg.topic == self.response_cwp_topic: 
                self.async_set_updated_data(None)

    async def _async_update_data(self):
        _LOGGER.debug(f"Żądanie danych (CurrentWorkParameters) z Reqnet na temat: {self.request_cwp_topic}")
        
        # Subskrypcja CWP
        if not self._unsub_cwp:
            try:
                self._unsub_cwp = await mqtt.async_subscribe(
                    self.hass, self.response_cwp_topic, self._handle_mqtt_message, qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat CWP result: {self.response_cwp_topic}")
            except Exception as e:
                _LOGGER.error(f"Nie udało się zasubskrybować tematu {self.response_cwp_topic}: {e}")
                raise UpdateFailed(f"Nie udało się zasubskrybować tematu MQTT CWP: {e}")
        
        # Subskrypcja AM
        if not self._unsub_am_result:
            try:
                self._unsub_am_result = await mqtt.async_subscribe(
                    self.hass, self.response_am_topic, self._handle_mqtt_message, qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat AM result: {self.response_am_topic}")
            except Exception as e:
                _LOGGER.warning(f"Nie udało się zasubskrybować tematu {self.response_am_topic}: {e}")
        
        # Subskrypcja MM
        if not self._unsub_mm_result:
            try:
                self._unsub_mm_result = await mqtt.async_subscribe(
                    self.hass, self.response_mm_topic, self._handle_mqtt_message, qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat MM result: {self.response_mm_topic}")
            except Exception as e:
                _LOGGER.warning(f"Nie udało się zasubskrybować tematu {self.response_mm_topic}: {e}")
        
        try:
            await mqtt.async_publish(self.hass, self.request_cwp_topic, "", qos=0, retain=False)
            _LOGGER.debug(f"Wysłano żądanie na {self.request_cwp_topic}")
            return self.data 
        except Exception as e:
            _LOGGER.error(f"Nie udało się wysłać żądania na {self.request_cwp_topic}: {e}")
            raise UpdateFailed(f"Nie udało się wysłać żądania MQTT CWP: {e}")

    async def async_set_automatic_mode(self) -> bool:
        """Ustawia tryb automatyczny."""
        _LOGGER.info(f"Wysyłanie polecenia AutomaticMode na temat MQTT: {self.command_am_topic}")
        try:
            await mqtt.async_publish(self.hass, self.command_am_topic, "", qos=0, retain=False)
            _LOGGER.info(f"Polecenie AutomaticMode wysłane pomyślnie na temat {self.command_am_topic}.")
            await asyncio.sleep(1) 
            await self.async_request_refresh()
            return True
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas wysyłania polecenia AutomaticMode przez MQTT: {e}")
            return False

    async def async_set_manual_mode(self, airflow_value: int = None, air_extraction_value: int = None) -> bool:
        """Ustawia tryb ręczny z zadanymi wartościami nawiewu i wyciągu."""
        _LOGGER.info(f"Wysyłanie polecenia ManualMode na temat MQTT: {self.command_mm_topic}")
        
        # Jeśli nie podano wartości, użyj aktualnych wartości z API lub wartości domyślnych
        if airflow_value is None or air_extraction_value is None:
            if self.data and len(self.data) > 6:
                # Użyj aktualnych wartości z API Index 6 i 7 (Python index 5 i 6)
                current_airflow = self.data[5] if self.data[5] is not None else 200
                current_extraction = self.data[6] if self.data[6] is not None else 200
                airflow_value = airflow_value or current_airflow
                air_extraction_value = air_extraction_value or current_extraction
            else:
                # Wartości domyślne jeśli brak danych
                airflow_value = airflow_value or 200
                air_extraction_value = air_extraction_value or 200
        
        # Przygotuj payload JSON z parametrami
        payload = {
            "AirflowValue": airflow_value,
            "ValueOfAirExtraction": air_extraction_value
        }
        
        try:
            payload_json = json.dumps(payload)
            _LOGGER.info(f"Wysyłanie ManualMode z parametrami: {payload_json}")
            
            await mqtt.async_publish(self.hass, self.command_mm_topic, payload_json, qos=0, retain=False)
            _LOGGER.info(f"Polecenie ManualMode wysłane pomyślnie na temat {self.command_mm_topic}.")
            await asyncio.sleep(1) 
            await self.async_request_refresh()
            return True
        except Exception as e:
            _LOGGER.exception(f"Błąd podczas wysyłania polecenia ManualMode przez MQTT: {e}")
            return False

    async def async_shutdown(self):
        """Zamyka połączenia MQTT."""
        _LOGGER.debug("Anulowanie subskrypcji MQTT dla Reqnet.")
        
        if self._unsub_cwp:
            self._unsub_cwp()
            self._unsub_cwp = None
            _LOGGER.debug(f"Anulowano subskrypcję tematu: {self.response_cwp_topic}")
            
        if self._unsub_am_result:
            self._unsub_am_result()
            self._unsub_am_result = None
            _LOGGER.debug(f"Anulowano subskrypcję tematu: {self.response_am_topic}")
            
        if self._unsub_mm_result:
            self._unsub_mm_result()
            self._unsub_mm_result = None
            _LOGGER.debug(f"Anulowano subskrypcję tematu: {self.response_mm_topic}")