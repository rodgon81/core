"""The hikvision_axpro integration."""
import asyncio
import logging
import bcrypt
import base64

from datetime import timedelta
from typing import Optional
from collections.abc import Callable
from homeassistant.core import callback
from homeassistant.components.alarm_control_panel import CodeFormat, ATTR_CODE_ARM_REQUIRED, SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .hikax import HikAx
from async_timeout import timeout
from .store import async_get_registry, AlarmoStorage
from homeassistant.helpers import device_registry as dr
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CODE,
    ATTR_NAME,
    ATTR_CODE_FORMAT,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CODE,
    CONF_SCAN_INTERVAL,
    Platform,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
    SERVICE_RELOAD,
)

from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .model import ZonesResponse, Zone, SubSystemResponse, SubSys, Arming, ZonesConf, ZoneConfig
from .websockets import async_register_websockets
from . import const
from .event import EventHandler

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL, Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Set up the hikvision_axpro integration component."""
    hass.data.setdefault(const.DOMAIN, {})

    async def _handle_reload(service):
        """Handle reload service call."""
        _LOGGER.info(
            "Service %s.reload called: reloading integration", const.DOMAIN)

        current_entries = hass.config_entries.async_entries(const.DOMAIN)

        reload_tasks = [hass.config_entries.async_reload(
            entry.entry_id) for entry in current_entries]

        await asyncio.gather(*reload_tasks)

    hass.helpers.service.async_register_admin_service(
        const.DOMAIN,
        SERVICE_RELOAD,
        _handle_reload,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hikvision_axpro from a config entry."""
    store = await async_get_registry(hass)

    axpro = HikAx(entry.data[CONF_HOST],
                  entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    coordinator = HikAxProDataUpdateCoordinator(store, hass, axpro, entry)

    _LOGGER.debug("Antes del init device y 10seg timeout")

    try:
        async with timeout(10):
            await hass.async_add_executor_job(coordinator.init_device)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    _LOGGER.debug("Despues del init device, y ahora registramos el device")

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(const.DOMAIN, coordinator.id)},
        manufacturer=const.MANUFACTURER,
        name=coordinator.device_name,
        model=coordinator.device_model,
        sw_version=coordinator.firmware_version,
    )

    hass.data.setdefault(const.DOMAIN, {})
    hass.data[const.DOMAIN] = {
        const.DATA_COORDINATOR: coordinator, const.DATA_AREAS: {}, const.DATA_MASTER: None}

    await coordinator.async_update_config(entry.data)

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=coordinator.id, data={})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Websocket support
    await async_register_websockets(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[const.DOMAIN].pop(entry.entry_id)

    if not unload_ok:
        return False

    coordinator: HikAxProDataUpdateCoordinator = hass.data[const.DOMAIN][const.DATA_COORDINATOR]
    await coordinator.async_unload()

    return True


async def async_remove_entry(hass, entry):
    """Remove Alarmo config entry."""
    coordinator: HikAxProDataUpdateCoordinator = hass.data[const.DOMAIN][const.DATA_COORDINATOR]
    await coordinator.async_delete_config()
    del hass.data[const.DOMAIN]


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class HikAxProDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ax pro data."""
    axpro: HikAx
    zone_status: Optional[ZonesResponse]
    zones: Optional[dict[int, Zone]] = None
    device_model: Optional[str] = None
    device_name: Optional[str] = None
    sub_systems: dict[int, SubSys] = {}
    """ Zones aka devices """
    devices: dict[int, ZoneConfig] = {}
    id: Optional[str] = None
    firmware_version: Optional[str] = None
    firmware_released_date: Optional[str] = None

    store: AlarmoStorage
    hass: HomeAssistant
    entry: ConfigEntry

    def __init__(self, store, hass, axpro: HikAx, entry: ConfigEntry):
        _LOGGER.debug("__init__ HikAxProDataUpdateCoordinator")
        self.hass = hass
        self.store = store
        self.axpro = axpro
        self.state = None
        self.zone_status = None
        self.use_code_arming = entry.data[ATTR_CODE_ARM_REQUIRED]
        self.use_code_disarming = entry.data[const.ATTR_CODE_DISARM_REQUIRED]
        self.code = entry.data[ATTR_CODE_FORMAT]
        self._subscriptions = []
        self.entry = entry

        self._subscriptions.append(async_dispatcher_connect(
            hass, "alarmo_platform_loaded", self.setup_alarm_entities))

        update_interval: float = entry.data.get(
            CONF_SCAN_INTERVAL, SCAN_INTERVAL.total_seconds())

        super().__init__(hass, _LOGGER, name=const.DOMAIN,
                         update_interval=timedelta(seconds=update_interval))

    @callback
    def setup_alarm_entities(self):
        _LOGGER.debug("setup_alarm_entities")

        self.hass.data[const.DOMAIN]["event_handler"] = EventHandler(self.hass)

        areas = self.sub_systems  # self.store.async_get_areas()
        config = self.store.async_get_config()

        _LOGGER.debug("areas: %s", areas)
        _LOGGER.debug("config: %s", config)

        for item in areas.values():
            async_dispatcher_send(self.hass, "alarmo_register_entity", item)

        if len(areas) > 1 and config[const.ATTR_ENABLED]:
            async_dispatcher_send(self.hass, "alarmo_register_master", config)

    # llamado de websoket
    async def async_update_config(self, data: dict):
        if data.get(const.CONF_ENABLE_DEBUG_OUTPUT):
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.NOTSET)

        old_config = self.store.async_get_config()

        _LOGGER.debug("old_config: %s", old_config)
        _LOGGER.debug("data: %s", data)

        if old_config[const.ATTR_ENABLED] != data[const.ATTR_ENABLED] or old_config[const.ATTR_NAME] != data[const.ATTR_NAME]:
            if self.hass.data[const.DOMAIN][const.ATTR_MASTER]:
                await self.async_remove_entity(const.ATTR_MASTER)
            if data[const.ATTR_ENABLED]:
                async_dispatcher_send(
                    self.hass, "alarmo_register_master", data)

        self.store.async_update_config(data)
        async_dispatcher_send(self.hass, "alarmo_config_updated")

    # llamado de websoket
    async def async_update_area_config(self, area_id: str = None, data: dict = {}):
        if const.ATTR_REMOVE in data:
            # delete an area
            res = self.store.async_get_area(area_id)
            if not res:
                return
            sensors = self.store.async_get_sensors()
            sensors = dict(
                filter(lambda el: el[1]["area"] == area_id, sensors.items()))
            if sensors:
                for el in sensors.keys():
                    self.store.async_delete_sensor(el)
                async_dispatcher_send(self.hass, "alarmo_sensors_updated")

            self.store.async_delete_area(area_id)
            await self.async_remove_entity(area_id)

            if len(self.store.async_get_areas()) == 1 and self.hass.data[const.DOMAIN]["master"]:
                await self.async_remove_entity("master")

        elif self.store.async_get_area(area_id):
            # modify an area
            entry = self.store.async_update_area(area_id, data)
            if "name" not in data:
                async_dispatcher_send(
                    self.hass, "alarmo_config_updated", area_id)
            else:
                await self.async_remove_entity(area_id)
                async_dispatcher_send(
                    self.hass, "alarmo_register_entity", entry)
        else:
            # create an area
            entry = self.store.async_create_area(data)
            async_dispatcher_send(self.hass, "alarmo_register_entity", entry)

            config = self.store.async_get_config()

            if len(self.store.async_get_areas()) == 2 and config["master"]["enabled"]:
                async_dispatcher_send(
                    self.hass, "alarmo_register_master", config["master"])

    # llamado de websoket
    async def async_update_sensor_config(self, entity_id: str, data: dict):
        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor(entity_id)
        elif self.store.async_get_sensor(entity_id):
            self.store.async_update_sensor(entity_id, data)
        else:
            self.store.async_create_sensor(entity_id, data)

        async_dispatcher_send(self.hass, "alarmo_sensors_updated")

    # se llama desde panel alarma
    def async_authenticate_user(self, code: str, user_id: str = None):
        config = self.store.async_get_config()

        if config[ATTR_CODE] is not None:
            hash = base64.b64decode(config[ATTR_CODE])

            if bcrypt.checkpw(code.encode("utf-8"), hash):
                return True

        return False

    async def async_remove_entity(self, area_id: str):
        entity_registry = self.hass.helpers.entity_registry.async_get(
            self.hass)
        if area_id == "master":
            entity = self.hass.data[const.DOMAIN]["master"]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["master"] = None
        else:
            entity = self.hass.data[const.DOMAIN]["areas"][area_id]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["areas"].pop(area_id, None)

    async def async_unload(self):
        """remove all alarmo objects"""

        # remove alarm_control_panel entities
        areas = list(self.hass.data[const.DOMAIN]["areas"].keys())
        for area in areas:
            await self.async_remove_entity(area)
        if self.hass.data[const.DOMAIN]["master"]:
            await self.async_remove_entity("master")

        del self.hass.data[const.DOMAIN]["sensor_handler"]
        del self.hass.data[const.DOMAIN]["event_handler"]

        # remove subscriptions for coordinator
        while len(self._subscriptions):
            self._subscriptions.pop()()

    async def async_delete_config(self):
        """wipe alarmo storage"""
        await self.store.async_delete()

    # ------------------------------------------------

    def init_device(self):
        self.axpro.connect()
        self.load_device_info()
        self.load_zones()
        self._update_areas()
        self._update_zones()

    def load_device_info(self):
        device_info = self.axpro.get_device_info()

        if device_info is not None:
            self.id = device_info["DeviceInfo"]["macAddress"]
            self.device_name = device_info["DeviceInfo"]["deviceName"]
            self.device_model = device_info["DeviceInfo"]["model"]
            self.firmware_version = device_info["DeviceInfo"]["firmwareVersion"]
            self.firmware_released_date = device_info["DeviceInfo"]["firmwareReleasedDate"]

    def load_zones(self):
        devices = ZonesConf.from_dict(self.axpro.load_devices())

        if devices is not None:
            self.devices = {}
            for item in devices.list:
                self.devices[item.zone.id] = item.zone

    def _update_areas(self) -> None:
        """Fetch data from axpro via sync functions."""
        status = STATE_ALARM_DISARMED
        status_json = self.axpro.subsystem_status()

        try:
            subsys_resp = SubSystemResponse.from_dict(status_json)
            subsys_arr: list[SubSys] = []

            if subsys_resp is not None and subsys_resp.sub_sys_list is not None:
                subsys_arr = []
                for sublist in subsys_resp.sub_sys_list:
                    subsys_arr.append(sublist.sub_sys)

            # funcion para filtrar
            func: Callable[[SubSys], bool] = lambda n: n.enabled
            # nuevo listado filtrado
            subsys_arr = list(filter(func, subsys_arr))
            self.sub_systems = {}

            for subsys in subsys_arr:
                self.sub_systems[subsys.id] = subsys
                if subsys.alarm:
                    status = STATE_ALARM_TRIGGERED
                    break
                if subsys.arming == Arming.AWAY:
                    status = STATE_ALARM_ARMED_AWAY
                    break
                if subsys.arming == Arming.STAY:
                    status = STATE_ALARM_ARMED_HOME
                    break
                if subsys.arming == Arming.VACATION:
                    status = STATE_ALARM_ARMED_VACATION
                    break
        except:
            _LOGGER.warning("Error getting status: %s", status_json)

        # _LOGGER.debug("Axpro status: %s", status)
        self.state = status

    def _update_zones(self) -> None:
        """Fetch data from axpro via sync functions."""
        zone_response = self.axpro.zone_status()
        # _LOGGER.debug("Zones: %s", zone_response)

        zone_status = ZonesResponse.from_dict(zone_response)
        self.zone_status = zone_status

        zones = {}
        for zone in self.zone_status.zone_list:
            zones[zone.zone.id] = zone.zone

        self.zones = zones

    async def _async_update_data(self) -> None:
        """Fetch data from Axpro."""
        try:
            async with timeout(1):
                await self.hass.async_add_executor_job(self._update_areas)
                await self.hass.async_add_executor_job(self._update_zones)
        except ConnectionError as error:
            raise UpdateFailed(error) from error

    async def async_arm_home(self, sub_id: Optional[int] = None):
        """Arm alarm panel in home state."""

        is_success = await self.hass.async_add_executor_job(self.axpro.arm_home, sub_id)

        if is_success:
            await self.hass.async_add_executor_job(self.axpro.check_arm, sub_id)

            await self._async_update_data()
            await self.async_request_refresh()

    async def async_arm_away(self, sub_id: Optional[int] = None):
        """Arm alarm panel in away state"""

        is_success = await self.hass.async_add_executor_job(self.axpro.arm_away, sub_id)

        if is_success:
            await self.hass.async_add_executor_job(self.axpro.check_arm, sub_id)

            await self._async_update_data()
            await self.async_request_refresh()

    async def async_disarm(self, sub_id: Optional[int] = None):
        """Disarm alarm control panel."""

        _LOGGER.debug("async_disarm apretado en init")

        is_success = await self.hass.async_add_executor_job(self.axpro.disarm, sub_id)

        if is_success:
            await self._async_update_data()
            await self.async_request_refresh()

    async def test_button(self):
        """Disarm alarm control panel."""

        _LOGGER.debug("Boton apretado")
