from __future__ import annotations

from typing import cast
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from collections.abc import Callable
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, DOMAIN as BINARY_SENSOR_DOMAIN, BinarySensorEntityDescription, STATE_ON, STATE_OFF
from dataclasses import dataclass

from . import HikAxProDataUpdateCoordinator
from . import const
from .model import Zone
from .entity import HikZoneEntity, HikvisionAlarmEntity


@dataclass
class HikAlarmBinarySensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    value_fn: Callable[[Zone], None]
    domain: str


@dataclass
class HikAlarmBinarySensornDescription(BinarySensorEntityDescription, HikAlarmBinarySensorDescriptionMixin):
    """Hikvision Alarm Button description."""


@dataclass
class xxHikAlarmBinarySensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    domain: str


@dataclass
class xxHikAlarmBinarySensornDescription(BinarySensorEntityDescription, xxHikAlarmBinarySensorDescriptionMixin):
    """Hikvision Alarm Button description."""


BINARY_SENSORS_ZONE = {
    "tamper_evident": HikAlarmBinarySensornDescription(
        key="tamper_evident",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="tamper_evident",
        device_class=BinarySensorDeviceClass.TAMPER,
        value_fn=lambda data: cast(bool, data.tamper_evident),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "shielded": HikAlarmBinarySensornDescription(
        key="shielded",
        icon="mdi:shield-lock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="shielded",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.shielded),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "bypassed": HikAlarmBinarySensornDescription(
        key="bypassed",
        icon="mdi:alarm-light-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="bypassed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.bypassed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "armed": HikAlarmBinarySensornDescription(
        key="armed",
        icon="mdi:lock",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="armed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.armed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "alarm": HikAlarmBinarySensornDescription(
        key="alarm",
        icon="mdi:alarm-light",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: cast(bool, data.alarm),
        domain=BINARY_SENSOR_DOMAIN,
    ),
}

BINARY_SENSORS: tuple[xxHikAlarmBinarySensornDescription, ...] = (
    xxHikAlarmBinarySensornDescription(
        key="reload_hikvision",
        translation_key="reload_hikvision",
        icon="mdi:reload",
        entity_category=EntityCategory.CONFIG,
        domain=BINARY_SENSOR_DOMAIN,
    ),
    xxHikAlarmBinarySensornDescription(
        key="test",
        translation_key="test",
        icon="mdi:reload",
        entity_category=EntityCategory.CONFIG,
        domain=BINARY_SENSOR_DOMAIN,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up a Hikvision ax pro alarm control panel based on a config entry."""

    coordinator: HikAxProDataUpdateCoordinator = hass.data[const.DOMAIN][entry.entry_id][const.DATA_COORDINATOR]

    @callback
    def async_add_alarm_zone_binary_sensor_entity(zone: Zone, type: str):
        binary_sensor_entity = HikBinarySensor(coordinator, zone, BINARY_SENSORS_ZONE[type])

        async_add_entities([binary_sensor_entity])

    async_dispatcher_connect(hass, "alarmo_register_zone_binary_sensor_entity", async_add_alarm_zone_binary_sensor_entity)

    @callback
    def async_add_alarm_entity_binary_sensor_entity():
        async_add_entities(HikAlarmBinarySensor(coordinator, description) for description in BINARY_SENSORS)

    async_dispatcher_connect(hass, "alarmo_register_entity_binary_sensor_entity", async_add_alarm_entity_binary_sensor_entity)

    async_dispatcher_send(hass, "hik_binary_sensor_platform_loaded")


class HikBinarySensor(HikZoneEntity, BinarySensorEntity):
    """Representation of Hikvision tamper_evident detection."""

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator, zone: Zone, entity_description: HikAlarmBinarySensornDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""

        self.entity_description: HikAlarmBinarySensornDescription = entity_description

        super().__init__(coordinator, zone.id, self.entity_description.key, self.entity_description.domain)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            value = self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
            if value is True:
                self._attr_icon = "mdi:magnet-on"
            else:
                self._attr_icon = "mdi:magnet"
        else:
            self._attr_icon = "mdi:help"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            value = self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
            self._attr_state = STATE_ON if value is True else STATE_OFF
        else:
            self._attr_state = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.zones and self.coordinator.zones[self.zone_id]:
            return self.entity_description.value_fn(self.coordinator.zones[self.zone_id])
        else:
            return False


class HikAlarmBinarySensor(HikvisionAlarmEntity, BinarySensorEntity):
    """Representation of a Hikvision Alarm button."""

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator, description: xxHikAlarmBinarySensornDescription):
        self.entity_description: xxHikAlarmBinarySensornDescription = description

        super().__init__(coordinator, description.key)
