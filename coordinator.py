# /config/custom_components/reqnet/coordinator.py
import logging
from datetime import timedelta
import json
import asyncio # Upewnij się, że ten import istnieje

# Usunięto import async_timeout, jeśli nie jest używany nigdzie indziej
# import async_timeout 
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import mqtt # Kluczowy import dla MQTT

_LOGGER = logging.getLogger(__name__)

# Częstotliwość odpytywania rekuperatora (np. co 30 sekund)
UPDATE_INTERVAL = timedelta(seconds=30) # Możesz dostosować

class ReqnetDataCoordinator(DataUpdateCoordinator):
    """Zarządza pobieraniem danych Reqnet przez MQTT."""

    def __init__(self, hass: HomeAssistant, mac_address: str):
        """Inicjalizacja."""
        self.hass = hass # <<< WAŻNE: Zapisz instancję hass
        self.mac_address = mac_address.replace(":", "").upper() # Upewnij się, że format MAC jest spójny
        
        # Tematy dla CurrentWorkParameters
        self.request_cwp_topic = f"{self.mac_address}/CurrentWorkParameters"
        self.response_cwp_topic = f"{self.mac_address}/CurrentWorkParametersResult"
        
        # Tematy dla AutomaticMode
        self.command_am_topic = f"{self.mac_address}/AutomaticMode"
        self.response_am_topic = f"{self.mac_address}/AutomaticModeResult" # Do ewentualnego nasłuchu/logowania wyniku

        self.data = None # Przechowuje ostatnie 'Values' z CurrentWorkParameters
        self._unsub_cwp = None # Funkcja do anulowania subskrypcji CurrentWorkParametersResult
        self._unsub_am_result = None # Opcjonalna funkcja do anulowania subskrypcji AutomaticModeResult

        super().__init__(
            hass,
            _LOGGER,
            name=f"Reqnet Data ({self.mac_address})", # Lepsza nazwa dla logowania
            update_interval=UPDATE_INTERVAL,
        )

    async def _handle_mqtt_message(self, msg):
        """Obsługuje nowe wiadomości MQTT z subskrybowanych tematów."""
        _LOGGER.debug(f"Otrzymano wiadomość MQTT na temacie '{msg.topic}': {msg.payload}")
        payload_str = ""
        try:
            payload_str = msg.payload.decode('utf-8') if isinstance(msg.payload, bytes) else str(msg.payload)
            data = json.loads(payload_str)

            # Obsługa odpowiedzi dla CurrentWorkParametersResult
            if msg.topic == self.response_cwp_topic:
                if data.get("CurrentWorkParametersResult") is True and "Values" in data:
                    _LOGGER.debug(f"Przetworzone dane z {self.response_cwp_topic}: {data['Values']}")
                    # Zaktualizuj self.data i powiadom Home Assistant
                    self.async_set_updated_data(data["Values"]) 
                else:
                    message = data.get("Message", "Brak wartości 'Values' lub wynik negatywny")
                    _LOGGER.error(f"Błąd w danych z {self.response_cwp_topic}: {message}")
                    # Można by rozważyć rzucenie UpdateFailed, jeśli błąd jest krytyczny dla sensorów
                    # self.async_set_updated_data(None) # Lub ustaw dane na None, aby sensory pokazały niedostępność

            # Opcjonalna obsługa odpowiedzi dla AutomaticModeResult (do logowania)
            elif msg.topic == self.response_am_topic:
                if data.get("AutomaticModeResult") is True:
                    _LOGGER.info(f"Potwierdzenie ({self.response_am_topic}): Tryb automatyczny włączony. Wiadomość: {data.get('Message', '')}")
                else:
                    _LOGGER.warning(f"Potwierdzenie ({self.response_am_topic}): Nie udało się włączyć trybu automatycznego. Wiadomość: {data.get('Message', 'Brak wiadomości')}")
            else:
                _LOGGER.warning(f"Otrzymano wiadomość na nieobsługiwanym temacie MQTT: {msg.topic}")

        except json.JSONDecodeError:
            _LOGGER.error(f"Błąd dekodowania JSON z tematu {msg.topic}: {payload_str}")
        except Exception as e:
            _LOGGER.exception(f"Nieoczekiwany błąd podczas przetwarzania wiadomości MQTT z {msg.topic}: {e}")


    async def _async_update_data(self):
        """Pobiera dane z Reqnet przez MQTT (wysyła żądanie)."""
        _LOGGER.debug(f"Żądanie danych (CurrentWorkParameters) z Reqnet na temat: {self.request_cwp_topic}")
        
        # Zasubskrybuj temat odpowiedzi CurrentWorkParametersResult, jeśli jeszcze nie jest
        if not self._unsub_cwp:
            try:
                self._unsub_cwp = await mqtt.async_subscribe(
                    self.hass,
                    self.response_cwp_topic,
                    self._handle_mqtt_message, # Użyj wspólnego handlera
                    qos=0 # Dostosuj qos jeśli potrzebujesz
                )
                _LOGGER.debug(f"Zasubskrybowano temat: {self.response_cwp_topic}")
            except Exception as e:
                _LOGGER.error(f"Nie udało się zasubskrybować tematu {self.response_cwp_topic}: {e}")
                raise UpdateFailed(f"Nie udało się zasubskrybować tematu MQTT: {e}")

        # Opcjonalnie: Zasubskrybuj temat odpowiedzi AutomaticModeResult do logowania
        # Robimy to tutaj, aby upewnić się, że subskrypcja jest aktywna, gdyby była potrzebna
        if not self._unsub_am_result:
            try:
                self._unsub_am_result = await mqtt.async_subscribe(
                    self.hass,
                    self.response_am_topic,
                    self._handle_mqtt_message, # Użyj wspólnego handlera
                    qos=0
                )
                _LOGGER.debug(f"Zasubskrybowano temat: {self.response_am_topic}")
            except Exception as e:
                _LOGGER.warning(f"Nie udało się zasubskrybować tematu {self.response_am_topic}: {e}")
                # To nie jest krytyczne dla aktualizacji danych sensorów, więc tylko ostrzeżenie

        # Wyślij żądanie danych
        try:
            await mqtt.async_publish(self.hass, self.request_cwp_topic, "", qos=0, retain=False)
            _LOGGER.debug(f"Wysłano żądanie na {self.request_cwp_topic}")
            # Dane zostaną zaktualizowane w _handle_mqtt_message po otrzymaniu odpowiedzi
            # DataUpdateCoordinator oczekuje, że _async_update_data zwróci dane lub rzuci UpdateFailed
            # W tym modelu (żądanie-odpowiedź MQTT), bezpośrednie zwracanie danych tutaj jest trudne.
            # Zamiast tego, _handle_mqtt_message wywoła self.async_set_updated_data().
            # Aby uniknąć timeoutu w DataUpdateCoordinator, jeśli odpowiedź nie przyjdzie szybko,
            # można zwrócić ostatnio znane dane lub poczekać na odpowiedź z timeoutem.
            # Na razie, zakładamy, że aktualizacja nastąpi asynchronicznie.
            # Jeśli self.data nie jest None, zwróć je, aby uniknąć błędu "no data" przy pierwszym odświeżeniu po restarcie HA.
            return self.data # Zwróć ostatnio znane dane lub None, jeśli jeszcze ich nie ma
        except Exception as e:
            _LOGGER.error(f"Nie udało się wysłać żądania na {self.request_cwp_topic}: {e}")
            raise UpdateFailed(f"Nie udało się wysłać żądania MQTT: {e}")

    async def async_set_automatic_mode(self) -> bool:
        """Wysyła polecenie włączenia trybu inteligentnego (AutomaticMode) przez MQTT."""
        _LOGGER.info(f"Wysyłanie polecenia AutomaticMode na temat MQTT: {self.command_am_topic}")
        try:
            await mqtt.async_publish(
                self.hass,
                self.command_am_topic,
                "", # Pusty payload
                qos=0, # Dostosuj qos
                retain=False
            )
            _LOGGER.info(f"Polecenie AutomaticMode wysłane pomyślnie na temat {self.command_am_topic}.")
            # Wynik przyjdzie na self.response_am_topic i zostanie obsłużony w _handle_mqtt_message (jeśli zasubskrybowany)
            
            # Możesz rozważyć krótkie opóźnienie i wymuszenie odświeżenia danych,
            # aby sensory mogły odzwierciedlić zmianę trybu.
            await asyncio.sleep(1) # Daj urządzeniu chwilę na przetworzenie polecenia
            await self.async_request_refresh() # Poproś o odświeżenie danych sensorów

            return True # Sukces wysłania polecenia
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