"""The hikvision_axpro integration."""
import asyncio
import logging

from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    DATA_COORDINATOR,
    CONF_HIK_SERVER_CONFIG,
    CONF_HIK_HOST,
    CONF_HIK_USERNAME,
    CONF_HIK_PASSWORD,
    CONF_HIK_ENABLE_DEBUG_OUTPUT,
    DATA_AREAS,
    DATA_MASTER,
    PLATFORMS,
)
from .websockets import async_register_websockets
from .hikax import HikAx
from .store import AlarmoStorage
from .coordinator import HikAlarmDataUpdateCoordinator
from .entity import device_registry
from .automations import AutomationHandler
from .event import EventHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    if entry.data.get(CONF_HIK_ENABLE_DEBUG_OUTPUT):
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.NOTSET)

    _LOGGER.debug("async_setup_entry de init")

    store = AlarmoStorage(hass)
    axpro = HikAx(
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_HOST],
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_USERNAME],
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_PASSWORD],
    )

    coordinator = HikAlarmDataUpdateCoordinator(store, hass, axpro, entry)

    try:
        async with timeout(10):
            await hass.async_add_executor_job(coordinator.init_device)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_AREAS: {},
        DATA_MASTER: None,
    }

    hass.data[DOMAIN][entry.entry_id]["automation_handler"] = AutomationHandler(hass, entry.entry_id)
    hass.data[DOMAIN][entry.entry_id]["event_handler"] = EventHandler(hass, entry.entry_id)

    device_registry(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_register_websockets(hass)

    entry.add_update_listener(update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry de init")

    del hass.data[DOMAIN][entry.entry_id]["automation_handler"]
    del hass.data[DOMAIN][entry.entry_id]["event_handler"]

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_ok:
        return False

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    await coordinator.async_unload()

    hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update from config entry."""
    _LOGGER.debug("update_listener de init")

    if entry.data.get(CONF_HIK_ENABLE_DEBUG_OUTPUT):
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.NOTSET)

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    if entry.data[CONF_HIK_SERVER_CONFIG] != coordinator.entry.data[CONF_HIK_SERVER_CONFIG]:
        _LOGGER.debug("Se cambio la configuracion del servidor")

    coordinator.axpro = HikAx(
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_HOST],
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_USERNAME],
        entry.data[CONF_HIK_SERVER_CONFIG][CONF_HIK_PASSWORD],
    )

    try:
        async with timeout(10):
            await hass.async_add_executor_job(coordinator.init_device)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    await coordinator.async_update_config(entry)
