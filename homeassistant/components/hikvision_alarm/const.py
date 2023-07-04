"""Constants for the hikvision_axpro integration."""
import voluptuous as vol

from datetime import timedelta
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
    CONF_MODE,
    CONF_CODE,
    ATTR_CODE,
    ATTR_NAME,
    STATE_ON,
    STATE_OFF,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    ATTR_CODE_FORMAT,
    SERVICE_RELOAD,
    ATTR_SERVICE,
    CONF_SERVICE_DATA,
    ATTR_ENTITY_ID,
    CONF_TYPE,
    STATE_UNAVAILABLE,
    STATE_OPEN,
    STATE_CLOSED,
    UnitOfTemperature,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    Platform,
)
from homeassistant.components.alarm_control_panel.const import ATTR_CODE_ARM_REQUIRED, CodeFormat
from typing import Final
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature
from homeassistant.helpers import config_validation as cv

DOMAIN: Final[str] = "hikvision_alarm"
DATA_COORDINATOR: Final[str] = "coordinator"
DATA_AREAS: Final[str] = "areas"
DATA_MASTER: Final[str] = "master"

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON]

NAME = "Alarm"
MANUFACTURER = "Hikvision"

CONF_HIK_HOST: Final[str] = CONF_HOST
CONF_HIK_USERNAME: Final[str] = CONF_USERNAME
CONF_HIK_PASSWORD: Final[str] = CONF_PASSWORD
CONF_HIK_CODE_ARM_REQUIRED: Final[str] = ATTR_CODE_ARM_REQUIRED
CONF_HIK_CODE_DISARM_REQUIRED: Final[str] = "code_disarm_required"
CONF_HIK_CODE: Final[str] = CONF_CODE
CONF_HIK_CODE_LENGTH: Final[str] = "code_length"
CONF_HIK_CODE_FORMAT: Final[str] = "code_format"
CONF_HIK_SERVER_CONFIG: Final[str] = "server_config"
CONF_HIK_MASTER_CONFIG: Final[str] = "master_config"
CONF_HIK_MASTER_ENABLED: Final[str] = "master_enabled"
CONF_HIK_MASTER_NAME: Final[str] = "master_name"
CONF_HIK_SCAN_INTERVAL: Final[str] = "scan_interval"
CONF_HIK_ENABLE_DEBUG_OUTPUT: Final[str] = "enable_debug_output"
CONF_HIK_NAME: Final[str] = "name"
CONF_HIK_ENABLED: Final[str] = "enabled"
CONF_HIK_ALARM_CONFIG: Final[str] = "alarm_config"
CONF_HIK_CAN_ARM: Final[str] = "can_arm"
CONF_HIK_CAN_DISARM: Final[str] = "can_disarm"
CONF_HIK_AREA_LIMIT: Final[str] = "area_limit"
CONF_HIK_ZONE_BYPASS: Final[str] = "zone_bypass"

DEFAULT_HOST: Final[str] = ""
DEFAULT_USERNAME: Final[str] = ""
DEFAULT_PASSWORD: Final[str] = ""
DEFAULT_CODE_ARM_REQUIRED: Final[bool] = True
DEFAULT_CODE_DISARM_REQUIRED: Final[bool] = True
DEFAULT_CODE: Final[str] = ""
DEFAULT_MASTER_ENABLED: Final[bool] = True
DEFAULT_MASTER_NAME: Final[str] = "Master"
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=5)
DEFAULT_ENABLE_DEBUG_OUTPUT: Final[bool] = True
DEFAULT_CAN_ARM: Final[bool] = False
DEFAULT_CAN_DISARM: Final[bool] = False
DEFAULT_AREA_LIMIT: Final = []
DEFAULT_ZONE_BYPASS: Final[bool] = False

ATTR_TYPE = "type"
ATTR_AREA = "area"
ATTR_MASTER = "master"
ATTR_ENABLED = "enabled"
ATTR_AREA_LIMIT = "area_limit"

