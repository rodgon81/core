from __future__ import annotations
from typing import cast
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from collections.abc import Callable, Coroutine
from homeassistant.components.sensor import SensorEntity, DOMAIN as SENSOR_DOMAIN, SensorEntityDescription, SensorDeviceClass
from dataclasses import dataclass

from . import HikAlarmDataUpdateCoordinator
from .const import PERCENTAGE, UnitOfTemperature, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, DOMAIN, DATA_COORDINATOR
from .model import Zone, Status
from .entity import HikZoneEntity, HikvisionAlarmEntity


@dataclass
class HikZoneSensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[Zone], None]
    domain: str


@dataclass
class HikZoneSensornDescription(SensorEntityDescription, HikZoneSensorDescriptionMixin):
    """Hikvision Alarm Button description."""


@dataclass
class HikAlarmSensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[HikAlarmDataUpdateCoordinator], None]
    domain: str


@dataclass
class HikAlarmSensornDescription(SensorEntityDescription, HikAlarmSensorDescriptionMixin):
    """Hikvision Alarm Button description."""


SENSORS_ZONE = {
    "status": HikZoneSensornDescription(
        key="status",
        translation_key="status",
        value_fn=lambda data: cast(str, data.status.value),
        domain=SENSOR_DOMAIN,
    ),
    "zone_type": HikZoneSensornDescription(
        key="zone_type",
        icon="mdi:signal",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="zone_type",
        value_fn=lambda data: cast(str, data.zone_type.value),
        domain=SENSOR_DOMAIN,
    ),
    "signal": HikZoneSensornDescription(
        key="signal",
        icon="mdi:signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda data: cast(float, data.signal),
        domain=SENSOR_DOMAIN,
    ),
    "humidity": HikZoneSensornDescription(
        key="humidity",
        icon="mdi:cloud-percent",
        native_unit_of_measurement=PERCENTAGE,
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        value_fn=lambda data: cast(float, data.humidity),
        domain=SENSOR_DOMAIN,
    ),
    "temperature": HikZoneSensornDescription(
        key="temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: cast(float, data.temperature),
        domain=SENSOR_DOMAIN,
    ),
    "battery": HikZoneSensornDescription(
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

SENSORS_ALARM: tuple[HikAlarmSensornDescription, ...] = (
    HikAlarmSensornDescription(
        key="battery_state",
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="battery_state",
        value_fn=lambda coordinator: cast(str, coordinator.batery_state),
        domain=SENSOR_DOMAIN,
    ),
    HikAlarmSensornDescription(
        key="device_mac",
        icon="mdi:network",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="device_mac",
        value_fn=lambda coordinator: cast(str, coordinator.device_mac),
        domain=SENSOR_DOMAIN,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Hikvision ax pro alarm control panel based on a config entry."""

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    @callback
    def async_add_alarm_zone_sensor_entity(zone: Zone, type: str):
        sensor_entity = HikZoneSensor(coordinator, zone, SENSORS_ZONE[type])

        async_add_entities([sensor_entity])

    async_dispatcher_connect(hass, "hik_register_zone_sensor", async_add_alarm_zone_sensor_entity)

    @callback
    def async_add_alarm_entity_binary_sensor_entity():
        async_add_entities(HikAlarmSensor(coordinator, description) for description in SENSORS_ALARM)

    async_dispatcher_connect(hass, "hik_register_alarm_sensor", async_add_alarm_entity_binary_sensor_entity)

    async_dispatcher_send(hass, "hik_sensor_platform_loaded")


class HikZoneSensor(HikZoneEntity, SensorEntity):
    """Representation of Hikvision external magnet detector."""

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, zone: Zone, entity_description: HikAlarmSensornDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.entity_description: HikAlarmSensornDescription = entity_description

        super().__init__(coordinator, zone.id, self.entity_description.key, self.entity_description.domain)

    @property
    def icon(self) -> str | None:
        if self.entity_description.key == "status":
            if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
                value = self.entity_description.value_fn(self.coordinator.zones[self.zone_id])

                if value == Status.OFFLINE.value:
                    return "mdi:signal-off"
                if value == Status.NOT_RELATED.value:
                    return "mdi:help"
                if value == Status.ONLINE.value:
                    return "mdi:access-point-check"
                if value == Status.TRIGGER.value:
                    return "mdi:alarm-light"
                if value == Status.BREAK_DOWN.value:
                    return "mdi:image-broken-variant"
                if value == Status.HEART_BEAT_ABNORMAL.value:
                    return "mdi:heart-broken"

                else:
                    return self.entity_description.icon
            else:
                return self.entity_description.icon
        else:
            return self.entity_description.icon

    @property
    def native_value(self) -> StateType:
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            return self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
        else:
            return None


class HikAlarmSensor(HikvisionAlarmEntity, SensorEntity):
    """Representation of Hikvision external magnet detector."""

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, entity_description: HikAlarmSensornDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.entity_description: HikAlarmSensornDescription = entity_description

        super().__init__(coordinator, self.entity_description.key)

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator)
