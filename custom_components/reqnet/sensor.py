"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfRatio,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
# Upewnij się, że DOMAIN i ReqnetDataCoordinator są poprawnie zdefiniowane/importowane
from .const import DOMAIN # Zakładam, że DOMAIN jest zdefiniowany w .const
from .coordinator import ReqnetDataCoordinator # Zakładam, że koordynator jest w .coordinator

# Definicje sensorów:
# (index_python (API_Index - 1), nazwa_przyrostka, jednostka, ikona, klasa_urządzenia, kategoria_encji)
SENSOR_DEFINITIONS: list[tuple[int, str, str | None, str | None, SensorDeviceClass | None, EntityCategory | None]] = [
    # --- Podstawowe odczyty ---
    (0, "Status urządzenia", None, "mdi:power", SensorDeviceClass.ENUM, None), # API Index 1
    (1, "Maksymalna wartość nawiewu", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-plus", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 2
    (2, "Aktualna temperatura", UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, None), # API Index 3
    (3, "Aktualna wartość nawiewu", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 4
    (4, "Aktualna wartość wyciągu", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-off", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 5
    (5, "Nawiew tryb ręczny", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-settings", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 6
    (6, "Wyciąg tryb ręczny", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-settings", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 7
    (7, "Wilgotność", UnitOfRatio.PERCENTAGE, "mdi:water-percent", SensorDeviceClass.HUMIDITY, None), # API Index 8
    (8, "Poziom CO2", UnitOfRatio.PARTS_PER_MILLION, "mdi:molecule-co2", SensorDeviceClass.CO2, None), # API Index 9
    (9, "Status harmonogramu", None, "mdi:calendar-clock", SensorDeviceClass.ENUM, None), # API Index 10 (0/1)
    (10, "Tryb pracy", None, "mdi:cog-outline", SensorDeviceClass.ENUM, None), # API Index 11 (mapowane wartości)
    (13, "Status grzanie/chłodzenie", None, "mdi:thermostat", SensorDeviceClass.ENUM, None), # API Index 14 (0/1/2)
    (15, "Model urządzenia", None, "mdi:information-outline", None, EntityCategory.DIAGNOSTIC), # API Index 16

    # --- Temperatury szczegółowe ---
    (55, "Temperatura na czerpni", UnitOfTemperature.CELSIUS, "mdi:export", SensorDeviceClass.TEMPERATURE, None), # API Index 56
    (56, "Temperatura na wyrzutni", UnitOfTemperature.CELSIUS, "mdi:import", SensorDeviceClass.TEMPERATURE, None), # API Index 57
    (57, "Temperatura nawiewu", UnitOfTemperature.CELSIUS, "mdi:coolant-temperature", SensorDeviceClass.TEMPERATURE, None), # API Index 58
    (58, "Temperatura wyciągu", UnitOfTemperature.CELSIUS, "mdi:coolant-temperature", SensorDeviceClass.TEMPERATURE, None), # API Index 59
    (59, "Temperatura za nagrzewnicą/chłodnicą", UnitOfTemperature.CELSIUS, "mdi:thermometer-lines", SensorDeviceClass.TEMPERATURE, None), # API Index 60
    (60, "Temperatura GWC", UnitOfTemperature.CELSIUS, "mdi:sun-thermometer-outline", SensorDeviceClass.TEMPERATURE, None), # API Index 61
    (61, "Temperatura w pomieszczeniu", UnitOfTemperature.CELSIUS, "mdi:home-thermometer-outline", SensorDeviceClass.TEMPERATURE, None), # API Index 62
    (62, "Temperatura dodatkowego czujnika", UnitOfTemperature.CELSIUS, "mdi:thermometer-alert", SensorDeviceClass.TEMPERATURE, None), # API Index 63

    # --- Ciśnienia/Opory ---
    (63, "Opór ciągu nawiewnego", UnitOfPressure.PA, "mdi:gauge-low", SensorDeviceClass.PRESSURE, None), # API Index 64
    (64, "Opór ciągu wywiewnego", UnitOfPressure.PA, "mdi:gauge-low", SensorDeviceClass.PRESSURE, None), # API Index 65
    (75, "Ciśnienie nawiew", UnitOfPressure.PA, "mdi:arrow-down-bold-pressure-outline", SensorDeviceClass.PRESSURE, None), # API Index 76 (zakładam Pa)
    (76, "Ciśnienie wyciąg", UnitOfPressure.PA, "mdi:arrow-up-bold-pressure-outline", SensorDeviceClass.PRESSURE, None), # API Index 77 (zakładam Pa)

    # --- Statusy i inne ---
    (39, "Status By-passu", None, "mdi:compare-horizontal", SensorDeviceClass.ENUM, None), # API Index 40 (mapowane wartości)
    (40, "Kod błędu", None, "mdi:alert-circle-outline", None, EntityCategory.DIAGNOSTIC), # API Index 41
    (41, "Kod komunikatu", None, "mdi:information-outline", None, EntityCategory.DIAGNOSTIC), # API Index 42
    (71, "Detekcja wilgotności", None, "mdi:water-check-outline", SensorDeviceClass.ENUM, None), # API Index 72 (0/1)
    (72, "Status nagrzewnicy wstępnej", None, "mdi:radiator", SensorDeviceClass.ENUM, None), # API Index 73 (0/1)
    (73, "Status systemu antyzamrożeniowego", None, "mdi:snowflake-melt", None, None), # API Index 74
    (74, "Status systemu przeciwwykropleniowego", None, "mdi:water-boiler-alert", None, None), # API Index 75
    (83, "Dni do wymiany filtra", UnitOfTime.DAYS, "mdi:air-filter", SensorDeviceClass.DURATION, None), # API Index 84
    (86, "Typ montażu", None, "mdi:tools", SensorDeviceClass.ENUM, EntityCategory.DIAGNOSTIC), # API Index 87 (1-lewy, 2-prawy)
    (92, "Współczynnik nadciśnienia", UnitOfRatio.PERCENTAGE, "mdi:arrow-expand-all", None, None), # API Index 93

    # --- Wentylatory ---
    (65, "Prędkość wentylatora nawiew", UnitOfRatio.PERCENTAGE, "mdi:fan-chevron-up", None, None), # API Index 66
    (66, "Prędkość wentylatora wyciąg", UnitOfRatio.PERCENTAGE, "mdi:fan-chevron-down", None, None), # API Index 67
    (81, "Moc wentylatora nawiewnego", UnitOfPower.WATT, "mdi:lightning-bolt", SensorDeviceClass.POWER, None), # API Index 82
    (82, "Moc wentylatora wywiewnego", UnitOfPower.WATT, "mdi:lightning-bolt", SensorDeviceClass.POWER, None), # API Index 83

    # --- Ustawienia ---
    (67, "Ustawiona temperatura komfortu", UnitOfTemperature.CELSIUS, "mdi:thermostat-box", SensorDeviceClass.TEMPERATURE, None), # API Index 68
    (69, "Aktualna czułość CO2", None, "mdi:molecule-co2", None, None), # API Index 70 (jednostka nieznana z API)
    (70, "Aktualna czułość HIGRO", None, "mdi:water-opacity", None, None), # API Index 71 (jednostka nieznana z API)

    # --- Wersje oprogramowania (diagnostyczne) ---
    (90, "Wersja firmware (major)", None, "mdi:chip", None, EntityCategory.DIAGNOSTIC), # API Index 91
    (91, "Wersja firmware (build)", None, "mdi:chip", None, EntityCategory.DIAGNOSTIC), # API Index 92
    (93, "Wersja firmware WiFi", None, "mdi:wifi", None, EntityCategory.DIAGNOSTIC), # API Index 94

    # --- Współczynniki wydajności dla funkcji (opcjonalne) ---
    # (16, "Wydajność Szybkie grzanie", UnitOfRatio.PERCENTAGE, "mdi:fire", None, None), # API Index 17
    # (17, "Wydajność Szybkie chłodzenie", UnitOfRatio.PERCENTAGE, "mdi:snowflake", None, None), # API Index 18
    # (18, "Wydajność Urlop", UnitOfRatio.PERCENTAGE, "mdi:palm-tree", None, None), # API Index 19
    # (19, "Wydajność Przewietrzanie", UnitOfRatio.PERCENTAGE, "mdi:weather-windy", None, None), # API Index 20
    # (20, "Wydajność Oczyszczanie", UnitOfRatio.PERCENTAGE, "mdi:air-purifier", None, None), # API Index 21
    # (21, "Wydajność Kominek", UnitOfRatio.PERCENTAGE, "mdi:fireplace", None, None), # API Index 22
]

SENSOR_OPTIONS: dict[int, list[str]] = {
    0: ["Włączone", "Wyłączone"],
    9: ["Aktywny", "Nieaktywny"],
    10: [
        "Szybkie grzanie",
        "Szybkie chłodzenie",
        "Urlop",
        "Przewietrzanie",
        "Oczyszczanie",
        "Kominek",
        "Tryb ręczny",
        "Tryb inteligentny",
        "Tryb pomiaru wydajności",
    ],
    13: ["Nieaktywna", "Grzanie", "Chłodzenie"],
    39: [
        "Zamknięty (ręcznie)",
        "Otwarty (ręcznie)",
        "Zamknięty (auto)",
        "Otwarty (auto)",
    ],
    71: ["Aktywna", "Nieaktywna"],
    72: ["Aktywna", "Nieaktywna"],
    86: ["Lewy", "Prawy"],
}

async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry[ReqnetDataCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Reqnet sensor platform."""
    del _hass
    coordinator = config_entry.runtime_data

    entities_to_add = []
    for index, name_suffix, unit, icon, dev_class, entity_cat in SENSOR_DEFINITIONS:
        entities_to_add.append(
            ReqnetSensor(
                coordinator=coordinator,
                index=index,
                name_suffix=name_suffix,
                unit=unit,
                icon=icon,
                device_class=dev_class,
                entity_category=entity_cat,
                options=SENSOR_OPTIONS.get(index),
            )
        )
    async_add_entities(entities_to_add)


class ReqnetSensor(CoordinatorEntity[ReqnetDataCoordinator], SensorEntity):
    _attr_has_entity_name = True # Ustawia, jeśli chcesz, aby nazwa urządzenia była częścią nazwy sensora
    

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        index: int,
        name_suffix: str,
        unit: str | None,
        icon: str | None,
        device_class: SensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None, # POPRAWIONE TYPOWANIE
        options: list[str] | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._index = index

        display_name = f"Reqnet {name_suffix}"

        self.entity_description = SensorEntityDescription(
            key=f"value_{self._index}",
            name=display_name,
            icon=icon,
            native_unit_of_measurement=unit,
            device_class=device_class,
            state_class=(
                SensorStateClass.MEASUREMENT
                if device_class not in (None, SensorDeviceClass.ENUM)
                else None
            ),
            entity_category=entity_category, # Tutaj zostanie przekazana poprawna instancja EntityCategory lub None
            options=options,
        )

        # Unikalne ID dla encji
        self._attr_unique_id = f"{coordinator.mac_address.replace(':', '').lower()}_{self.entity_description.key}"

        # Informacje o urządzeniu (wspólne dla wszystkich sensorów tego urządzenia)
        # Można to ulepszyć, np. dynamicznie ustawiając model na podstawie danych z API (np. indeks 15)
        # w metodzie update koordynatora lub przy pierwszym odczycie, jeśli to bezpieczne.
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"Reqnet Recuperator ({coordinator.mac_address})",
            "manufacturer": "Reqnet",
            "model": "Recuperator", # Można spróbować odczytać API Index 16 (Python index 15)
        }
        # Przykład dynamicznego ustawiania modelu, jeśli dane są już dostępne:
        # if coordinator.data and len(coordinator.data) > 15 and coordinator.data[15] is not None:
        #     self._attr_device_info["model"] = f"Recuperator Model {coordinator.data[15]}"
        
        # Informacje o urządzeniu (wspólne dla wszystkich sensorów tego urządzenia)
        

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or not isinstance(self.coordinator.data, list)
            or self._index >= len(self.coordinator.data)
        ):
            # _LOGGER.debug( # Zmieniono na debug, aby nie spamować logów przy chwilowych problemach
            #    f"Data for sensor {self.entity_description.name} (index {self._index}) is unavailable or out of bounds."
            # )
            return None # Zgodnie z dokumentacją HA, powinno zwracać None lub STATE_UNAVAILABLE

        value = self.coordinator.data[self._index]

        # Mapowanie wartości dla specyficznych sensorów
        # API Index 1 (Python index 0): Status urządzenia
        if self._index == 0:
            return {0: "Wyłączone", 1: "Włączone"}.get(value)
        
        # API Index 10 (Python index 9): Status harmonogramu
        if self._index == 9:
            return {0: "Nieaktywny", 1: "Aktywny"}.get(value)

        # API Index 11 (Python index 10): Tryb pracy
        if self._index == 10:
            modes = {
                1: "Szybkie grzanie", 2: "Szybkie chłodzenie", 3: "Urlop",
                4: "Przewietrzanie", 5: "Oczyszczanie", 6: "Kominek",
                8: "Tryb ręczny", 9: "Tryb inteligentny", 10: "Tryb pomiaru wydajności",
            }
            return modes.get(value)

        # API Index 14 (Python index 13): Status funkcji równoległej (grzanie/chłodzenie)
        if self._index == 13:
            statuses = {0: "Nieaktywna", 1: "Grzanie", 2: "Chłodzenie"}
            return statuses.get(value)

        # API Index 40 (Python index 39): Wartość ByPassu
        if self._index == 39:
            bypass_status = {
                0: "Zamknięty (ręcznie)", 1: "Otwarty (ręcznie)",
                2: "Zamknięty (auto)", 3: "Otwarty (auto)",
            }
            return bypass_status.get(value)

        # API Index 72 (Python index 71): Detekcja wilgotności
        if self._index == 71:
            return {0: "Nieaktywna", 1: "Aktywna"}.get(value)

        # API Index 73 (Python index 72): Status nagrzewnicy wstępnej
        if self._index == 72:
            return {0: "Nieaktywna", 1: "Aktywna"}.get(value)

        # API Index 87 (Python index 86): Typ montażu
        if self._index == 86:
            types = {1: "Lewy", 2: "Prawy"}
            return types.get(value)

        return value