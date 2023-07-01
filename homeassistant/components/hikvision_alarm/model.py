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
    NewKeyZoneTriggerTypeCFG,
    ZoneStatusCFG,
    ChimeWarningType,
    ArmModeConf,
    ZoneAttrib,
    DetectorAccessMode,
    DetectorWiringMode,
    AMMode,
    AccessModuleType,
    ModuleType,
)

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


@dataclass
class InputList:
    id: int
    enabled: bool
    mode: str

    @staticmethod
    def from_dict(obj: Any) -> "InputList":
        assert isinstance(obj, dict)

        id = from_int(obj.get("id"))
        enabled = from_bool(obj.get("enabled"))
        mode = from_str(obj.get("mode"))

        return InputList(id, enabled, mode)

    def to_dict(self) -> dict:
        result: dict = {}

        result["id"] = from_int(self.id)
        result["enabled"] = from_bool(self.enabled)
        result["mode"] = from_str(self.mode)

        return result


@dataclass
class Zone:
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
    def from_dict(obj: Any) -> "Zone":
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

        return Zone(
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
class ZoneList:
    zone: Zone

    @staticmethod
    def from_dict(obj: Any) -> "ZoneList":
        assert isinstance(obj, dict)

        zone = Zone.from_dict(obj.get("Zone"))

        return ZoneList(zone)

    def to_dict(self) -> dict:
        result: dict = {}

        result["Zone"] = to_class(Zone, self.zone)

        return result


@dataclass
class ZonesResponse:
    zone_list: List[ZoneList]

    @staticmethod
    def from_dict(obj: Any) -> "ZonesResponse":
        assert isinstance(obj, dict)

        zone_list = from_list(ZoneList.from_dict, obj.get("ZoneList"))

        return ZonesResponse(zone_list)

    def to_dict(self) -> dict:
        result: dict = {}

        result["ZoneList"] = from_list(lambda x: to_class(ZoneList, x), self.zone_list)

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
class CrossZoneCFG:
    is_associated: bool
    support_associated_zone: List[int]
    already_associated_zone: List[Any]
    support_linkage_channel_id: List[Any]
    already_linkage_channel_id: List[Any]
    associate_time: int

    @staticmethod
    def from_dict(obj: Any) -> "CrossZoneCFG":
        assert isinstance(obj, dict)

        is_associated = from_bool(obj.get("isAssociated"))
        support_associated_zone = from_list(from_int, obj.get("supportAssociatedZone"))
        already_associated_zone = from_list(lambda x: x, obj.get("alreadyAssociatedZone"))
        support_linkage_channel_id = from_list(lambda x: x, obj.get("supportLinkageChannelID"))
        already_linkage_channel_id = from_list(lambda x: x, obj.get("alreadyLinkageChannelID"))
        associate_time = from_int(obj.get("associateTime"))

        return CrossZoneCFG(is_associated, support_associated_zone, already_associated_zone, support_linkage_channel_id, already_linkage_channel_id, associate_time)

    def to_dict(self) -> dict:
        result: dict = {}

        result["isAssociated"] = from_bool(self.is_associated)
        result["supportAssociatedZone"] = from_list(from_int, self.support_associated_zone)
        result["alreadyAssociatedZone"] = from_list(lambda x: x, self.already_associated_zone)
        result["supportLinkageChannelID"] = from_list(lambda x: x, self.support_linkage_channel_id)
        result["alreadyLinkageChannelID"] = from_list(lambda x: x, self.already_linkage_channel_id)
        result["associateTime"] = from_int(self.associate_time)

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
class RelatedPIRCAM:
    support_linkage_zones: List[Any]
    linkage_zone: List[Any]
    linkage_pircam_name: str

    @staticmethod
    def from_dict(obj: Any) -> "RelatedPIRCAM":
        assert isinstance(obj, dict)

        support_linkage_zones = from_list(lambda x: x, obj.get("supportLinkageZones"))
        linkage_zone = from_list(lambda x: x, obj.get("linkageZone"))
        linkage_pircam_name = from_str(obj.get("linkagePIRCAMName"))

        return RelatedPIRCAM(support_linkage_zones, linkage_zone, linkage_pircam_name)

    def to_dict(self) -> dict:
        result: dict = {}

        result["supportLinkageZones"] = from_list(lambda x: x, self.support_linkage_zones)
        result["linkageZone"] = from_list(lambda x: x, self.linkage_zone)
        result["linkagePIRCAMName"] = from_str(self.linkage_pircam_name)

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
