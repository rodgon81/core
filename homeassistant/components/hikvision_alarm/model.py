import logging
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Optional, TypeVar

from .api_class import (
    from_int,
    from_bool,
    from_str,
    from_none,
    from_list,
    from_float,
    from_union,
    to_enum,
    to_class,
    try_get,
    Status,
    ZoneType,
    Arming,
    Relator,
    DetectorType,
    TimeoutType,
    ZoneAttrib,
    ModuleType,
)

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


@dataclass
class ZoneStatus:
    id: int
    name: str
    status: Optional[Status]
    tamper_evident: Optional[bool]
    shielded: Optional[bool]
    bypassed: Optional[bool]
    armed: Optional[bool]
    alarm: Optional[bool]
    zone_type: Optional[ZoneType]
    signal: Optional[int]

    @staticmethod
    def from_dict(obj: Any) -> "ZoneStatus":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        name = from_str(obj.get("name"))
        status = Status(obj.get("status"))
        tamper_evident = from_union([from_bool, from_none], obj.get("tamperEvident"))
        shielded = from_union([from_bool, from_none], obj.get("shielded"))
        bypassed = from_union([from_bool, from_none], obj.get("bypassed"))
        armed = from_union([from_bool, from_none], obj.get("armed"))
        alarm = from_union([from_bool, from_none], obj.get("alarm"))
        zone_type = from_union([ZoneType, from_none], obj.get("zoneType"))
        signal = from_union([from_int, from_none], obj.get("signal"))

        return ZoneStatus(
            id,
            name,
            status,
            tamper_evident,
            shielded,
            bypassed,
            armed,
            alarm,
            zone_type,
            signal,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["name"] = from_str(self.name)
        result["status"] = to_enum(Status, self.status)
        result["tamperEvident"] = from_bool(self.tamper_evident)
        result["shielded"] = from_bool(self.shielded)
        result["bypassed"] = from_bool(self.bypassed)
        result["armed"] = from_bool(self.armed)
        result["alarm"] = from_bool(self.alarm)
        result["zoneType"] = to_enum(ZoneType, self.zone_type)
        result["signal"] = from_union([from_int, from_none], self.signal)

        return result


@dataclass
class ZoneStatusList:
    zone: ZoneStatus

    @staticmethod
    def from_dict(obj: Any) -> "ZoneStatusList":
        assert isinstance(obj, dict)

        zone = ZoneStatus.from_dict(obj.get("Zone"))

        return ZoneStatusList(zone)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Zone"] = to_class(ZoneStatus, self.zone)

        return result


@dataclass
class ZonesStatus:
    zone_list: List[ZoneStatusList]

    @staticmethod
    def from_dict(obj: Any) -> "ZonesStatus":
        assert isinstance(obj, dict)

        zone_list = from_list(ZoneStatusList.from_dict, obj.get("ZoneList"))

        return ZonesStatus(zone_list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["ZoneList"] = from_list(lambda x: to_class(ZoneStatusList, x), self.zone_list)

        return result


@dataclass
class SirenStatus:
    id: int
    name: str
    status: bool
    tamper_evident: bool
    siren_attrib: str

    @staticmethod
    def from_dict(obj: Any) -> "SirenStatus":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        name = from_str(obj.get("name"))
        status = True if obj.get("status") == "on" else False
        tamper_evident = from_bool(obj.get("tamperEvident"))
        siren_attrib = from_str(obj.get("sirenAttrib"))

        return SirenStatus(
            id,
            name,
            status,
            tamper_evident,
            siren_attrib,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["name"] = from_str(self.name)
        result["status"] = from_bool(self.status)
        result["tamperEvident"] = from_bool(self.tamper_evident)
        result["sirenAttrib"] = from_str(self.siren_attrib)

        return result


@dataclass
class SirenStatusList:
    siren: SirenStatus

    @staticmethod
    def from_dict(obj: Any) -> "SirenStatusList":
        assert isinstance(obj, dict)

        siren = SirenStatus.from_dict(obj.get("Siren"))

        return SirenStatusList(siren)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Siren"] = to_class(SirenStatus, self.siren)

        return result


@dataclass
class SirensStatus:
    siren_list: List[SirenStatusList]

    @staticmethod
    def from_dict(obj: Any) -> "SirensStatus":
        assert isinstance(obj, dict)

        pre_obj = obj.get("ExDevStatus")
        assert isinstance(pre_obj, dict)
        siren_list = from_list(SirenStatusList.from_dict, pre_obj.get("SirenList"))

        return SirensStatus(siren_list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["SirenList"] = from_list(lambda x: to_class(ZoneStatusList, x), self.siren_list)

        return result


@dataclass
class RelayStatus:
    id: int
    name: str
    status: bool
    tamper_evident: bool

    @staticmethod
    def from_dict(obj: Any) -> "RelayStatus":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        name = from_str(obj.get("name"))
        status = True if obj.get("status") == "on" else False
        tamper_evident = from_bool(obj.get("tamperEvident"))

        return RelayStatus(
            id,
            name,
            status,
            tamper_evident,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["name"] = from_str(self.name)
        result["status"] = from_bool(self.status)
        result["tamperEvident"] = from_bool(self.tamper_evident)

        return result


@dataclass
class RelayStatusList:
    relay: RelayStatus

    @staticmethod
    def from_dict(obj: Any) -> "RelayStatusList":
        assert isinstance(obj, dict)

        relay = RelayStatus.from_dict(obj.get("Output"))

        return RelayStatusList(relay)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Output"] = to_class(RelayStatus, self.relay)

        return result


@dataclass
class RelaysStatus:
    relay_list: List[RelayStatusList]

    @staticmethod
    def from_dict(obj: Any) -> "RelaysStatus":
        assert isinstance(obj, dict)

        pre_obj = obj.get("ExDevStatus")
        assert isinstance(pre_obj, dict)
        relay_list = from_list(RelayStatusList.from_dict, pre_obj.get("OutputList"))

        return RelaysStatus(relay_list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["OutputList"] = from_list(lambda x: to_class(RelayStatusList, x), self.relay_list)

        return result


@dataclass
class SubSys:
    id: int
    arming: Arming
    alarm: bool
    enabled: bool
    name: str
    delay_time: int

    @staticmethod
    def from_dict(obj: Any) -> "SubSys":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        arming = Arming(obj.get("arming"))
        alarm = from_bool(obj.get("alarm"))
        enabled = from_union([from_bool, from_none], obj.get("enabled"))
        name = from_union([from_str, from_none], obj.get("name"))
        delay_time = 10

        return SubSys(id, arming, alarm, enabled, name, delay_time)

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["arming"] = to_enum(Arming, self.arming)
        result["alarm"] = from_bool(self.alarm)
        result["enabled"] = from_bool(self.enabled)
        result["name"] = from_str(self.name)
        result["delayTime"] = from_int(self.delay_time)

        return result


@dataclass
class SubSysList:
    sub_sys: SubSys

    @staticmethod
    def from_dict(obj: Any) -> "SubSysList":
        assert isinstance(obj, dict)

        sub_sys = SubSys.from_dict(obj.get("SubSys"))

        return SubSysList(sub_sys)

    def to_dict(self) -> dict:
        result: dict = {}

        result["SubSys"] = to_class(SubSys, self.sub_sys)

        return result


@dataclass
class SubSystemResponse:
    sub_sys_list: List[SubSysList]

    @staticmethod
    def from_dict(obj: Any) -> "SubSystemResponse":
        assert isinstance(obj, dict)

        sub_sys_list = from_list(SubSysList.from_dict, obj.get("SubSysList"))

        return SubSystemResponse(sub_sys_list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["SubSysList"] = from_list(lambda x: to_class(SubSysList, x), self.sub_sys_list)

        return result


@dataclass
class RelatedChan:
    camera_seq: str
    related_chan: int
    linkage_camera_name: Optional[str] = None
    relator: Optional[Relator] = None

    @staticmethod
    def from_dict(obj: Any) -> "RelatedChan":
        assert isinstance(obj, dict)

        camera_seq = from_str(obj.get("cameraSeq"))
        related_chan = from_int(obj.get("relatedChan"))
        linkage_camera_name = from_union([from_str, from_none], obj.get("linkageCameraName"))
        relator = from_union([Relator, from_none], obj.get("relator"))

        return RelatedChan(camera_seq, related_chan, linkage_camera_name, relator)

    def to_dict(self) -> dict:
        result: dict = {}

        result["cameraSeq"] = from_str(self.camera_seq)
        result["relatedChan"] = from_int(self.related_chan)
        result["linkageCameraName"] = from_union([from_str, from_none], self.linkage_camera_name)
        result["relator"] = from_union([lambda x: to_enum(Relator, x), from_none], self.relator)

        return result


@dataclass
class RelatedChanList:
    related_chan: RelatedChan

    @staticmethod
    def from_dict(obj: Any) -> "RelatedChanList":
        assert isinstance(obj, dict)

        related_chan = RelatedChan.from_dict(obj.get("RelatedChan"))

        return RelatedChanList(related_chan)

    def to_dict(self) -> dict:
        result: dict = {}

        result["RelatedChan"] = to_class(RelatedChan, self.related_chan)

        return result


@dataclass
class ZoneConfig:
    id: int
    zone_name: str
    detector_type: DetectorType
    zone_type: Optional[ZoneType]
    sub_system_no: Optional[int]
    delay_time: Optional[int]
    stay_away_enabled: Optional[bool]
    silent_enabled: Optional[bool]
    timeout_limit: Optional[bool]
    timeout_type: TimeoutType
    timeout: Optional[int]
    related_chan_list: List[RelatedChanList]
    module_channel: Optional[int]
    module_type: Optional[ModuleType]
    module_status: Optional[str]
    sensitivity: Optional[int]
    resistor: Optional[float]
    tamper_type: Optional[str]
    zone_attrib: Optional[ZoneAttrib]
    double_zone_cfg_enable: Optional[bool]
    arm_no_bypass_enabled: Optional[bool]
    double_knock_enabled: Optional[bool]
    double_knock_time: Optional[int]
    address: Optional[int]
    trans_Method: Optional[str]
    check_time: Optional[int]
    linkage_address: Optional[int]
    detector_seq: Optional[str]
    relate_detector: Optional[bool]

    @staticmethod
    def from_dict(obj: Any) -> "ZoneConfig":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        zone_name = from_str(obj.get("zoneName"))
        detector_type = DetectorType(obj.get("detectorType"))
        zone_type = from_union([ZoneType, from_none], obj.get("zoneType"))
        sub_system_no = from_union([from_int, from_none], try_get(obj, "subSystemNo"))
        delay_time = from_union([from_int, from_none], obj.get("delayTime"))
        stay_away_enabled = from_bool(obj.get("stayAwayEnabled"))
        silent_enabled = from_bool(obj.get("silentEnabled"))
        timeout_limit = from_union([from_bool, from_none], obj.get("timeoutLimit"))
        timeout_type = TimeoutType(obj.get("timeoutType"))
        timeout = from_int(obj.get("timeout"))
        related_chan_list = from_list(RelatedChanList.from_dict, obj.get("RelatedChanList"))
        module_channel = from_union([from_int, from_none], obj.get("moduleChannel"))

        module_type = from_union([ModuleType, from_none], obj.get("moduleType"))

        if module_type == ModuleType.EXTEND_WIRED:
            address = from_int(obj.get("address"))
            trans_Method = from_str(obj.get("transMethod"))
        else:
            address = None
            trans_Method = None

        module_status = from_str(obj.get("moduleStatus"))
        zone_attrib = from_union([ZoneAttrib, from_none], obj.get("zoneAttrib"))

        if zone_attrib == ZoneAttrib.WIRED:
            sensitivity = from_int(obj.get("sensitivity"))
            resistor = from_float(obj.get("resistor"))
            tamper_type = from_str(obj.get("tamperType"))
        else:
            sensitivity = None
            resistor = None
            tamper_type = None

        if zone_attrib == ZoneAttrib.WIRELESS:
            check_time = from_int(obj.get("checkTime"))
            linkage_address = from_int(obj.get("linkageAddress"))
            detector_seq = from_str(obj.get("detectorSeq"))
            relate_detector = from_bool(obj.get("relateDetector"))
        else:
            check_time = None
            linkage_address = None
            detector_seq = None
            relate_detector = None

        double_zone_cfg_enable = from_union([from_bool, from_none], try_get(obj, "doubleZoneCfgEnable"))
        arm_no_bypass_enabled = from_union([from_bool, from_none], obj.get("armNoBypassEnabled"))
        double_knock_enabled = from_bool(obj.get("doubleKnockEnabled"))
        double_knock_time = from_int(obj.get("doubleKnockTime"))

        return ZoneConfig(
            id,
            zone_name,
            detector_type,
            zone_type,
            sub_system_no,
            delay_time,
            stay_away_enabled,
            silent_enabled,
            timeout_limit,
            timeout_type,
            timeout,
            related_chan_list,
            module_channel,
            module_type,
            module_status,
            sensitivity,
            resistor,
            tamper_type,
            zone_attrib,
            double_zone_cfg_enable,
            arm_no_bypass_enabled,
            double_knock_enabled,
            double_knock_time,
            address,
            trans_Method,
            check_time,
            linkage_address,
            detector_seq,
            relate_detector,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["zoneName"] = from_str(self.zone_name)
        result["detectorType"] = to_enum(DetectorType, self.detector_type)
        result["zoneType"] = to_enum(ZoneType, self.zone_type)
        result["subSystemNo"] = from_union([from_int, from_none], self.sub_system_no)
        result["delayTime"] = from_union([from_int, from_none], self.delay_time)
        result["stayAwayEnabled"] = from_bool(self.stay_away_enabled)
        result["silentEnabled"] = from_bool(self.silent_enabled)
        result["timeoutLimit"] = from_union([from_bool, from_none], self.timeout_limit)
        result["timeoutType"] = to_enum(TimeoutType, self.timeout_type)
        result["timeout"] = from_int(self.timeout)
        result["RelatedChanList"] = from_list(lambda x: to_class(RelatedChanList, x), self.related_chan_list)
        result["moduleChannel"] = from_union([from_int, from_none], self.module_channel)
        result["moduleType"] = from_str(self.module_type)
        result["moduleStatus"] = from_str(self.module_status)
        result["sensitivity"] = from_union([from_int, from_none], self.sensitivity)
        result["resistor"] = from_union([from_float, from_none], self.resistor)
        result["tamperType"] = from_union([from_str, from_none], self.tamper_type)
        result["zoneAttrib"] = from_union([lambda x: to_enum(ZoneAttrib, x), from_none], self.zone_attrib)
        result["doubleZoneCfgEnable"] = from_union([from_bool, from_none], self.double_zone_cfg_enable)
        result["armNoBypassEnabled"] = from_union([from_bool, from_none], self.arm_no_bypass_enabled)
        result["doubleKnockEnabled"] = from_bool(self.double_knock_enabled)
        result["doubleKnockTime"] = from_int(self.double_knock_time)
        result["address"] = from_union([from_int, from_none], self.address)
        result["transMethod"] = from_union([from_str, from_none], self.trans_Method)
        result["checkTime"] = from_union([from_int, from_none], self.check_time)
        result["linkageAddress"] = from_union([from_int, from_none], self.linkage_address)
        result["detectorSeq"] = from_union([from_str, from_none], self.detector_seq)
        result["relateDetector"] = from_union([from_bool, from_none], self.relate_detector)

        return result


@dataclass
class ListElement:
    zone: ZoneConfig

    @staticmethod
    def from_dict(obj: Any) -> "ListElement":
        assert isinstance(obj, dict)

        zone = ZoneConfig.from_dict(obj.get("Zone"))

        return ListElement(zone)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Zone"] = to_class(ZoneConfig, self.zone)

        return result


@dataclass
class ZonesConf:
    list: List[ListElement]

    @staticmethod
    def from_dict(obj: Any) -> "ZonesConf":
        assert isinstance(obj, dict)

        list = from_list(ListElement.from_dict, obj.get("List"))

        return ZonesConf(list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["List"] = from_list(lambda x: to_class(ListElement, x), self.list)

        return result


@dataclass
class RelayConfig:
    id: int
    name: str

    @staticmethod
    def from_dict(obj: Any, relay_id) -> "RelayConfig":
        assert isinstance(obj, dict)

        id = from_int(relay_id)
        name = from_str(obj.get("name"))

        return RelayConfig(
            id,
            name,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["name"] = from_str(self.name)

        return result


@dataclass
class ListElementRelays:
    relay: RelayConfig

    @staticmethod
    def from_dict(obj: Any) -> "ListElementRelays":
        assert isinstance(obj, dict)

        relay = RelayConfig.from_dict(obj.get("OutPutModule"), obj.get("id"))

        return ListElementRelays(relay)

    def to_dict(self) -> dict:
        result: dict = {}

        result["OutPutModule"] = to_class(RelayConfig, self.relay)

        return result


@dataclass
class RelaysConf:
    list: List[ListElementRelays]

    @staticmethod
    def from_dict(obj: Any) -> "RelaysConf":
        assert isinstance(obj, dict)

        list = from_list(ListElementRelays.from_dict, obj.get("List"))

        return RelaysConf(list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["List"] = from_list(lambda x: to_class(ListElementRelays, x), self.list)

        return result


@dataclass
class SirenConfig:
    id: int
    name: str

    @staticmethod
    def from_dict(obj: Any) -> "SirenConfig":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        name = from_str(obj.get("name"))

        return SirenConfig(
            id,
            name,
        )

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["name"] = from_str(self.name)

        return result


@dataclass
class ListElementSirens:
    siren: SirenConfig

    @staticmethod
    def from_dict(obj: Any) -> "ListElementSirens":
        assert isinstance(obj, dict)

        siren = SirenConfig.from_dict(obj.get("Siren"))

        return ListElementSirens(siren)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Siren"] = to_class(SirenConfig, self.siren)

        return result


@dataclass
class SirensConf:
    list: List[ListElementSirens]

    @staticmethod
    def from_dict(obj: Any) -> "SirensConf":
        assert isinstance(obj, dict)

        list = from_list(ListElementSirens.from_dict, obj.get("List"))

        return SirensConf(list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["List"] = from_list(lambda x: to_class(ListElementSirens, x), self.list)

        return result
