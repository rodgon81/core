from __future__ import annotations

import logging
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr
from collections.abc import Callable
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, DOMAIN as BINARY_SENSOR_DOMAIN, BinarySensorEntityDescription, STATE_ON, STATE_OFF
from dataclasses import dataclass
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send


from . import HikAxProDataUpdateCoordinator
from . import const
from .model import DetectorType, Zone, detector_model_to_name
from .entity import HikZoneEntity, HikvisionAlarmEntity

_LOGGER = logging.getLogger(__name__)


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
    "magnet_presence": HikAlarmBinarySensornDescription(
        key="magnet_presence",
        icon="mdi:magnet",
        translation_key="magnet_presence",
        device_class=BinarySensorDeviceClass.PRESENCE,
        value_fn=lambda data: cast(bool, data.magnet_open_status),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "tamper_evident": HikAlarmBinarySensornDescription(
        key="tamper_evident",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="tamper_evident",
        device_class=BinarySensorDeviceClass.TAMPER,
        value_fn=lambda data: cast(bool, data.tamper_evident),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "bypassed": HikAlarmBinarySensornDescription(
        key="bypassed",
        icon="mdi:alarm-light-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="bypassed",
        device_class=BinarySensorDeviceClass.SAFETY,
        value_fn=lambda data: cast(bool, data.bypassed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "armed": HikAlarmBinarySensornDescription(
        key="armed",
        icon="mdi:lock",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="armed",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda data: cast(bool, data.armed),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "alarm": HikAlarmBinarySensornDescription(
        key="alarm",
        icon="mdi:alarm-light",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda data: cast(bool, data.alarm),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "stay_away": HikAlarmBinarySensornDescription(
        key="stay_away",
        icon="mdi:shield-lock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="stay_away",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda data: cast(bool, data.stay_away),
        domain=BINARY_SENSOR_DOMAIN,
    ),
    "is_via_repeater": HikAlarmBinarySensornDescription(
        key="is_via_repeater",
        icon="mdi:google-circles-extended",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="is_via_repeater",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: cast(bool, data.is_via_repeater),
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
    def async_add_alarm_zone_binary_sensor_entity():
        devices = []

        # await coordinator.async_request_refresh()

        if coordinator.zone_status is not None:
            for zone in coordinator.zone_status.zone_list:
                zone_config = coordinator.devices.get(zone.zone.id)

                # _LOGGER.debug("Adding device with zone config: %s", zone)
                # _LOGGER.debug("+ config: %s", zone_config)

                device_registry = dr.async_get(hass)
                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers={(const.DOMAIN, str(entry.entry_id) + "-" + str(zone_config.id))},
                    manufacturer="HikVision",
                    name=zone_config.zone_name,
                    via_device=(const.DOMAIN, str(coordinator.id)),
                    model=detector_model_to_name(zone.zone.model),
                )

                detector_type: DetectorType | None
                detector_type = zone_config.detector_type

                # Specific entity
                if detector_type == DetectorType.WIRELESS_EXTERNAL_MAGNET_DETECTOR:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["magnet_presence"]))
                if detector_type == DetectorType.DOOR_MAGNETIC_CONTACT_DETECTOR or detector_type == DetectorType.SLIM_MAGNETIC_CONTACT or detector_type == DetectorType.MAGNET_SHOCK_DETECTOR:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["magnet_presence"]))

                if zone.zone.tamper_evident is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["tamper_evident"]))
                if zone.zone.bypassed is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["bypassed"]))
                if zone.zone.armed is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["armed"]))
                if zone.zone.alarm is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["alarm"]))
                if zone.zone.stay_away is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["stay_away"]))
                if zone.zone.is_via_repeater is not None:
                    devices.append(HikBinarySensor(coordinator, zone.zone, BINARY_SENSORS_ZONE["is_via_repeater"]))

        # _LOGGER.debug("devices: %s", devices)
        async_add_entities(devices, False)

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

        super().__init__(coordinator, zone, self.entity_description.key, self.entity_description.domain)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if self.coordinator.zones and self.coordinator.zones[self.zone.id]:
            value = self.entity_description.value_fn(self.coordinator.zones[self.zone.id])
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

        if self.coordinator.zones and self.coordinator.zones[self.zone.id]:
            value = self.entity_description.value_fn(self.coordinator.zones[self.zone.id])
            self._attr_state = STATE_ON if value is True else STATE_OFF
        else:
            self._attr_state = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.zones and self.coordinator.zones[self.zone.id]:
            return self.entity_description.value_fn(self.coordinator.zones[self.zone.id])
        else:
            return False


class HikAlarmBinarySensor(HikvisionAlarmEntity, BinarySensorEntity):
    """Representation of a Hikvision Alarm button."""

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator, description: xxHikAlarmBinarySensornDescription):
        self.entity_description: xxHikAlarmBinarySensornDescription = description

        super().__init__(coordinator, description.key)
