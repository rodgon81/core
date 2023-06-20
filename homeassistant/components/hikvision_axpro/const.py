"""Constants for the hikvision_axpro integration."""

from typing import Final


DOMAIN: Final[str] = "hikvision_axpro"
DATA_COORDINATOR: Final[str] = "hikaxpro"
USE_CODE_ARMING: Final[str] = "use_code_arming"
ALLOW_SUBSYSTEMS: Final[str] = "allow_subsystems"
ENABLE_DEBUG_OUTPUT: Final[str] = "debug"


class Endpoints:
    Session_Capabilities = "/ISAPI/Security/sessionLogin/capabilities?username="
    Session_Login = "/ISAPI/Security/sessionLogin"
    Session_Logout = "/ISAPI/Security/sessionLogout"
    Alarm_Disarm = "/ISAPI/SecurityCP/control/disarm/{}"
    Alarm_ArmAway = "/ISAPI/SecurityCP/control/arm/{}?ways=away"
    Alarm_ArmHome = "/ISAPI/SecurityCP/control/arm/{}?ways=stay"
    SubSystemStatus = "/ISAPI/SecurityCP/status/subSystems"
    AlertStream = "/ISAPI/Event/notification/alertStream"
    DetectorConfig = "/ISAPI/SecurityCP/BasicParam/DetectorCfg"
    DetectorConfigCap = "/ISAPI/SecurityCP/BasicParam/DetectorCfg/capabilities"
    Caps = "/ISAPI/SecurityCP/capabilities"
    CheckResultCap = "/ISAPI/SecurityCP/CheckResult/capabilities"
    CheckResult = "/ISAPI/SecurityCP/CheckResult"
    ConfCap = "/ISAPI/SecurityCP/Configuration/capabilities"
    ZonesConfig = "/ISAPI/SecurityCP/Configuration/zones"
    DeviceTime = "/ISAPI/SecurityCP/Configuration/deviceTime"
    EventRecordCap = "/ISAPI/SecurityCP/Configuration/eventRecord/channels/2/capabilities"
    EventRecord = "/ISAPI/SecurityCP/Configuration/eventRecord/channels/1"
    FaultCheck = "/ISAPI/SecurityCP/Configuration/faultCheckCfg"
    GlassBreakDetector = "/ISAPI/SecurityCP/Configuration/glassBreakDetector/zone/5"
    MagneticContact = "/ISAPI/SecurityCP/Configuration/magneticContact/zone/0"
    PublicSubSystem = "/ISAPI/SecurityCP/Configuration/publicSubSys"
    ZonesCap = "/ISAPI/SecurityCP/Configuration/zones/capabilities"
    Zones = "/ISAPI/SecurityCP/Configuration/zones/"
    ArmStatus = "/ISAPI/SecurityCP/status/armStatus"
    StatusCap = "/ISAPI/SecurityCP/status/capabilities"
    HostStatus = "/ISAPI/SecurityCP/status/host"
    PeripheralsStatus = "/ISAPI/SecurityCP/status/exDevStatus"
    ZoneStatus = "/ISAPI/SecurityCP/status/zones"
    BypassZone = "/ISAPI/SecurityCP/control/bypass/"
    RecoverBypassZone = "/ISAPI/SecurityCP/control/Recoverbypass/"
    InterfaceInfo = "/ISAPI/System/Network/interfaces"
    AreaArmStatus = "/ISAPI/SecurityCP/status/armStatus"
    SirenStatus = "/ISAPI/SecurityCP/status/sirenStatus"
    RepeaterStatus = "/ISAPI/SecurityCP/status/repeaterStatus"
    KeypadStatus = "/ISAPI/SecurityCP/status/keypadStatus"
    DeviceInfo = "/ISAPI/System/deviceInfo"


class Method:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


XML_SERIALIZABLE_NAMES = ["SessionLogin", "userName",
                          "password", "sessionID", "sessionIDVersion"]
