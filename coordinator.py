# /config/custom_components/reqnet/coordinator.py
import logging
from datetime import timedelta
import json
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import mqtt

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

class ReqnetDataCoordinator(DataUpdateCoordinator):
    """Zarządza pobieraniem danych Reqnet przez MQTT."""

    def __init__(self, hass: HomeAssistant, mac_address_from_config: str): # np. "8C:CE:4E:FE:B6:B3"
        """Inicjalizacja."""
        self.hass = hass
        
        # 1. Adres MAC dla tematów MQTT (zgodnie z urządzeniem: wielkie litery, Z DWUKROPKAMI)
        self.mac_for_mqtt_topics = mac_address_from_config.upper() 
        
        # 2. Adres MAC sformatowany dla identyfikatorów Home Assistant 
        #    (np. unique_id encji, device_info identifiers - wielkie litery, BEZ DWUKROPKÓW)
        #    Ten atrybut będzie używany przez encje jako `coordinator.mac_address`
        self.mac_address = mac_address_from_config.replace(":", "").upper()

        _LOGGER.debug(f"MAC dla tematów MQTT: {self.mac_for_mqtt_topics}")
        _LOGGER.debug(f"MAC dla identyfikatorów HA: {self.mac_address}")
        
        # Tematy dla CurrentWorkParameters (używamy mac_for_mqtt_topics)
        self.request_cwp_topic = f"{self.mac_for_mqtt_topics}/CurrentWorkParameters"
        self.response_cwp_topic = f"{self.mac_for_mqtt_topics}/CurrentWorkParametersResult"
        
        # Tematy dla AutomaticMode (używamy mac_for_mqtt_topics)
        self.command_am_topic = f"{self.mac_for_mqtt_topics}/AutomaticMode"
        self.response_am_topic = f"{self.mac_for_mqtt_topics}/AutomaticModeResult"

        self.data = None 
        self._unsub_cwp = None
        self._unsub_am_result = None

        super().__init__(
            hass,
            _LOGGER,
            # Nazwa koordynatora może używać sformatowanego MAC dla spójności z ID encji
            name=f"Reqnet Data ({self.mac_address})", 
            update_interval=UPDATE_INTERVAL,
        )

    # --- METODY _handle_mqtt_message, _async_update_data, async_set_automatic_mode, async_shutdown ---
    # --- POZOSTAJĄ TAKIE SAME JAK W POPRZEDNIEJ SUGESTII (powinny używać ---
    # --- self.response_cwp_topic, self.request_cwp_topic itd., które są teraz poprawnie zdefiniowane) ---

    async def _handle_mqtt_message(self, msg):
        """Obsługuje nowe wiadomości MQTT z subskrybowanych tematów."""
        # Użyj INFO dla testowania, aby łatwiej było zobaczyć te logi
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
                    # Możesz chcieć ustawić self.data na None lub rzucić UpdateFailed, aby sensory stały się niedostępne
                    self.async_set_updated_data(None) # Sygnalizuje błąd pobierania danych
            elif msg.topic == self.response_am_topic:
                if data.get("AutomaticModeResult") is True:
                    _LOGGER.info(f"Potwierdzenie ({self.response_am_topic}): Tryb automatyczny włączony. Wiadomość: {data.get('Message', '')}")
                else:
                    _LOGGER.warning(f"Potwierdzenie ({self.response_am_topic}): Nie udało się włączyć trybu automatycznego. Wiadomość: {data.get('Message', 'Brak wiadomości')}")
            else:
                _LOGGER.warning(f"Otrzymano wiadomość na nieobsługiwanym temacie MQTT: {msg.topic}")

        except json.JSONDecodeError:
            _LOGGER.error(f"Błąd dekodowania JSON z tematu {msg.topic}: {payload_str}")
            if msg.topic == self.response_cwp_topic: self.async_set_updated_data(None)
        except Exception as e:
            _LOGGER.exception(f"Nieoczekiwany błąd podczas przetwarzania wiadomości MQTT z {msg.topic}: {e}")
            if msg.topic == self.response_cwp_topic: self.async_set_updated_data(None)

    async def _async_update_data(self):
        """Pobiera dane z Reqnet przez MQTT (wysyła żądanie)."""
        _LOGGER.debug(f"Żądanie danych (CurrentWorkParameters) z Reqnet na temat: {self.request_cwp_topic}")
        
        # Upewnij się, że subskrypcje są aktywne
        # Subskrypcja CurrentWorkParametersResult
        if not self._unsub_cwp:
            try:
                self._unsub_cwp = await mqtt.async_subscribe(
                    self.hass, self.response_cwp_topic, self._handle_mqtt_message, qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat CWP result: {self.response_cwp_topic}")
            except Exception as e:
                _LOGGER.error(f"Nie udało się zasubskrybować tematu {self.response_cwp_topic}: {e}")
                raise UpdateFailed(f"Nie udało się zasubskrybować tematu MQTT CWP: {e}")

        # Subskrypcja AutomaticModeResult (opcjonalna, do logowania)
        if not self._unsub_am_result:
            try:
                self._unsub_am_result = await mqtt.async_subscribe(
                    self.hass, self.response_am_topic, self._handle_mqtt_message, qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat AM result: {self.response_am_topic}")
            except Exception as e:
                _LOGGER.warning(f"Nie udało się zasubskrybować tematu {self.response_am_topic}: {e}")
        
        # Wyślij żądanie danych
        try:
            await mqtt.async_publish(self.hass, self.request_cwp_topic, "", qos=0, retain=False)
            _LOGGER.debug(f"Wysłano żądanie na {self.request_cwp_topic}")
            # Wzorzec żądanie-odpowiedź przez MQTT: _async_update_data inicjuje żądanie.
            # Rzeczywiste dane są ustawiane w _handle_mqtt_message przez self.async_set_updated_data().
            # Aby uniknąć problemów z pierwszym odświeżeniem, jeśli odpowiedź nie nadejdzie natychmiast,
            # można zaimplementować mechanizm oczekiwania (np. asyncio.Event) lub po prostu zwrócić
            # ostatnio znane dane. Zwrócenie self.data jest prostsze.
            return self.data 
        except Exception as e:
            _LOGGER.error(f"Nie udało się wysłać żądania na {self.request_cwp_topic}: {e}")
            raise UpdateFailed(f"Nie udało się wysłać żądania MQTT CWP: {e}")

    async def async_set_automatic_mode(self) -> bool:
        """Wysyła polecenie włączenia trybu inteligentnego (AutomaticMode) przez MQTT."""
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

    async def async_shutdown(self):
        """Anuluje subskrypcje MQTT przy zamykaniu."""
        _LOGGER.debug("Anulowanie subskrypcji MQTT dla Reqnet.")
        if self._unsub_cwp:
            self._unsub_cwp()
            self._unsub_cwp = None
            _LOGGER.debug(f"Anulowano subskrypcję tematu: {self.response_cwp_topic}")
        if self._unsub_am_result:
            self._unsub_am_result()
            self._unsub_am_result = None
            _LOGGER.debug(f"Anulowano subskrypcję tematu: {self.response_am_topic}")