from __future__ import annotations
from typing import cast
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from collections.abc import Callable
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, DOMAIN as BINARY_SENSOR_DOMAIN, BinarySensorEntityDescription
from dataclasses import dataclass

from .coordinator import HikAlarmDataUpdateCoordinator
from .const import DOMAIN, DATA_COORDINATOR
from .model import ZoneStatus
from .entity import HikGroupEntity, HikAlarmEntity


@dataclass
class HikZoneBinarySensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[ZoneStatus], None]
    domain: str


@dataclass
class HikZoneBinarySensorDescription(BinarySensorEntityDescription, HikZoneBinarySensorDescriptionMixin):
    """Hikvision Alarm Button description."""


@dataclass
class HikAlarmBinarySensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[HikAlarmDataUpdateCoordinator], None]
    domain: str


@dataclass
class HikAlarmBinarySensorDescription(BinarySensorEntityDescription, HikAlarmBinarySensorDescriptionMixin):
    """Hikvision Alarm Button description."""


BINARY_SENSORS_ZONE = {
    "tamper_evident": HikZoneBinarySensorDescription(
        key="tamper_evident",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="tamper_evident",
        device_class=BinarySensorDeviceClass.TAMPER,
        value_fn=lambda data: cast(bool, data.tamper_evident),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "shielded": HikZoneBinarySensorDescription(
        key="shielded",
        icon="mdi:shield-lock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="shielded",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.shielded),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "bypassed": HikZoneBinarySensorDescription(
        key="bypassed",
        icon="mdi:alarm-light-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="bypassed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.bypassed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "armed": HikZoneBinarySensorDescription(
        key="armed",
        icon="mdi:lock",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="armed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.armed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "alarm": HikZoneBinarySensorDescription(
        key="alarm",
        icon="mdi:alarm-light",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.alarm),
        domain=BINARY_SENSOR_DOMAIN,
    ),
}

BINARY_SENSORS_ALARM: tuple[HikAlarmBinarySensorDescription, ...] = (
    HikAlarmBinarySensorDescription(
        key="wifi_state",
        translation_key="wifi_state",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: cast(bool, coordinator.wifi_state),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    HikAlarmBinarySensorDescription(
        key="movile_net_state",
        translation_key="movile_net_state",
        icon="mdi:broadcast",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: cast(bool, coordinator.movile_net_state),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    HikAlarmBinarySensorDescription(
        key="ethernet_state",
        translation_key="ethernet_state",
        icon="mdi:ethernet",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: cast(bool, coordinator.ethernet_state),
        domain=BINARY_SENSOR_DOMAIN,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Hikvision ax pro alarm control panel based on a config entry."""

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    @callback
    def async_add_alarm_zone_binary_sensor_entity(zone_status: ZoneStatus, type: str):
        binary_sensor_entity = HikZoneBinarySensor(coordinator, zone_status, BINARY_SENSORS_ZONE[type])

        async_add_entities([binary_sensor_entity])

    async_dispatcher_connect(hass, "hik_register_zone_binary_sensor", async_add_alarm_zone_binary_sensor_entity)

    @callback
    def async_add_alarm_entity_binary_sensor_entity():
        async_add_entities(HikAlarmBinarySensor(coordinator, entity_description) for entity_description in BINARY_SENSORS_ALARM)

    async_dispatcher_connect(hass, "hik_register_alarm_binary_sensor", async_add_alarm_entity_binary_sensor_entity)

    async_dispatcher_send(hass, "hik_binary_sensor_platform_loaded")


class HikZoneBinarySensor(HikGroupEntity, BinarySensorEntity):
    """Representation of Hikvision tamper_evident detection."""

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, zone_status: ZoneStatus, entity_description: HikZoneBinarySensorDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""

        self.entity_description: HikZoneBinarySensorDescription = entity_description

        super().__init__(coordinator, zone_status.id, self.entity_description.key, self.entity_description.domain, "zone")

    @property
    def icon(self) -> str | None:
        return self.entity_description.icon

        """Return the icon to use in the frontend, if any."""
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            value = self.entity_description.value_fn(self.coordinator.zones[self.zone_id])

            if value is True:
                return "mdi:magnet-on"
            else:
                return "mdi:magnet"
        else:
            return "mdi:help"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            return self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
        else:
            return None


class HikAlarmBinarySensor(HikAlarmEntity, BinarySensorEntity):
    """Representation of a Hikvision Alarm button."""

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, entity_description: HikAlarmBinarySensorDescription):
        self.entity_description: HikAlarmBinarySensorDescription = entity_description

        super().__init__(coordinator, entity_description.key, self.entity_description.domain)

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""

        return self.entity_description.value_fn(self.coordinator)
