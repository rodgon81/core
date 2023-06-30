import logging
import time
import attr
from collections import OrderedDict
from typing import MutableMapping
from homeassistant.core import callback, HomeAssistant

from homeassistant.components.alarm_control_panel.const import FORMAT_NUMBER as CODE_FORMAT_NUMBER

from . import const

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True, frozen=True)
class ModeEntry:
    """Mode storage Entry."""

    enabled = attr.ib(type=bool, default=False)
    exit_time = attr.ib(type=int, default=0)
    entry_time = attr.ib(type=int, default=0)


@attr.s(slots=True, frozen=True)
class MasterConfig:
    """Master storage Entry."""

    enabled = attr.ib(type=bool, default=True)
    name = attr.ib(type=str, default="master")


@attr.s(slots=True, frozen=True)
class AreaEntry:
    """Area storage Entry."""

    area_id = attr.ib(type=str, default=None)
    name = attr.ib(type=str, default=None)
    enabled = attr.ib(type=bool, default=False)
    modes = attr.ib(
        type=[str, ModeEntry],
        default={
            const.STATE_ALARM_ARMED_AWAY: ModeEntry(),
            const.STATE_ALARM_ARMED_HOME: ModeEntry(),
            const.STATE_ALARM_ARMED_NIGHT: ModeEntry(),
            const.STATE_ALARM_ARMED_CUSTOM_BYPASS: ModeEntry(),
            const.STATE_ALARM_ARMED_VACATION: ModeEntry(),
        },
    )


@attr.s(slots=True, frozen=True)
class AlarmConfig:
    """Master storage Entry."""

    username = attr.ib(type=str, default="master")
    code_arm_required = attr.ib(type=bool, default=False)
    code_disarm_required = attr.ib(type=bool, default=False)
    can_arm = attr.ib(type=bool, default=False)
    can_disarm = attr.ib(type=bool, default=False)
    area_limit = attr.ib(type=list, default=[])
    zone_bypass = attr.ib(type=bool, default=False)
    code_length = attr.ib(type=int, default=0)
    code_format = attr.ib(type=str, default=CODE_FORMAT_NUMBER)
    code = attr.ib(type=str, default="")


@attr.s(slots=True, frozen=True)
class Config:
    """(General) Config storage Entry."""

    host = attr.ib(type=str, default="")
    username = attr.ib(type=str, default="")
    password = attr.ib(type=str, default="")
    scan_interval = attr.ib(type=int, default=5)
    enable_debug_output = attr.ib(type=bool, default=True)
    master_config = attr.ib(type=MasterConfig, default=MasterConfig())
    alarm_config = attr.ib(type=AlarmConfig, default=AlarmConfig())


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


@attr.s(slots=True, frozen=True)
class AlarmoTriggerEntry:
    """Trigger storage Entry."""

    event = attr.ib(type=str, default="")
    area = attr.ib(type=str, default=None)
    modes = attr.ib(type=list, default=[])


@attr.s(slots=True, frozen=True)
class EntityTriggerEntry:
    """Trigger storage Entry."""

    entity_id = attr.ib(type=str, default=None)
    state = attr.ib(type=str, default=None)


@attr.s(slots=True, frozen=True)
class ActionEntry:
    """Action storage Entry."""

    service = attr.ib(type=str, default="")
    entity_id = attr.ib(type=str, default=None)
    data = attr.ib(type=dict, default={})


@attr.s(slots=True, frozen=True)
class AutomationEntry:
    """Automation storage Entry."""

    automation_id = attr.ib(type=str, default=None)
    type = attr.ib(type=str, default=None)
    name = attr.ib(type=str, default="")
    triggers = attr.ib(type=[AlarmoTriggerEntry], default=[])
    actions = attr.ib(type=[ActionEntry], default=[])
    enabled = attr.ib(type=bool, default=True)


def parse_automation_entry(data: dict):
    def create_trigger_entity(config: dict):
        if "event" in config:
            return AlarmoTriggerEntry(**config)
        else:
            return EntityTriggerEntry(**config)

    output = {}

    if "triggers" in data:
        output["triggers"] = list(map(create_trigger_entity, data["triggers"]))
    if "actions" in data:
        output["actions"] = list(map(lambda el: ActionEntry(**el), data["actions"]))
    if "automation_id" in data:
        output["automation_id"] = data["automation_id"]
    if "name" in data:
        output["name"] = data["name"]
    if "type" in data:
        output["type"] = data["type"]
    if "enabled" in data:
        output["enabled"] = data["enabled"]
    return output


