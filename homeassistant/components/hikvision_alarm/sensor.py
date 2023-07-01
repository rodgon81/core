from __future__ import annotations

from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from collections.abc import Callable
from homeassistant.components.sensor import SensorEntity, DOMAIN as SENSOR_DOMAIN, SensorEntityDescription, SensorDeviceClass, SensorStateClass
from dataclasses import dataclass

from . import HikAxProDataUpdateCoordinator
from .const import PERCENTAGE, UnitOfTemperature, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, DOMAIN, DATA_COORDINATOR
from .model import Zone, Status
from .entity import HikZoneEntity


@dataclass
class HikAlarmSensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[Zone], None]
    domain: str


@dataclass
class HikAlarmSensornDescription(SensorEntityDescription, HikAlarmSensorDescriptionMixin):
    """Hikvision Alarm Button description."""


SENSORS = {
    "status": HikAlarmSensornDescription(
        key="status",
        translation_key="status",
        value_fn=lambda data: cast(str, data.status.value),
        domain=SENSOR_DOMAIN,
    ),
    "zone_type": HikAlarmSensornDescription(
        key="zone_type",
        icon="mdi:signal",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="zone_type",
        value_fn=lambda data: cast(str, data.zone_type.value),
        domain=SENSOR_DOMAIN,
    ),
    "signal": HikAlarmSensornDescription(
        key="signal",
        icon="mdi:signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda data: cast(float, data.signal),
        domain=SENSOR_DOMAIN,
    ),
    "humidity": HikAlarmSensornDescription(
        key="humidity",
        icon="mdi:cloud-percent",
        native_unit_of_measurement=PERCENTAGE,
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        value_fn=lambda data: cast(float, data.humidity),
        domain=SENSOR_DOMAIN,
    ),
    "temperature": HikAlarmSensornDescription(
        key="temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: cast(float, data.temperature),
        domain=SENSOR_DOMAIN,
    ),
    "battery": HikAlarmSensornDescription(
        key="battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        value_fn=lambda data: cast(float, data.charge_value),
        domain=SENSOR_DOMAIN,
    ),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Hikvision ax pro alarm control panel based on a config entry."""

    coordinator: HikAxProDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    @callback
    def async_add_alarm_zone_sensor_entity(zone: Zone, type: str):
        sensor_entity = HikSensor(coordinator, zone, SENSORS[type])

        async_add_entities([sensor_entity])

    async_dispatcher_connect(hass, "alarmo_register_zone_sensor_entity", async_add_alarm_zone_sensor_entity)

    async_dispatcher_send(hass, "hik_sensor_platform_loaded")


class HikSensor(HikZoneEntity, SensorEntity):
    """Representation of Hikvision external magnet detector."""

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator, zone: Zone, entity_description: HikAlarmSensornDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.entity_description: HikAlarmSensornDescription = entity_description

        super().__init__(coordinator, zone.id, self.entity_description.key, self.entity_description.domain)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if self._attr_native_value is not None:
            if self._attr_native_value == Status.OFFLINE.value:
                return "mdi:signal-off"
            if self._attr_native_value == Status.NOT_RELATED.value:
                return "mdi:help"
            if self._attr_native_value == Status.ONLINE.value:
                return "mdi:access-point-check"
            if self._attr_native_value == Status.TRIGGER.value:
                return "mdi:alarm-light"
            if self._attr_native_value == Status.BREAK_DOWN.value:
                return "mdi:image-broken-variant"
            if self._attr_native_value == Status.HEART_BEAT_ABNORMAL.value:
                return "mdi:heart-broken"
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            return self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
        else:
            return None
