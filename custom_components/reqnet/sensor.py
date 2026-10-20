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
# (index_python (API_Index - 1), translation_key, jednostka, ikona, klasa_urządzenia, kategoria_encji)
SENSOR_DEFINITIONS: list[tuple[int, str, str | None, str | None, SensorDeviceClass | None, EntityCategory | None]] = [
    # --- Podstawowe odczyty ---
    (0, "device_status", None, "mdi:power", SensorDeviceClass.ENUM, None), # API Index 1
    (1, "max_supply_flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-plus", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 2
    (2, "current_temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, None), # API Index 3
    (3, "current_supply_flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 4
    (4, "current_extraction_flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-off", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 5
    (5, "supply_manual_mode", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-settings", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 6
    (6, "extraction_manual_mode", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, "mdi:fan-settings", SensorDeviceClass.VOLUME_FLOW_RATE, None), # API Index 7
    (7, "humidity", UnitOfRatio.PERCENTAGE, "mdi:water-percent", SensorDeviceClass.HUMIDITY, None), # API Index 8
    (8, "co2_level", UnitOfRatio.PARTS_PER_MILLION, "mdi:molecule-co2", SensorDeviceClass.CO2, None), # API Index 9
    (9, "schedule_status", None, "mdi:calendar-clock", SensorDeviceClass.ENUM, None), # API Index 10 (0/1)
    (10, "operation_mode", None, "mdi:cog-outline", SensorDeviceClass.ENUM, None), # API Index 11 (mapowane wartości)
    (13, "heating_cooling_status", None, "mdi:thermostat", SensorDeviceClass.ENUM, None), # API Index 14 (0/1/2)
    (15, "device_model", None, "mdi:information-outline", None, EntityCategory.DIAGNOSTIC), # API Index 16

    # --- Temperatury szczegółowe ---
    (55, "intake_temperature", UnitOfTemperature.CELSIUS, "mdi:export", SensorDeviceClass.TEMPERATURE, None), # API Index 56
    (56, "exhaust_duct_temperature", UnitOfTemperature.CELSIUS, "mdi:import", SensorDeviceClass.TEMPERATURE, None), # API Index 57
    (57, "supply_temperature", UnitOfTemperature.CELSIUS, "mdi:coolant-temperature", SensorDeviceClass.TEMPERATURE, None), # API Index 58
    (58, "extraction_temperature", UnitOfTemperature.CELSIUS, "mdi:coolant-temperature", SensorDeviceClass.TEMPERATURE, None), # API Index 59
    (59, "temperature_after_heater_cooler", UnitOfTemperature.CELSIUS, "mdi:thermometer-lines", SensorDeviceClass.TEMPERATURE, None), # API Index 60
    (60, "gwc_temperature", UnitOfTemperature.CELSIUS, "mdi:sun-thermometer-outline", SensorDeviceClass.TEMPERATURE, None), # API Index 61
    (61, "room_temperature", UnitOfTemperature.CELSIUS, "mdi:home-thermometer-outline", SensorDeviceClass.TEMPERATURE, None), # API Index 62
    (62, "additional_sensor_temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer-alert", SensorDeviceClass.TEMPERATURE, None), # API Index 63

    # --- Ciśnienia/Opory ---
    (63, "supply_duct_resistance", UnitOfPressure.PA, "mdi:gauge-low", SensorDeviceClass.PRESSURE, None), # API Index 64
    (64, "extraction_duct_resistance", UnitOfPressure.PA, "mdi:gauge-low", SensorDeviceClass.PRESSURE, None), # API Index 65
    (75, "supply_pressure", UnitOfPressure.PA, "mdi:arrow-down-bold-pressure-outline", SensorDeviceClass.PRESSURE, None),  # API Index 76 (zakładam Pa)
    (76, "extraction_pressure", UnitOfPressure.PA, "mdi:arrow-up-bold-pressure-outline", SensorDeviceClass.PRESSURE, None), # API Index 77 (zakładam Pa)
    # --- Statusy i inne ---
    (39, "bypass_status", None, "mdi:compare-horizontal", SensorDeviceClass.ENUM, None), # API Index 40 (mapowane wartości)
    (40, "error_code", None, "mdi:alert-circle-outline", None, EntityCategory.DIAGNOSTIC), # API Index 41
    (41, "message_code", None, "mdi:information-outline", None, EntityCategory.DIAGNOSTIC), # API Index 42
    (71, "humidity_detection", None, "mdi:water-check-outline", SensorDeviceClass.ENUM, None), # API Index 72 (0/1)
    (72, "preheater_status", None, "mdi:radiator", SensorDeviceClass.ENUM, None), # API Index 73 (0/1)
    (73, "antifreeze_system_status", None, "mdi:snowflake-melt", None, None), # API Index 74
    (74, "condensation_system_status", None, "mdi:water-boiler-alert", None, None), # API Index 75
    (83, "filter_days_until_replacement", UnitOfTime.DAYS, "mdi:air-filter", SensorDeviceClass.DURATION, None), # API Index 84
    (86, "mount_type", None, "mdi:tools", SensorDeviceClass.ENUM, EntityCategory.DIAGNOSTIC), # API Index 87 (1-lewy, 2-prawy)
    (92, "overpressure_coefficient", UnitOfRatio.PERCENTAGE, "mdi:arrow-expand-all", None, None), # API Index 93

    # --- Wentylatory ---
    (65, "supply_fan_speed", UnitOfRatio.PERCENTAGE, "mdi:fan-chevron-up", None, None), # API Index 66
    (66, "extraction_fan_speed", UnitOfRatio.PERCENTAGE, "mdi:fan-chevron-down", None, None), # API Index 67
    (81, "supply_fan_power", UnitOfPower.WATT, "mdi:lightning-bolt", SensorDeviceClass.POWER, None), # API Index 82
    (82, "extraction_fan_power", UnitOfPower.WATT, "mdi:lightning-bolt", SensorDeviceClass.POWER, None), # API Index 83

    # --- Ustawienia ---
    (67, "comfort_temperature_setpoint", UnitOfTemperature.CELSIUS, "mdi:thermostat-box", SensorDeviceClass.TEMPERATURE, None), # API Index 68
    (69, "co2_sensitivity", None, "mdi:molecule-co2", None, None), # API Index 70 (jednostka nieznana z API)
    (70, "higro_sensitivity", None, "mdi:water-opacity", None, None), # API Index 71 (jednostka nieznana z API)

    # --- Wersje oprogramowania (diagnostyczne) ---
    (90, "firmware_version_major", None, "mdi:chip", None, EntityCategory.DIAGNOSTIC), # API Index 91
    (91, "firmware_version_build", None, "mdi:chip", None, EntityCategory.DIAGNOSTIC), # API Index 92
    (93, "firmware_version_wifi", None, "mdi:wifi", None, EntityCategory.DIAGNOSTIC), # API Index 94

    # --- Współczynniki wydajności dla funkcji (opcjonalne) ---
    # (16, "Wydajność Szybkie grzanie", UnitOfRatio.PERCENTAGE, "mdi:fire", None, None), # API Index 17
    # (17, "Wydajność Szybkie chłodzenie", UnitOfRatio.PERCENTAGE, "mdi:snowflake", None, None), # API Index 18
    # (18, "Wydajność Urlop", UnitOfRatio.PERCENTAGE, "mdi:palm-tree", None, None), # API Index 19
    # (19, "Wydajność Przewietrzanie", UnitOfRatio.PERCENTAGE, "mdi:weather-windy", None, None), # API Index 20
    # (20, "Wydajność Oczyszczanie", UnitOfRatio.PERCENTAGE, "mdi:air-purifier", None, None), # API Index 21
    # (21, "Wydajność Kominek", UnitOfRatio.PERCENTAGE, "mdi:fireplace", None, None), # API Index 22
]

SENSOR_OPTIONS: dict[int, list[str]] = {
    0: ["on", "off"],
    9: ["active", "inactive"],
    10: [
        "fast_heating",
        "fast_cooling",
        "vacation",
        "ventilation",
        "purification",
        "fireplace",
        "manual_mode",
        "intelligent_mode",
        "efficiency_measurement_mode",
        "unknown_mode",
    ],
    13: ["inactive", "heating", "cooling", "unknown_status"],
    39: [
        "closed_manual",
        "open_manual",
        "closed_auto",
        "open_auto",
        "unknown_status",
    ],
    71: ["active", "inactive"],
    72: ["active", "inactive"],
    86: ["left", "right", "unknown"],
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
    for index, translation_key, unit, icon, dev_class, entity_cat in SENSOR_DEFINITIONS:
        entities_to_add.append(
            ReqnetSensor(
                coordinator=coordinator,
                index=index,
                translation_key=translation_key,
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
        translation_key: str,
        unit: str | None,
        icon: str | None,
        device_class: SensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None, # POPRAWIONE TYPOWANIE
        options: list[str] | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._index = index

        self.entity_description = SensorEntityDescription(
            key=f"value_{self._index}",
            translation_key=translation_key,
            icon=icon,
            native_unit_of_measurement=unit,
            device_class=device_class,
            state_class=(
                SensorStateClass.MEASUREMENT
                if device_class not in (None, SensorDeviceClass.ENUM)
                else None
            ),
            entity_category=entity_category,
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
        self._attr_translation_placeholders = {}

        # Mapowanie wartości dla specyficznych sensorów
        # API Index 1 (Python index 0): Status urządzenia
        if self._index == 0:
            return "on" if value == 1 else "off"

        # API Index 10 (Python index 9): Status harmonogramu
        if self._index == 9:
            return "active" if value == 1 else "inactive"

        # API Index 11 (Python index 10): Tryb pracy
        if self._index == 10:
            modes = {
                1: "fast_heating", 2: "fast_cooling", 3: "vacation",
                4: "ventilation", 5: "purification", 6: "fireplace",
                8: "manual_mode", 9: "intelligent_mode", 10: "efficiency_measurement_mode",
            }
            if value in modes:
                return modes[value]
            self._attr_translation_placeholders = {"value": str(value)}
            return "unknown_mode"

        # API Index 14 (Python index 13): Status funkcji równoległej (grzanie/chłodzenie)
        if self._index == 13:
            statuses = {0: "inactive", 1: "heating", 2: "cooling"}
            if value in statuses:
                return statuses[value]
            self._attr_translation_placeholders = {"value": str(value)}
            return "unknown_status"

        # API Index 40 (Python index 39): Wartość ByPassu
        if self._index == 39:
            bypass_status = {
                0: "closed_manual", 1: "open_manual",
                2: "closed_auto", 3: "open_auto",
            }
            if value in bypass_status:
                return bypass_status[value]
            self._attr_translation_placeholders = {"value": str(value)}
            return "unknown_status"

        # API Index 72 (Python index 71): Detekcja wilgotności
        if self._index == 71:
            return "active" if value == 1 else "inactive"

        # API Index 73 (Python index 72): Status nagrzewnicy wstępnej
        if self._index == 72:
            return "active" if value == 1 else "inactive"

        # API Index 87 (Python index 86): Typ montażu
        if self._index == 86:
            types = {1: "left", 2: "right"}
            if value in types:
                return types[value]
            self._attr_translation_placeholders = {"value": str(value)}
            return "unknown"

        return value