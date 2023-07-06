from __future__ import annotations
from typing import cast, Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from collections.abc import Callable, Coroutine
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchEntity, SwitchEntityDescription, SwitchDeviceClass
from dataclasses import dataclass

from .coordinator import HikAlarmDataUpdateCoordinator
from .const import DOMAIN, DATA_COORDINATOR
from .model import RelayStatus
from .entity import HikGroupEntity


@dataclass
class HikZoneSensorDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    is_on_fn: Callable[[RelayStatus], None]
    turn_on_fn: Callable[[HikAlarmDataUpdateCoordinator], Coroutine]
    turn_off_fn: Callable[[HikAlarmDataUpdateCoordinator], Coroutine]
    domain: str


@dataclass
class HikGroupSwitchDescription(SwitchEntityDescription, HikZoneSensorDescriptionMixin):
    """Hikvision Alarm Button description."""


SWITCH_ZONE = {
    "relay_state": HikGroupSwitchDescription(
        key="relay_state",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="relay_state",
        device_class=SwitchDeviceClass.SWITCH,
        is_on_fn=lambda data: cast(bool, data.status),
        turn_on_fn=lambda coordinator: coordinator.set_state_relay(True, 1),
        turn_off_fn=lambda coordinator: coordinator.set_state_relay(False, 1),
        domain=SWITCH_DOMAIN,
    ),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up discovered switches."""
    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    @callback
    def async_add_alarm_zone_switch_entity(relay_status: RelayStatus, type: str):
        binary_sensor_entity = HikZoneSwitch(coordinator, relay_status, SWITCH_ZONE[type])

        async_add_entities([binary_sensor_entity])

    async_dispatcher_connect(hass, "hik_register_relay_switch", async_add_alarm_zone_switch_entity)

    async_dispatcher_send(hass, "hik_switch_platform_loaded")


class HikZoneSwitch(HikGroupEntity, SwitchEntity):
    """Representation of a switch."""

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, relay_status: RelayStatus, entity_description: HikGroupSwitchDescription) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.entity_description: HikGroupSwitchDescription = entity_description

        super().__init__(coordinator, relay_status.id, self.entity_description.key, self.entity_description.domain, "relay")

    @property
    def is_on(self) -> bool:
        """Return whether the switch is on or not."""
        return self.entity_description.is_on_fn(self.coordinator.relay_status[self.zone_id])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""

        await self.entity_description.turn_off_fn(self.coordinator)  # ()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""

        await self.entity_description.turn_on_fn(self.coordinator)  # ()
