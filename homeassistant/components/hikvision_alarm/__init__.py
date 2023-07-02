"""The hikvision_axpro integration."""
import asyncio
import logging

from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import const
from .websockets import async_register_websockets
from .hikax import HikAx
from .store import AlarmoStorage
from .coordinator import HikAlarmDataUpdateCoordinator
from .entity import device_registry

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Set up the hikvision_axpro integration component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hikvision_axpro from a config entry."""
    if entry.data.get(const.CONF_HIK_ENABLE_DEBUG_OUTPUT):
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.NOTSET)

    _LOGGER.debug("async_setup_entry de init")

    store = AlarmoStorage(hass)

    axpro = HikAx(entry.data[const.CONF_HIK_HOST], entry.data[const.CONF_HIK_USERNAME], entry.data[const.CONF_HIK_PASSWORD])

    coordinator = HikAlarmDataUpdateCoordinator(store, hass, axpro, entry)

    _LOGGER.debug("Antes del init device y 10seg timeout")

    try:
        async with timeout(10):
            await hass.async_add_executor_job(coordinator.init_device)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    _LOGGER.debug("Despues del init device, y ahora registramos el device")

    hass.data.setdefault(const.DOMAIN, {})
    hass.data[const.DOMAIN][entry.entry_id] = {const.DATA_COORDINATOR: coordinator, const.DATA_AREAS: {}, const.DATA_MASTER: None}

    await coordinator.async_update_config()
    device_registry(hass, entry)

    # if entry.unique_id is None:
    # hass.config_entries.async_update_entry(entry, unique_id=coordinator.id, data={})

    await hass.config_entries.async_forward_entry_setups(entry, const.PLATFORMS)

    # Websocket support
    await async_register_websockets(hass)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry de init")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, const.PLATFORMS)

    if not unload_ok:
        return False

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[const.DOMAIN][entry.entry_id][const.DATA_COORDINATOR]
    await coordinator.async_unload()

    hass.data[const.DOMAIN].pop(entry.entry_id)

    return True


async def async_remove_entry(hass, entry):
    """Remove Alarmo config entry."""
    _LOGGER.debug("async_remove_entry de init")

    coordinator: HikAlarmDataUpdateCoordinator = hass.data[const.DOMAIN][entry.entry_id][const.DATA_COORDINATOR]
    await coordinator.async_delete_config()

    del hass.data[const.DOMAIN]


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener."""
    _LOGGER.debug("update_listener de init")

    await hass.config_entries.async_reload(config_entry.entry_id)