ATTR_IS_OVERRIDE_CODE = "is_override_code"
ATTR_AREA_LIMIT = "area_limit"
ATTR_CODE_FORMAT = "code_format"
ATTR_CODE_LENGTH = "code_length"

ATTR_FORCE = "force"
ATTR_SKIP_DELAY = "skip_delay"
ATTR_CONTEXT_ID = "context_id"

ATTR_MODES = "modes"
ATTR_ARM_MODE = "arm_mode"
ATTR_CODE_DISARM_REQUIRED = "code_disarm_required"
ATTR_REMOVE = "remove"
ATTR_OLD_CODE = "old_code"

ATTR_TRIGGERS = "triggers"
ATTR_ACTIONS = "actions"
ATTR_EVENT = "event"
ATTR_REQUIRE_CODE = "require_code"

ATTR_NOTIFICATION = "notification"
ATTR_VERSION = "version"

COMMAND_ARM_NIGHT = "arm_night"
COMMAND_ARM_AWAY = "arm_away"
COMMAND_ARM_HOME = "arm_home"
COMMAND_ARM_CUSTOM_BYPASS = "arm_custom_bypass"
COMMAND_ARM_VACATION = "arm_vacation"
COMMAND_DISARM = "disarm"

SENSOR_TYPE_OTHER = "other"


class Endpoints:
    Session_Capabilities = "/ISAPI/Security/sessionLogin/capabilities?username="
    Session_Login = "/ISAPI/Security/sessionLogin"
    Session_Logout = "/ISAPI/Security/sessionLogout"
    Alarm_Disarm = "/ISAPI/SecurityCP/control/disarm/{}"
    Alarm_ArmAway = "/ISAPI/SecurityCP/control/arm/{}?ways=away"
    Alarm_ArmHome = "/ISAPI/SecurityCP/control/arm/{}?ways=stay"
    SubSystemStatus = "/ISAPI/SecurityCP/status/subSystems"
    ZonesConfig = "/ISAPI/SecurityCP/Configuration/zones"
    Areas_Config = "/ISAPI/SecurityCP/Configuration/subSys"
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

    get_users = "/ISAPI/Security/users"
    get_config_user = "/ISAPI/Security/UserPermission/"


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

PUSH_EVENT = "mobile_app_notification_action"
EVENT_ACTION_FORCE_ARM = "ALARMO_FORCE_ARM"
EVENT_ACTION_RETRY_ARM = "ALARMO_RETRY_ARM"
EVENT_ACTION_DISARM = "ALARMO_DISARM"

EVENT_ARM_FAILURE = "arm_failure"

ARM_MODE_TO_STATE = {
    "away": STATE_ALARM_ARMED_AWAY,
    "home": STATE_ALARM_ARMED_HOME,
    "night": STATE_ALARM_ARMED_NIGHT,
    "custom": STATE_ALARM_ARMED_CUSTOM_BYPASS,
    "vacation": STATE_ALARM_ARMED_VACATION,
}

STATE_TO_ARM_MODE = {
    STATE_ALARM_ARMED_AWAY: "away",
    STATE_ALARM_ARMED_HOME: "home",
    STATE_ALARM_ARMED_NIGHT: "night",
    STATE_ALARM_ARMED_CUSTOM_BYPASS: "custom",
    STATE_ALARM_ARMED_VACATION: "vacation",
}

MODES_TO_SUPPORTED_FEATURES = {
    STATE_ALARM_ARMED_AWAY: AlarmControlPanelEntityFeature.ARM_AWAY,
    STATE_ALARM_ARMED_HOME: AlarmControlPanelEntityFeature.ARM_HOME,
    STATE_ALARM_ARMED_NIGHT: AlarmControlPanelEntityFeature.ARM_NIGHT,
    STATE_ALARM_ARMED_CUSTOM_BYPASS: AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_VACATION: AlarmControlPanelEntityFeature.ARM_VACATION,
}


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

SERVICE_DISARM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_CODE, default=""): cv.string,
        vol.Optional(ATTR_CONTEXT_ID): int,
    }
)
