import logging
import time
import attr
from collections import OrderedDict
from typing import MutableMapping, cast
from homeassistant.loader import bind_hass
from homeassistant.core import (callback, HomeAssistant)
from homeassistant.helpers.storage import Store

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_VACATION
)

from homeassistant.components.alarm_control_panel import (
    FORMAT_NUMBER as CODE_FORMAT_NUMBER,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_REGISTRY = f"{DOMAIN}_storage"
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 6
SAVE_DELAY = 10


@attr.s(slots=True, frozen=True)
class ModeEntry:
    """Mode storage Entry."""

    enabled = attr.ib(type=bool, default=False)
    exit_time = attr.ib(type=int, default=0)
    entry_time = attr.ib(type=int, default=0)


@attr.s(slots=True, frozen=True)
class AreaEntry:
    """Area storage Entry."""

    area_id = attr.ib(type=str, default=None)
    name = attr.ib(type=str, default=None)
    modes = attr.ib(type=[str, ModeEntry], default={
        STATE_ALARM_ARMED_AWAY: ModeEntry(),
        STATE_ALARM_ARMED_HOME: ModeEntry(),
        STATE_ALARM_ARMED_NIGHT: ModeEntry(),
        STATE_ALARM_ARMED_CUSTOM_BYPASS: ModeEntry(),
        STATE_ALARM_ARMED_VACATION: ModeEntry()
    })


@attr.s(slots=True, frozen=True)
class Config:
    """(General) Config storage Entry."""
    host = attr.ib(type=str, default="")
    username = attr.ib(type=str, default="")
    password = attr.ib(type=str, default="")
    code_arm_required = attr.ib(type=bool, default=False)
    code_disarm_required = attr.ib(type=bool, default=False)
    code_format = attr.ib(type=str, default=CODE_FORMAT_NUMBER)
    enabled = attr.ib(type=bool, default=True)
    name = attr.ib(type=str, default="master_test")
    code = attr.ib(type=str, default="")
    scan_interval = attr.ib(type=int, default=5)
    enable_debug_output = attr.ib(type=bool, default=True)


@attr.s(slots=True, frozen=True)
class SensorEntry:
    """Sensor storage Entry."""

    entity_id = attr.ib(type=str, default=None)
    # type = attr.ib(type=str, default=SENSOR_TYPE_OTHER)
    modes = attr.ib(type=list, default=[])
    use_exit_delay = attr.ib(type=bool, default=True)
    use_entry_delay = attr.ib(type=bool, default=True)
    always_on = attr.ib(type=bool, default=False)
    arm_on_close = attr.ib(type=bool, default=False)
    allow_open = attr.ib(type=bool, default=False)
    trigger_unavailable = attr.ib(type=bool, default=False)
    auto_bypass = attr.ib(type=bool, default=False)
    auto_bypass_modes = attr.ib(type=list, default=[])
    area = attr.ib(type=str, default=None)
    enabled = attr.ib(type=bool, default=True)


class MigratableStore(Store):
    async def _async_migrate_func(self, old_version, data: dict):
        area_id = str(int(time.time()))
        data["areas"] = [
            attr.asdict(AreaEntry(**{
                "name": "Hikvision",
                "modes": {
                    mode: attr.asdict(ModeEntry(
                        enabled=bool(config["enabled"]),
                        exit_time=int(config["leave_time"]),
                        entry_time=int(config["entry_time"]),
                    ))
                    for (mode, config) in data["config"]["modes"].items()
                }
            }, area_id=area_id))
        ]

        if "sensors" in data:
            for sensor in data["sensors"]:
                sensor["area"] = area_id

        data["sensors"] = [
            # attr.asdict(SensorEntry(
            #   **omit(sensor, ["name"]),
            # ))
            # for sensor in data["sensors"]
        ]

        return data


class AlarmoStorage:
    """Class to hold alarmo configuration data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the storage."""
        self.hass = hass
        self.config: Config = Config()
        self.areas: MutableMapping[str, AreaEntry] = {}
        self.sensors: MutableMapping[str, SensorEntry] = {}
        self._store = MigratableStore(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> None:
        """Load the registry of schedule entries."""
        data = await self._store.async_load()
        config: Config = Config()
        areas: "OrderedDict[str, AreaEntry]" = OrderedDict()
        sensors: "OrderedDict[str, SensorEntry]" = OrderedDict()

        if data is not None:
            config = Config(
                code_arm_required=data["config"]["code_arm_required"],
                code_disarm_required=data["config"]["code_disarm_required"],
                code_format=data["config"]["code_format"]
                # enabled=data["config"]["enabled"],
                # name=data["config"]["name"],
                # code=data["config"]["code"]
            )

            if "areas" in data:
                for area in data["areas"]:
                    modes = {
                        mode: ModeEntry(
                            enabled=config["enabled"],
                            exit_time=config["exit_time"],
                            entry_time=config["entry_time"],
                        )
                        for (mode, config) in area["modes"].items()
                    }
                    areas[area["area_id"]] = AreaEntry(
                        area_id=area["area_id"],
                        name=area["name"],
                        modes=modes
                    )

            if "sensors" in data:
                for sensor in data["sensors"]:
                    sensors[sensor["entity_id"]] = SensorEntry(**sensor)

        self.config = config
        self.areas = areas
        self.sensors = sensors

        if not areas:
            await self.async_factory_default()

    async def async_factory_default(self):
        self.async_create_area({
            "name": "Hikvision",
            "modes": {
                STATE_ALARM_ARMED_AWAY: attr.asdict(
                    ModeEntry(
                        enabled=True,
                        exit_time=60,
                        entry_time=60
                    )
                ),
                STATE_ALARM_ARMED_HOME: attr.asdict(
                    ModeEntry(
                        enabled=True
                    )
                )
            }
        })

    @callback
    def async_schedule_save(self) -> None:
        """Schedule saving the registry of alarmo."""
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    async def async_save(self) -> None:
        """Save the registry of alarmo."""
        await self._store.async_save(self._data_to_save())

    @callback
    def _data_to_save(self) -> dict:
        """Return data for the registry for alarmo to store in a file."""
        store_data = {
            "config": attr.asdict(self.config),
        }

        store_data["areas"] = [
            attr.asdict(entry) for entry in self.areas.values()
        ]
        store_data["sensors"] = [
            attr.asdict(entry) for entry in self.sensors.values()
        ]

        return store_data

    async def async_delete(self):
        """Delete config."""
        _LOGGER.warning("Removing alarmo configuration data!")
        await self._store.async_remove()
        self.config = Config()
        self.areas = {}
        self.sensors = {}

        await self.async_factory_default()

    @callback
    def async_get_config(self):
        return attr.asdict(self.config)

    @callback
    def async_update_config(self, changes: dict):
        """Update existing config."""

        old = self.config
        new = self.config = attr.evolve(old, **changes)
        self.async_schedule_save()
        return attr.asdict(new)

    @callback
    def async_update_mode_config(self, mode: str, changes: dict):
        """Update existing config."""

        modes = self.config.modes
        old = (
            self.config.modes[mode]
            if mode in self.config.modes
            else ModeEntry()
        )
        new = attr.evolve(old, **changes)
        modes[mode] = new
        self.config = attr.evolve(self.config, **{"modes": modes})
        self.async_schedule_save()
        return new

    @callback
    def async_get_area(self, area_id) -> AreaEntry:
        """Get an existing AreaEntry by id."""
        res = self.areas.get(area_id)
        return attr.asdict(res) if res else None

    @callback
    def async_get_areas(self):
        """Get an existing AreaEntry by id."""
        res = {}
        for (key, val) in self.areas.items():
            res[key] = attr.asdict(val)
        return res

    @callback
    def async_create_area(self, data: dict) -> AreaEntry:
        """Create a new AreaEntry."""
        area_id = str(int(time.time()))
        new_area = AreaEntry(**data, area_id=area_id)
        self.areas[area_id] = new_area
        self.async_schedule_save()
        return attr.asdict(new_area)

    @callback
    def async_delete_area(self, area_id: str) -> None:
        """Delete AreaEntry."""
        if area_id in self.areas:
            del self.areas[area_id]
            self.async_schedule_save()
            return True
        return False

    @callback
    def async_update_area(self, area_id: str, changes: dict) -> AreaEntry:
        """Update existing self."""
        old = self.areas[area_id]
        new = self.areas[area_id] = attr.evolve(old, **changes)
        self.async_schedule_save()
        return attr.asdict(new)

    @callback
    def async_get_sensor(self, entity_id) -> SensorEntry:
        """Get an existing SensorEntry by id."""
        res = self.sensors.get(entity_id)
        return attr.asdict(res) if res else None

    @callback
    def async_get_sensors(self):
        """Get an existing SensorEntry by id."""
        res = {}
        for (key, val) in self.sensors.items():
            res[key] = attr.asdict(val)
        return res

    @callback
    def async_create_sensor(self, entity_id: str, data: dict) -> SensorEntry:
        """Create a new SensorEntry."""
        if entity_id in self.sensors:
            return False
        new_sensor = SensorEntry(**data, entity_id=entity_id)
        self.sensors[entity_id] = new_sensor
        self.async_schedule_save()
        return new_sensor

    @callback
    def async_delete_sensor(self, entity_id: str) -> None:
        """Delete SensorEntry."""
        if entity_id in self.sensors:
            del self.sensors[entity_id]
            self.async_schedule_save()
            return True
        return False

    @callback
    def async_update_sensor(self, entity_id: str, changes: dict) -> SensorEntry:
        """Update existing SensorEntry."""
        old = self.sensors[entity_id]
        new = self.sensors[entity_id] = attr.evolve(old, **changes)
        self.async_schedule_save()
        return new


@bind_hass
async def async_get_registry(hass: HomeAssistant) -> AlarmoStorage:
    """Return alarmo storage instance."""
    task = hass.data.get(DATA_REGISTRY)

    if task is None:

        async def _load_reg() -> AlarmoStorage:
            registry = AlarmoStorage(hass)
            await registry.async_load()
            return registry

        task = hass.data[DATA_REGISTRY] = hass.async_create_task(_load_reg())

    return cast(AlarmoStorage, await task)
