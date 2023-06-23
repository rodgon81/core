from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from . import HikAxProDataUpdateCoordinator
from .const import DATA_COORDINATOR, DOMAIN
from homeassistant.helpers import device_registry as dr

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: HikAxProDataUpdateCoordinator = hass.data[DOMAIN][DATA_COORDINATOR]

    async_add_entities(
        [NanoleafIdentifyButton(coordinator)]
    )


class NanoleafIdentifyButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Nanoleaf identify button."""

    coordinator: HikAxProDataUpdateCoordinator
    _attr_unique_id = f"boton_prueba_identify"
    _attr_name = f"Identify Boton Prueba"
    _attr_icon = "mdi:magnify"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: HikAxProDataUpdateCoordinator):
        super().__init__(coordinator=coordinator)
        self.coordinator = coordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)}
        )

    @property
    def unique_id(self):
        """Return a unique id."""
        return self.coordinator.mac

    @property
    def name(self):
        """Return the name."""
        return "boton tttttt"
        # "HikvisionAxPro"

    async def async_press(self) -> None:
        """Identify the Nanoleaf."""
        await self.coordinator.test_button()
