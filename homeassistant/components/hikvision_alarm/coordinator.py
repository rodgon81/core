"""The hikvision_axpro integration."""
import asyncio
import logging

from datetime import timedelta
from typing import Optional, Any
from collections.abc import Callable
from homeassistant.core import callback
from async_timeout import timeout
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import const
from .model import ZonesResponse, Zone, SubSystemResponse, SubSys, Arming, ZonesConf, ZoneConfig
from .hikax import HikAx
from .store import AlarmoStorage
from .automations import AutomationHandler
from .event import EventHandler
from .api_class import ModuleType


_LOGGER = logging.getLogger(__name__)


class HikAlarmDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ax pro data."""

    def __init__(self, store, hass, axpro: HikAx, entry: ConfigEntry):
        _LOGGER.debug("__init__ HikAlarmDataUpdateCoordinator")
        self.hass: HomeAssistant = hass
        self.store: AlarmoStorage = store
        self.axpro: HikAx = axpro
        self.zone_status: Optional[ZonesResponse] = None
        self.siren_status: None
        self.relay_status: None
        self._subscriptions = []
        self.entry: ConfigEntry = entry
        self.zones: Optional[dict[int, Zone]] = None
        self.device_model: Optional[str] = None
        self.device_name: Optional[str] = None
        self.device_mac: Optional[str] = None
        self.sub_systems: dict[int, SubSys] = {}
        """ Zones aka devices """
        self.devices: dict[int, ZoneConfig] = {}
        self.id: Optional[str] = entry.entry_id
        self.firmware_version: Optional[str] = None
        self.firmware_released_date: Optional[str] = None
        self.batery: Optional[int] = 100
        self.wifi_state: Optional[bool] = False
        self.movile_net_state: Optional[bool] = True
        self.ethernet_state: Optional[bool] = True
        self.batery_state: Optional[str] = "100%"

        self._subscriptions.append(async_dispatcher_connect(hass, "hik_alarm_control_platform_loaded", self.setup_alarm_control_platform_entities))
        self._subscriptions.append(async_dispatcher_connect(hass, "hik_button_platform_loaded", self.setup_button_platform_entities))
        self._subscriptions.append(async_dispatcher_connect(hass, "hik_binary_sensor_platform_loaded", self.setup_binary_sensor_platform_entities))
        self._subscriptions.append(async_dispatcher_connect(hass, "hik_sensor_platform_loaded", self.setup_sensor_platform_entities))

        super().__init__(hass, _LOGGER, name=const.DOMAIN, update_interval=timedelta(seconds=self.entry.data[const.CONF_HIK_SCAN_INTERVAL]))

    @callback
    def setup_alarm_control_platform_entities(self):
        _LOGGER.debug("setup_alarm_entities de Coordinator")

        self.hass.data[const.DOMAIN][self.entry.entry_id]["automation_handler"] = AutomationHandler(self.hass, self.entry.entry_id)
        self.hass.data[const.DOMAIN][self.entry.entry_id]["event_handler"] = EventHandler(self.hass, self.entry.entry_id)

        _LOGGER.debug("self.entry.data: %s", self.entry.data[const.CONF_HIK_MASTER_CONFIG])

        areas = self.store.async_get_areas()

        _LOGGER.debug("async_get_areas: %s", areas)

        config = self.store.async_get_master_config()  # self.entry.data[const.CONF_HIK_MASTER_CONFIG]

        _LOGGER.debug("async_get_master_config: %s", config)

        for item in areas.values():
            async_dispatcher_send(self.hass, "alarmo_register_entity", item)

        if len(areas) > 1 and config[const.CONF_HIK_ENABLED]:
            async_dispatcher_send(self.hass, "alarmo_register_master", config)

    @callback
    def setup_button_platform_entities(self):
        _LOGGER.debug("setup_button_platform_entities de Coordinator")

        async_dispatcher_send(self.hass, "hik_register_alarm_button")

    @callback
    def setup_binary_sensor_platform_entities(self):
        _LOGGER.debug("setup_binary_sensor_platform_entities de Coordinator")

        if self.zone_status is not None:
            for zone in self.zone_status.zone_list:
                zone_config = self.devices.get(zone.zone.id)

                if zone.zone.tamper_evident is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_binary_sensor", zone.zone, "tamper_evident")
                if zone.zone.shielded is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_binary_sensor", zone.zone, "shielded")
                if zone.zone.bypassed is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_binary_sensor", zone.zone, "bypassed")
                if zone.zone.armed is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_binary_sensor", zone.zone, "armed")
                if zone.zone.alarm is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_binary_sensor", zone.zone, "alarm")

        async_dispatcher_send(self.hass, "hik_register_alarm_binary_sensor")

    @callback
    def setup_sensor_platform_entities(self):
        _LOGGER.debug("setup_sensor_platform_entities de Coordinator")

        if self.zone_status is not None:
            for zone in self.zone_status.zone_list:
                zone_config = self.devices.get(zone.zone.id)

                if zone.zone.status is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_sensor", zone.zone, "status")
                if zone.zone.zone_type is not None:
                    async_dispatcher_send(self.hass, "hik_register_zone_sensor", zone.zone, "zone_type")
                if zone.zone.signal is not None and zone_config.module_type is ModuleType.EXTEND_WIRELESS:
                    async_dispatcher_send(self.hass, "hik_register_zone_sensor", zone.zone, "signal")

        async_dispatcher_send(self.hass, "hik_register_alarm_sensor")

    # llamado de websoket
    async def async_update_config(self):
        _LOGGER.debug("async_update_config de Coordinator")

        data = self.entry.data

        old_config = self.store.async_get_master_config()

        _LOGGER.debug("async_get_master_config: %s", old_config)
        _LOGGER.debug("data: %s", data)

        if old_config != data[const.CONF_HIK_MASTER_CONFIG]:
            if self.hass.data[const.DOMAIN][self.entry.entry_id][const.ATTR_MASTER]:
                await self.async_remove_entity(const.ATTR_MASTER)
            if data[const.CONF_HIK_MASTER_CONFIG][const.CONF_HIK_ENABLED]:
                async_dispatcher_send(self.hass, "alarmo_register_master", data[const.CONF_HIK_MASTER_CONFIG])
            else:
                automations = self.hass.data[const.DOMAIN][self.entry.entry_id]["automation_handler"].get_automations_by_area(None)

                if len(automations):
                    for el in automations:
                        self.store.async_delete_automation(el)
                    async_dispatcher_send(self.hass, "alarmo_automations_updated")

        self.store.async_update_master_config(data[const.CONF_HIK_MASTER_CONFIG])
        self.store.async_update_alarm_config(data[const.CONF_HIK_ALARM_CONFIG])

        async_dispatcher_send(self.hass, "alarmo_config_updated")

    # llamado de websoket
    async def async_update_area_config(self, area_id: str = None, data: dict = {}):
        _LOGGER.debug("async_update_area_config de Coordinator")
        if const.ATTR_REMOVE in data:
            # delete an area
            res = self.store.async_get_area(area_id)

            if not res:
                return

            sensors = self.store.async_get_sensors()
            sensors = dict(filter(lambda el: el[1]["area"] == area_id, sensors.items()))

            if sensors:
                for el in sensors.keys():
                    self.store.async_delete_sensor(el)
                async_dispatcher_send(self.hass, "alarmo_sensors_updated")

            self.store.async_delete_area(area_id)

            await self.async_remove_entity(area_id)

            if len(self.store.async_get_areas()) == 1 and self.hass.data[const.DOMAIN][self.entry.entry_id]["master"]:
                await self.async_remove_entity("master")

        elif self.store.async_get_area(area_id):
            # modify an area
            entry = self.store.async_update_area(area_id, data)

            if "name" not in data:
                async_dispatcher_send(self.hass, "alarmo_config_updated", area_id)
            else:
                await self.async_remove_entity(area_id)
                async_dispatcher_send(self.hass, "alarmo_register_entity", entry)
        else:
            # create an area
            entry = self.store.async_create_area(data)

            async_dispatcher_send(self.hass, "alarmo_register_entity", entry)

            config = self.store.async_get_config()

            if len(self.store.async_get_areas()) == 2 and config["master"]["enabled"]:
                async_dispatcher_send(self.hass, "alarmo_register_master", config["master"])

    # llamado de websoket
    async def async_update_sensor_config(self, entity_id: str, data: dict):
        _LOGGER.debug("async_update_sensor_config de Coordinator")

        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor(entity_id)
        elif self.store.async_get_sensor(entity_id):
            self.store.async_update_sensor(entity_id, data)
        else:
            self.store.async_create_sensor(entity_id, data)

        async_dispatcher_send(self.hass, "alarmo_sensors_updated")

    async def async_remove_entity(self, area_id: str):
        _LOGGER.debug("async_remove_entity de Coordinator")

        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)

        if area_id == "master":
            entity = self.hass.data[const.DOMAIN][self.entry.entry_id]["master"]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN][self.entry.entry_id]["master"] = None
        else:
            entity = self.hass.data[const.DOMAIN][self.entry.entry_id]["areas"][area_id]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN][self.entry.entry_id]["areas"].pop(area_id, None)

    async def async_unload(self):
        """remove all alarmo objects"""
        _LOGGER.debug("async_unload de Coordinator")

        # remove alarm_control_panel entities
        areas = list(self.hass.data[const.DOMAIN][self.entry.entry_id]["areas"].keys())
        for area in areas:
            await self.async_remove_entity(area)
        if self.hass.data[const.DOMAIN][self.entry.entry_id]["master"]:
            await self.async_remove_entity("master")

        del self.hass.data[const.DOMAIN][self.entry.entry_id]["automation_handler"]
        del self.hass.data[const.DOMAIN][self.entry.entry_id]["event_handler"]

        # remove subscriptions for coordinator
        while len(self._subscriptions):
            self._subscriptions.pop()()

    async def async_delete_config(self):
        """wipe alarmo storage"""
        await self.store.async_delete()

    # ------------------------------------------------

    async def get_mac(self):
        """Handle reload service call."""
        _LOGGER.info("get_mac")
        return self.device_mac

    async def get_batery(self):
        """Handle reload service call."""
        _LOGGER.info("get_batery")
        return "100%"

    async def get_wifi_state(self):
        """Handle reload service call."""
        _LOGGER.info("get_wifi_state")
        return False  # self.batery

    async def get_movile_net_state(self):
        """Handle reload service call."""
        _LOGGER.info("get_movile_net_state")
        return True  # self.batery

    async def get_ethernet_state(self):
        """Handle reload service call."""
        _LOGGER.info("get_ethernet_state")
        return True  # self.batery

    async def handle_reload(self):
        """Handle reload service call."""
        _LOGGER.info("Service %s.reload called: reloading integration", const.DOMAIN)

        reload_task = [self.hass.config_entries.async_reload(self.entry.entry_id)]

        await asyncio.gather(*reload_task)

    def from_bool(self, value: Any) -> bool:
        """Convert string value to boolean."""
        if isinstance(value, bool):
            return value

        if not isinstance(value, str):
            raise ValueError("invalid literal for boolean. Not a string.")

        valid = {"true": True, "1": True, "false": False, "0": False}

        lower_value = value.lower()

        if lower_value in valid:
            return valid[lower_value]
        else:
            raise ValueError('invalid literal for boolean: "%s"' % value)

    def init_device(self):
        _LOGGER.debug("init_device de Coordinator")

        self.axpro.connect()
        self.load_device_info()

        areas_config = self.axpro.get_areas_config()

        _LOGGER.debug("areas_config: %s", areas_config)

        for val in areas_config["List"]:
            if not self.from_bool(val["SubSys"]["enabled"]):
                continue

            data = {
                "area_id": val["SubSys"]["id"],
                "name": val["SubSys"]["name"],
                "enabled": val["SubSys"]["enabled"],
                "modes": {
                    const.STATE_ALARM_ARMED_AWAY: {
                        "enabled": True,
                        "exit_time": 20,
                        "entry_time": 30,
                        "trigger_time": 30,
                    },
                    const.STATE_ALARM_ARMED_HOME: {
                        "enabled": True,
                        "exit_time": 20,
                        "entry_time": 30,
                        "trigger_time": 30,
                    },
                },
            }

            new_area = self.store.async_create_area(data)
            _LOGGER.debug("new_area: %s", new_area)
        # ----------------------------------------------------------
        users = self.axpro.get_users()

        user_id = 0
        for user in users["UserList"]["User"]:
            if user["userName"] == self.entry.data[const.CONF_HIK_USERNAME]:
                user_id = user["id"]

        user = self.axpro.get_config_user(user_id)
        subSysOrZoneArm = self.from_bool(user["UserPermission"]["remotePermission"]["subSysOrZoneArm"])
        subSysOrZoneDisarm = self.from_bool(user["UserPermission"]["remotePermission"]["subSysOrZoneDisarm"])
        subSysOrZoneClearArm = self.from_bool(user["UserPermission"]["remotePermission"]["subSysOrZoneClearArm"])
        zoneBypass = self.from_bool(user["UserPermission"]["remotePermission"]["zoneBypass"])
        zoneBypassRecover = self.from_bool(user["UserPermission"]["remotePermission"]["zoneBypassRecover"])
        # subSystemList = user["UserPermission"]["remotePermission"]["subSystemList"]

        self.entry.data[const.CONF_HIK_ALARM_CONFIG][const.CONF_HIK_CODE_ARM_REQUIRED] = subSysOrZoneArm
        self.entry.data[const.CONF_HIK_ALARM_CONFIG][const.CONF_HIK_CODE_DISARM_REQUIRED] = subSysOrZoneDisarm

        _LOGGER.debug("CONF_HIK_ALARM_CONFIG: %s", self.entry.data[const.CONF_HIK_ALARM_CONFIG])

        self.load_zones()
        self._update_areas()
        self._update_zones()

    def load_device_info(self):
        device_info = self.axpro.get_device_info()

        if device_info is not None:
            self.device_mac = device_info["DeviceInfo"]["macAddress"]
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
        status = const.STATE_ALARM_DISARMED
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
                    status = const.STATE_ALARM_TRIGGERED
                    break
                if subsys.arming == Arming.AWAY:
                    status = const.STATE_ALARM_ARMED_AWAY
                    break
                if subsys.arming == Arming.STAY:
                    status = const.STATE_ALARM_ARMED_HOME
                    break
                if subsys.arming == Arming.VACATION:
                    status = const.STATE_ALARM_ARMED_VACATION
                    break
        except:
            _LOGGER.warning("Error getting status: %s", status_json)

        # _LOGGER.debug("Axpro status: %s", status)

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