class AlarmoStorage:
    """Class to hold alarmo configuration data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the storage."""
        self.hass = hass
        self.config: Config = Config()
        self.master_config: MasterConfig = MasterConfig()
        self.alarm_config: AlarmConfig = AlarmConfig()
        self.areas: MutableMapping[str, AreaEntry] = {}
        self.sensors: MutableMapping[str, SensorEntry] = {}
        self.automations: MutableMapping[str, AutomationEntry] = {}

    async def async_delete(self):
        """Delete config."""
        _LOGGER.warning("Removing alarmo configuration data!")

        self.config = {}
        self.master_config = {}
        self.alarm_config = {}
        self.areas = {}
        self.sensors = {}
        self.automations = {}

    @callback
    def async_get_master_config(self):
        res = self.master_config
        return attr.asdict(res)

    @callback
    def async_update_master_config(self, changes: dict):
        """Update existing config."""
        old = self.master_config
        new = attr.evolve(old, **changes)

        self.master_config = new

        return attr.asdict(self.master_config)

    @callback
    def async_get_alarm_config(self):
        res = self.alarm_config
        return attr.asdict(res)

    @callback
    def async_update_alarm_config(self, changes: dict):
        """Update existing config."""
        old = self.alarm_config
        new = attr.evolve(old, **changes)

        self.alarm_config = new

        return attr.asdict(self.alarm_config)

    @callback
    def async_get_config(self):
        return attr.asdict(self.config)

    @callback
    def async_update_config(self, changes: dict):
        """Update existing config."""
        old = self.config
        new = attr.evolve(old, **changes)

        self.config = new

        return attr.asdict(self.config)

    @callback
    def async_update_mode_config(self, mode: str, changes: dict):
        """Update existing config."""

        modes = self.config.modes
        old = self.config.modes[mode] if mode in self.config.modes else ModeEntry()
        new = attr.evolve(old, **changes)
        modes[mode] = new
        self.config = attr.evolve(self.config, **{"modes": modes})

        return new

    @callback
    def async_get_area(self, area_id) -> AreaEntry:
        """Get an existing AreaEntry by id."""
        res = self.areas.get(area_id)

        return attr.asdict(res)

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
        new_area = AreaEntry(**data)

        self.areas[new_area.area_id] = new_area

        return attr.asdict(new_area)

    @callback
    def async_delete_area(self, area_id: str) -> None:
        """Delete AreaEntry."""
        if area_id in self.areas:
            del self.areas[area_id]

            return True
        return False

    @callback
    def async_update_area(self, area_id: str, changes: dict) -> AreaEntry:
        """Update existing self."""
        old = self.areas[area_id]
        new = self.areas[area_id] = attr.evolve(old, **changes)

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

        return new_sensor

    @callback
    def async_delete_sensor(self, entity_id: str) -> None:
        """Delete SensorEntry."""
        if entity_id in self.sensors:
            del self.sensors[entity_id]

            return True

        return False

    @callback
    def async_update_sensor(self, entity_id: str, changes: dict) -> SensorEntry:
        """Update existing SensorEntry."""
        old = self.sensors[entity_id]
        new = self.sensors[entity_id] = attr.evolve(old, **changes)

        return new

    @callback
    def async_get_automations(self):
        """Get an existing AutomationEntry by id."""
        res = {}

        for (key, val) in self.automations.items():
            res[key] = attr.asdict(val)

        return res

    @callback
    def async_create_automation(self, data: dict) -> AutomationEntry:
        """Create a new AutomationEntry."""
        automation_id = str(int(time.time()))
        new_automation = AutomationEntry(**parse_automation_entry(data), automation_id=automation_id)
        self.automations[automation_id] = new_automation

        return new_automation

    @callback
    def async_delete_automation(self, automation_id: str) -> None:
        """Delete AutomationEntry."""
        if automation_id in self.automations:
            del self.automations[automation_id]

            return True

        return False

    @callback
    def async_update_automation(self, automation_id: str, changes: dict) -> AutomationEntry:
        """Update existing AutomationEntry."""
        old = self.automations[automation_id]
        new = self.automations[automation_id] = attr.evolve(old, **parse_automation_entry(changes))

        return new
