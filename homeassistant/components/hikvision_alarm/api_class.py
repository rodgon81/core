import logging
from enum import Enum
from typing import Any, List, Optional, TypeVar, Callable, Type, cast

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_none(x: Any) -> Any:
    assert x is None
    return x


def try_get(obj: Any, x):
    try:
        data = obj.get(x)
    except:
        _LOGGER.debug("No se encuentra la clave: %s", x)
        return None
    else:
        return data


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def detector_model_to_name(model_id: Optional[str]) -> str:
    if model_id == "0x00001":
        return "Passive Infrared Detector"
    if model_id == "0x00005":
        return "Slim Magnetic Contact"
    if model_id == "0x00006":
        return "Magnetic Contact"
    if model_id == "0x00012":
        return "Wireless PIR CAM Detector"
    if model_id == "0x00015":
        return "Wireless Smoke Detector"
    if model_id == "0x00017":
        return "Wireless Magnet Shock Detector"
    if model_id == "0x00018":
        return "Glass Break Detector"
    if model_id == "0x00026":
        return "Wireless Temperature Humidity Detector"
    if model_id == "0x00028":
        return "Wireless External Magnet Detector"
    if model_id == "0x00032":
        return "Wireless PIR AM Curtain Detector"
    if model_id is not None:
        return str(model_id)
    return "Hikvision"


class AccessModuleType(Enum):
    LOCAL_TRANSMITTER = "localTransmitter"
    MULTI_TRANSMITTER = "multiTransmitter"
    LOCAL_ZONE = "localZone"
    LOCAL_RELAY = "localRelay"
    LOCAL_SIREN = "localSiren"
    KEYPAD = "keypad"
    # Undocumented type
    INPUT_MAIN_ZONE = "inputMainZone"


class DetectorType(Enum):
    ACTIVE_IR_DETECTOR = "activeInfraredDetector"
    CONTROL_SWITCH = "controlSwitch"
    DISPLACEMENT_DETECTOR = "displacementDetector"
    DOOR_CONTACT = "singleInfraredDetector"
    DOOR_MAGNETIC_CONTACT_DETECTOR = "magneticContact"
    DUAL_TECHNOLOGY_MOTION_DETECTOR = "dualTechnologyPirDetector"
    DYNAMIC_SWITCH = "dynamicSwitch"
    GAS_DETECTOR = "combustibleGasDetector"
    GLASS_BREAK_DETECTOR = "glassBreakDetector"
    HUMIDITY_DETECTOR = "humidityDetector"
    INDOOR_DUAL_TECHNOLOGY_DETECTOR = "indoorDualTechnologyDetector"
    IR_CURTAIN_DETECTOR = "curtainInfraredDetector"
    MAGNET_SHOCK_DETECTOR = "magnetShockDetector"
    PANIC_BUTTON = "panicButton"
    PIRCAM_DETECTOR = "pircam"
    PIR_DETECTOR = "passiveInfraredDetector"
    SHOCK_DETECTOR = "vibrationDetector"
    SLIM_MAGNETIC_CONTACT = "slimMagneticContact"
    SMART_LOCK = "smartLock"
    SMOKE_DETECTOR = "smokeDetector"
    TEMPERATURE_DETECTOR = "temperatureDetector"
    TRIPLE_TECHNOLOGY_DETECTOR = "tripleTechnologyPirDetector"
    WATER_DETECTOR = "waterDetector"
    WATER_LEAK_DETECTOR = "waterLeakDetector"
    WIRELESS_CODETECTOR = "wirelessCODetector"
    WIRELESS_DTAMCURTAIN_DETECTOR = "wirelessDTAMCurtainDetector"
    WIRELESS_EXTERNAL_MAGNET_DETECTOR = "wirelessExternalMagnetDetector"
    WIRELESS_GLASS_BREAK_DETECTOR = "wirelessGlassBreakDetector"
    WIRELESS_HEAT_DETECTOR = "wirelessHeatDetector"
    WIRELESS_PIRCEILING_DETECTOR = "wirelessPIRCeilingDetector"
    WIRELESS_PIRCURTAIN_DETECTOR = "wirelessPIRCurtainDetector"
    WIRELESS_SINGLE_INPUT_EXPANDER = "singleZoneModule"
    WIRELESS_SMOKE_DETECTOR = "wirelessSmokeDetector"
    WIRELESS_TEMPERATURE_HUMIDITY_DETECTOR = "wirelessTemperatureHumidityDetector"
    OTHER = "other"


class Status(Enum):
    ONLINE = "online"
    TRIGGER = "trigger"
    OFFLINE = "offline"
    BREAK_DOWN = "breakDown"
    HEART_BEAT_ABNORMAL = "heartbeatAbnormal"
    NOT_RELATED = "notRelated"


class ZoneAttrib(Enum):
    WIRED = "wired"
    WIRELESS = "wireless"


class ModuleType(Enum):
    LOCAL_WIRED = "localWired"
    EXTEND_WIRED = "extendWired"
    EXTEND_WIRELESS = "extendWireless"


class ZoneType(Enum):
    """delay zone"""

    DELAY = "Delay"
    """ panic zone """
    EMERGENCY = "Emergency"
    """ fire zone """
    FIRE = "Fire"
    """ follow zone """
    FOLLOW = "Follow"
    """ gas zone """
    GAS = "Gas"
    """ key """
    KEY = "Key"
    """ medical zone """
    MEDICAL = "Medical"
    """ disabled zone """
    NON_ALARM = "Non-Alarm"
    """ 24 - hour silent zone """
    NO_SOUND_24 = "24hNoSound"
    """ perimeter zone """
    PERIMETER = "Perimeter"
    """ timeout zone """
    TIMEOUT = "Timeout"
    """ instant zone """
    INSTANT = "Instant"


class Arming(Enum):
    AWAY = "away"
    STAY = "stay"
    VACATION = "vacation"
    DISARM = "disarm"
    ARMING = "arming"


class AMMode(Enum):
    ARM = "arm"


class ArmModeConf(Enum):
    AND = "and"
    OR = "or"


class ArmMode(Enum):
    WIRELESS = "wireless"
    WIRED = "wired"


class ChimeWarningType(Enum):
    SINGLE = "single"
    CONTINUOUS = "continuous"


class DetectorAccessMode(Enum):
    NO = "NO"


class DetectorWiringMode(Enum):
    SEOL = "SEOL"


class NewKeyZoneTriggerTypeCFG(Enum):
    ZONE_STATUS = "zoneStatus"


class Relator(Enum):
    APP = "app"
    HOST = "host"


class TimeoutType(Enum):
    RECOVER = "recover"
    TIGGER = "tigger"


class ZoneStatusCFG(Enum):
    TRIGGER_ARM = "triggerArm"
