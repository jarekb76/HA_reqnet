"""Number platform for the Reqnet integration."""
from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfVolumeFlowRate

from .coordinator import ReqnetDataCoordinator

MANUAL_AIRFLOW_INDEX = 5
MANUAL_EXTRACTION_INDEX = 6


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry[ReqnetDataCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the manual airflow number entities."""
    del _hass
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            ReqnetManualFlowNumber(
                coordinator,
                index=MANUAL_AIRFLOW_INDEX,
                key="manual_airflow",
                name="Zadany nawiew",
            ),
            ReqnetManualFlowNumber(
                coordinator,
                index=MANUAL_EXTRACTION_INDEX,
                key="manual_extraction",
                name="Zadany wyciąg",
            ),
        ]
    )


class ReqnetManualFlowNumber(
    CoordinatorEntity[ReqnetDataCoordinator], NumberEntity
):
    """Set one of the manual airflow values."""

    _attr_has_entity_name = True
    _attr_device_class = NumberDeviceClass.VOLUME_FLOW_RATE
    _attr_native_min_value = 0
    _attr_native_max_value = 350
    _attr_native_step = 10
    _attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: ReqnetDataCoordinator,
        *,
        index: int,
        key: str,
        name: str,
    ) -> None:
        """Initialize the manual airflow number."""
        super().__init__(coordinator)
        self._index = index
        self._attr_unique_id = f"{coordinator.mac_address.lower()}_{key}"
        self._attr_name = name
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return the current manual airflow value."""
        data = self.coordinator.data
        if (
            not isinstance(data, list)
            or len(data) <= self._index
            or data[self._index] is None
        ):
            return None
        return float(data[self._index])

    @property
    def available(self) -> bool:
        """Return whether the current value is available."""
        return self.coordinator.last_update_success and self.native_value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set this airflow value and preserve the other current value."""
        if self._index == MANUAL_AIRFLOW_INDEX:
            success = await self.coordinator.async_set_manual_mode(
                airflow_value=int(value)
            )
        else:
            success = await self.coordinator.async_set_manual_mode(
                air_extraction_value=int(value)
            )

        if not success:
            raise HomeAssistantError("Nie udało się ustawić wartości przepływu")