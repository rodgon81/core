"""The hikvision_axpro integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Optional
from collections.abc import Callable

from homeassistant.core import (
    callback,
)

from .hikax import HikAx
from async_timeout import timeout
from .store import async_get_registry
from homeassistant.helpers import device_registry as dr
from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
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
    STATE_ALARM_TRIGGERED, SERVICE_RELOAD
)

from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DOMAIN, CONF_USE_CODE_ARMING, CONF_USE_CODE_DISARMING, CONF_ENABLE_DEBUG_OUTPUT
from .model import ZonesResponse, Zone, SubSystemResponse, SubSys, Arming, ZonesConf, ZoneConfig
from .websockets import async_register_websockets
from . import const
from .event import EventHandler

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL, Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Set up the hikvision_axpro integration component."""
    hass.data.setdefault(DOMAIN, {})

    async def _handle_reload(service):
        """Handle reload service call."""
        _LOGGER.info("Service %s.reload called: reloading integration", DOMAIN)

        current_entries = hass.config_entries.async_entries(DOMAIN)

        reload_tasks = [
            hass.config_entries.async_reload(entry.entry_id)
            for entry in current_entries
        ]

        await asyncio.gather(*reload_tasks)

    hass.helpers.service.async_register_admin_service(
        DOMAIN,
        SERVICE_RELOAD,
        _handle_reload,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hikvision_axpro from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    axpro = HikAx(host, username, password)

    use_code_arming = entry.data[CONF_USE_CODE_ARMING]
    use_code_disarming = entry.data[CONF_USE_CODE_DISARMING]
    code = entry.data[CONF_CODE]

    update_interval: float = entry.data.get(
        CONF_SCAN_INTERVAL, SCAN_INTERVAL.total_seconds())

    if entry.data.get(CONF_ENABLE_DEBUG_OUTPUT):
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.NOTSET)

    store = await async_get_registry(hass)
    coordinator = HikAxProDataUpdateCoordinator(
        store,
        hass,
        axpro,
        use_code_arming,
        use_code_disarming,
        code,
        update_interval
    )

    _LOGGER.debug("Antes del init device y 10seg timeout")

    try:
        async with timeout(10):
            await hass.async_add_executor_job(coordinator.init_device)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    _LOGGER.debug("Despues del init device, y ahora registramos el device")
    _LOGGER.debug("entry.entry_id: %s", entry.entry_id)
    _LOGGER.debug("coordinator.mac: %s", coordinator.mac)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        # connections={},
        identifiers={(DOMAIN, coordinator.mac)},
        manufacturer="HikVision" if coordinator.device_model is not None else "Unknown",
        # suggested_area=zone.zone.,
        name=coordinator.device_name,
        # via_device=(DOMAIN, str(coordinator.mac)),
        model=coordinator.device_model,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        const.DATA_COORDINATOR: coordinator,
        const.DATA_AREAS: {},
        const.DATA_MASTER: None
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Websocket support
    await async_register_websockets(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


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
    mac: Optional[str] = None
    firmware_version: Optional[str] = None
    firmware_released_date: Optional[str] = None

    def __init__(
        self,
        store,
        hass,
        axpro: HikAx,
        use_code_arming,
        use_code_disarming,
        code,
        update_interval: float
    ):
        self.hass = hass
        self.store = store
        self.axpro = axpro
        self.state = None
        self.zone_status = None
        self.host = axpro.host
        self.use_code_arming = use_code_arming
        self.use_code_disarming = use_code_disarming
        self.code = code
        self._subscriptions = []

        self._subscriptions.append(
            async_dispatcher_connect(
                hass, "alarmo_platform_loaded", self.setup_alarm_entities
            )
        )
        self.register_events()

        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=timedelta(seconds=update_interval))

    @callback
    def setup_alarm_entities(self):
        self.hass.data[const.DOMAIN]["event_handler"] = EventHandler(self.hass)

        areas = self.store.async_get_areas()
        config = self.store.async_get_config()

        for item in areas.values():
            async_dispatcher_send(self.hass, "alarmo_register_entity", item)

        if len(areas) > 1 and config["master"]["enabled"]:
            async_dispatcher_send(
                self.hass, "alarmo_register_master", config["master"])

    def init_device(self):
        self.axpro.connect()
        self.load_device_info()
        self.load_devices()
        self._update_data()

    def load_device_info(self):
        device_info = self.axpro.get_device_info()

        if device_info is not None:
            self.mac = device_info['DeviceInfo']['macAddress']
            self.device_name = device_info['DeviceInfo']['deviceName']
            self.device_model = device_info['DeviceInfo']['model']
            self.firmware_version = device_info['DeviceInfo']['firmwareVersion']
            self.firmware_released_date = device_info['DeviceInfo']['firmwareReleasedDate']

    def load_devices(self):
        devices = ZonesConf.from_dict(self.axpro.load_devices())

        if devices is not None:
            self.devices = {}
            for item in devices.list:
                self.devices[item.zone.id] = item.zone

    def register_events(self):
        # handle push notifications with action buttons
        @callback
        async def async_handle_push_event(event):
            if not event.data:
                return
            action = event.data.get(
                "actionName") if "actionName" in event.data else event.data.get("action")

            if action not in [
                const.EVENT_ACTION_FORCE_ARM,
                const.EVENT_ACTION_RETRY_ARM,
                const.EVENT_ACTION_DISARM
            ]:
                return

            if self.hass.data[const.DOMAIN]["master"]:
                alarm_entity = self.hass.data[const.DOMAIN]["master"]
            elif len(self.hass.data[const.DOMAIN]["areas"]) == 1:
                alarm_entity = list(
                    self.hass.data[const.DOMAIN]["areas"].values())[0]
            else:
                _LOGGER.info(
                    "Cannot process the push action, since there are multiple areas.")
                return

            arm_mode = alarm_entity._arm_mode
            if not arm_mode:
                _LOGGER.info(
                    "Cannot process the push action, since the arm mode is not known.")
                return

            if action == const.EVENT_ACTION_FORCE_ARM:
                _LOGGER.info("Received request for force arming")
                await alarm_entity.async_handle_arm_request(arm_mode, skip_code=True, bypass_open_sensors=True)
            elif action == const.EVENT_ACTION_RETRY_ARM:
                _LOGGER.info("Received request for retry arming")
                await alarm_entity.async_handle_arm_request(arm_mode, skip_code=True)
            elif action == const.EVENT_ACTION_DISARM:
                _LOGGER.info("Received request for disarming")
                await alarm_entity.async_alarm_disarm(code=None, skip_code=True)

        self._subscriptions.append(
            self.hass.bus.async_listen(
                const.PUSH_EVENT, async_handle_push_event)
        )

    def _update_data(self) -> None:
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

            func: Callable[[SubSys], bool] = lambda n: n.enabled
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

        zone_response = self.axpro.zone_status()
        zone_status = ZonesResponse.from_dict(zone_response)
        self.zone_status = zone_status
        zones = {}

        for zone in zone_status.zone_list:
            zones[zone.zone.id] = zone.zone

        self.zones = zones
        # _LOGGER.debug("Zones: %s", zone_response)

    async def _async_update_data(self) -> None:
        """Fetch data from Axpro."""
        try:
            async with timeout(1):
                await self.hass.async_add_executor_job(self._update_data)
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
