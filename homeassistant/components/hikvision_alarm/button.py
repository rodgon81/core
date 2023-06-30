from __future__ import annotations
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from collections.abc import Callable, Coroutine
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from dataclasses import dataclass
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from . import HikAxProDataUpdateCoordinator
from .const import DOMAIN, DATA_COORDINATOR
from .entity import HikvisionAlarmEntity


@dataclass
class HikAlarmButtonDescriptionMixin:
    """Mixin to describe a Hikvision Alarm Button entity."""

    press_action: Callable[[HikAxProDataUpdateCoordinator], Coroutine]


@dataclass
class HikAlarmButtonDescription(ButtonEntityDescription, HikAlarmButtonDescriptionMixin):
    """Hikvision Alarm Button description."""


BUTTONS: tuple[HikAlarmButtonDescription, ...] = (
    HikAlarmButtonDescription(
        key="reload_hikvision",
        translation_key="reload_hikvision",
        icon="mdi:reload",
        entity_category=EntityCategory.CONFIG,
        press_action=lambda coordinator: coordinator.handle_reload(),
    ),
    HikAlarmButtonDescription(
        key="test",
        translation_key="test",
        icon="mdi:reload",
        entity_category=EntityCategory.CONFIG,
        press_action=lambda coordinator: coordinator.handle_reload(),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: HikAxProDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    @callback
    def async_add_alarm_button_entity():
        async_add_entities(HikAlarmButton(coordinator, description) for description in BUTTONS)

    async_dispatcher_connect(hass, "alarmo_register_zone_button_entity", async_add_alarm_button_entity)

    async_dispatcher_send(hass, "hik_button_platform_loaded")


class HikAlarmButton(HikvisionAlarmEntity, ButtonEntity):
    """Representation of a Hikvision Alarm button."""

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator, description: HikAlarmButtonDescription):
        self.entity_description: HikAlarmButtonDescription = description

        super().__init__(coordinator, description.key)

    async def async_press(self) -> None:
        await self.entity_description.press_action(self.coordinator)
