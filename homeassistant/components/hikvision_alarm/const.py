"""Constants for the hikvision_axpro integration."""

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
    STATE_ALARM_PENDING,
    STATE_ALARM_ARMING,
    ATTR_ENTITY_ID,
    CONF_MODE,
    CONF_CODE,
    ATTR_NAME,
)
from typing import Final
import voluptuous as vol
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature
from homeassistant.helpers import config_validation as cv

PUSH_EVENT = "mobile_app_notification_action"
EVENT_ACTION_FORCE_ARM = "ALARMO_FORCE_ARM"
EVENT_ACTION_RETRY_ARM = "ALARMO_RETRY_ARM"
EVENT_ACTION_DISARM = "ALARMO_DISARM"

DOMAIN: Final[str] = "hikvision_alarm"
DATA_COORDINATOR: Final[str] = "coordinator"
DATA_AREAS: Final[str] = "areas"
DATA_MASTER: Final[str] = "master"

CONF_USE_CODE_ARMING: Final[str] = "use_code_arming"
CONF_USE_CODE_DISARMING: Final[str] = "use_code_disarming"
CONF_ALLOW_SUBSYSTEMS: Final[str] = "allow_subsystems"
CONF_ENABLE_DEBUG_OUTPUT: Final[str] = "enable_debug_output"

ATTR_TYPE = "type"
ATTR_AREA = "area"
ATTR_MASTER = "master"
ATTR_ENABLED = "enabled"
ATTR_AREA_LIMIT = "area_limit"
ATTR_CODE_ARM_REQUIRED = "code_arm_required"
ATTR_CODE_DISARM_REQUIRED = "code_disarm_required"

NAME = "Alarm"
MANUFACTURER = "Hikvision"

ATTR_FORCE = "force"
ATTR_SKIP_DELAY = "skip_delay"
ATTR_CONTEXT_ID = "context_id"

ATTR_MODES = "modes"
ATTR_ARM_MODE = "arm_mode"
ATTR_CODE_DISARM_REQUIRED = "code_disarm_required"
ATTR_REMOVE = "remove"
ATTR_OLD_CODE = "old_code"


class Endpoints:
    Session_Capabilities = "/ISAPI/Security/sessionLogin/capabilities?username="
    Session_Login = "/ISAPI/Security/sessionLogin"
    Session_Logout = "/ISAPI/Security/sessionLogout"
    Alarm_Disarm = "/ISAPI/SecurityCP/control/disarm/{}"
    Alarm_ArmAway = "/ISAPI/SecurityCP/control/arm/{}?ways=away"
    Alarm_ArmHome = "/ISAPI/SecurityCP/control/arm/{}?ways=stay"
    SubSystemStatus = "/ISAPI/SecurityCP/status/subSystems"
    ZonesConfig = "/ISAPI/SecurityCP/Configuration/zones"
    HostStatus = "/ISAPI/SecurityCP/status/host"
    PeripheralsStatus = "/ISAPI/SecurityCP/status/exDevStatus"
    ZoneStatus = "/ISAPI/SecurityCP/status/zones"
    BypassZone = "/ISAPI/SecurityCP/control/bypass/"
    RecoverBypassZone = "/ISAPI/SecurityCP/control/Recoverbypass/"
    AreaArmStatus = "/ISAPI/SecurityCP/status/armStatus"
    SirenStatus = "/ISAPI/SecurityCP/status/sirenStatus"
    RepeaterStatus = "/ISAPI/SecurityCP/status/repeaterStatus"
    KeypadStatus = "/ISAPI/SecurityCP/status/keypadStatus"
    DeviceInfo = "/ISAPI/System/deviceInfo"
    systemFault = "/ISAPI/SecurityCP/status/systemFault"


class Method:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


SERVICE_ARM = "arm"
SERVICE_DISARM = "disarm"

EVENT_DISARM = "disarm"
EVENT_LEAVE = "leave"
EVENT_ARM = "arm"
EVENT_ENTRY = "entry"
EVENT_TRIGGER = "trigger"
EVENT_FAILED_TO_ARM = "failed_to_arm"
EVENT_COMMAND_NOT_ALLOWED = "command_not_allowed"
EVENT_INVALID_CODE_PROVIDED = "invalid_code_provided"
EVENT_NO_CODE_PROVIDED = "no_code_provided"
EVENT_TRIGGER_TIME_EXPIRED = "trigger_time_expired"

ARM_MODE_TO_STATE = {
    "away": STATE_ALARM_ARMED_AWAY,
    "home": STATE_ALARM_ARMED_HOME,
    "night": STATE_ALARM_ARMED_NIGHT,
    "custom": STATE_ALARM_ARMED_CUSTOM_BYPASS,
    "vacation": STATE_ALARM_ARMED_VACATION,
}

MODES_TO_SUPPORTED_FEATURES = {
    STATE_ALARM_ARMED_AWAY: AlarmControlPanelEntityFeature.ARM_AWAY,
    STATE_ALARM_ARMED_HOME: AlarmControlPanelEntityFeature.ARM_HOME,
    STATE_ALARM_ARMED_NIGHT: AlarmControlPanelEntityFeature.ARM_NIGHT,
    STATE_ALARM_ARMED_CUSTOM_BYPASS: AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_VACATION: AlarmControlPanelEntityFeature.ARM_VACATION,
}

ATTR_IS_OVERRIDE_CODE = "is_override_code"

ARM_MODES = [STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_CUSTOM_BYPASS, STATE_ALARM_ARMED_VACATION]

SERVICE_ARM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_CODE, default=""): cv.string,
        vol.Optional(CONF_MODE, default=STATE_ALARM_ARMED_AWAY): vol.In(
            [
                "away",
                "home",
                "night",
                "custom",
                "vacation",
                STATE_ALARM_ARMED_AWAY,
                STATE_ALARM_ARMED_HOME,
                STATE_ALARM_ARMED_NIGHT,
                STATE_ALARM_ARMED_CUSTOM_BYPASS,
                STATE_ALARM_ARMED_VACATION,
            ]
        ),
        vol.Optional(ATTR_SKIP_DELAY, default=False): cv.boolean,
        vol.Optional(ATTR_FORCE, default=False): cv.boolean,
        vol.Optional(ATTR_CONTEXT_ID): int,
    }
)

SERVICE_DISARM_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id, vol.Optional(CONF_CODE, default=""): cv.string, vol.Optional(ATTR_CONTEXT_ID): int})
