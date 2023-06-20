from typing import Optional, Any
import hashlib

import requests
from xml.etree import ElementTree
import consts
from .models import SessionLoginCap, SessionLogin
from .errors import errors
from datetime import datetime
import logging
import urllib.parse
import xmltodict

_LOGGER = logging.getLogger(__name__)


class HikAx:
    """HikVisison Ax Pro Alarm panel coordinator."""

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.cookie = ''
        self.is_connected = False

    def serialize_object(self, obj):
        result = f"<{type(obj).__name__}>"

        for prop, value in vars(obj).items():
            if prop in consts.XML_SERIALIZABLE_NAMES:
                result += f"<{prop}>{value}</{prop}>"

        result += f"</{type(obj).__name__}>"

        return result

    def get_session_params(self):
        q_user = urllib.parse.quote(self.username)
        q_password = urllib.parse.quote(self.password)

        response = requests.get(
            f"http://{q_user}:{q_password}@{self.host}{consts.Endpoints.Session_Capabilities}{q_user}")

        _LOGGER.debug("Session_Capabilities response")
        _LOGGER.debug("Status: %s", response.status_code)
        _LOGGER.debug("Content: %s", response.content)
        _LOGGER.debug("Text: %s", response.text)
        _LOGGER.debug("Headers: %s", response.headers)
        _LOGGER.debug("End Session_Capabilities response")

        if response.status_code == 200:
            try:
                session_cap = self.parse_session_response(response.text)
                return session_cap
            except:
                raise errors.IncorrectResponseContentError()
        else:
            return None

    @staticmethod
    def set_logging_level(level):
        _LOGGER.setLevel(level)

    @staticmethod
    def _root_get_value(root, ns, key, default=None) -> Any | None:
        item = root.find(key, ns)

        if item is not None:
            return item.text

        return default

    @staticmethod
    def parse_session_response(xml_data):
        root = ElementTree.fromstring(xml_data)
        namespaces = {'xmlns': consts.XML_SCHEMA}

        session_id = HikAx._root_get_value(root, namespaces, "xmlns:sessionID")
        challenge = HikAx._root_get_value(root, namespaces, "xmlns:challenge")
        iterations = HikAx._root_get_value(
            root, namespaces, "xmlns:iterations")
        is_irreversible = HikAx._root_get_value(
            root, namespaces, "xmlns:isIrreversible")
        session_id_version = HikAx._root_get_value(
            root, namespaces, "xmlns:sessionIDVersion")
        salt = HikAx._root_get_value(root, namespaces, "xmlns:salt")

        session_cap = SessionLoginCap.SessionLoginCap(
            session_id=session_id,
            challenge=challenge,
            iterations=int(iterations),
            is_irreversible=bool(is_irreversible),
            session_id_version=session_id_version,
            salt=salt
        )

        return session_cap

    def encode_password(self, session_cap: SessionLoginCap.SessionLoginCap):
        if session_cap.is_irreversible:
            result = hashlib.sha256(str(
                f"{self.username}{session_cap.salt}{self.password}").encode("utf-8")).hexdigest()
            result = hashlib.sha256(
                str(f"{result}{session_cap.challenge}").encode("utf-8")).hexdigest()

            for i in range(2, session_cap.iterations):
                result = hashlib.sha256(
                    str(result).encode("utf-8")).hexdigest()
        else:
            result = None
        return result

    def connect(self):
        params = self.get_session_params()

        if params is None:
            _LOGGER.error(
                "Respuesta no esperada al pedir parametros de sesion")
            return False

        encoded_password = self.encode_password(params)

        _LOGGER.debug("encoded_password: %s", encoded_password)

        xml = self.serialize_object(
            SessionLogin.SessionLogin(
                self.username,
                encoded_password,
                params.session_id,
                params.session_id_version
            )
        )

        _LOGGER.debug("xml: %s", xml)

        dt = datetime.now()
        timestamp = datetime.timestamp(dt)

        session_login_url = f"http://{self.host}{consts.Endpoints.Session_Login}?timeStamp={int(timestamp)}"

        result = False

        try:
            login_response: requests.Response = requests.post(
                session_login_url, xml)

            _LOGGER.debug("Connect response")
            _LOGGER.debug("Status: %s", login_response.status_code)
            _LOGGER.debug("Content: %s", login_response.content)
            _LOGGER.debug("Text: %s", login_response.text)
            _LOGGER.debug("Headers: %s", login_response.headers)
            _LOGGER.debug("End connect response")

            if login_response.status_code == 200:
                cookie = login_response.headers.get("Set-Cookie")

                if cookie is None:
                    root = ElementTree.fromstring(login_response.text)
                    namespaces = {'xmlns': consts.XML_SCHEMA}
                    session_id = HikAx._root_get_value(
                        root, namespaces, "xmlns:sessionID")

                    if session_id is not None:
                        cookie = "WebSession=" + session_id
                else:
                    self.cookie = cookie.split(";")[0]

                if cookie is None:
                    raise Exception("No cookie provided")

                self.cookie = cookie
                self.is_connected = True

                result = True
        except Exception as e:
            _LOGGER.error("Error in parsing response", exc_info=e)
            result = False

        return result

    @staticmethod
    def build_url(endpoint, is_json: bool = True):
        param_prefix = "&" if "?" in endpoint else "?"

        return f"{endpoint}{param_prefix}format=json" if is_json else endpoint

    def make_request(self, endpoint, method, data=None, is_json: bool = True):
        if self.is_connected:
            headers = {"Cookie": self.cookie}

            if method == consts.Method.GET:
                response = requests.get(endpoint, headers=headers)
            elif method == consts.Method.POST:
                if is_json:
                    response = requests.post(
                        endpoint, json=data, headers=headers)
                else:
                    response = requests.post(
                        endpoint, data=data, headers=headers)
            elif method == consts.Method.PUT:
                if is_json:
                    response = requests.put(
                        endpoint, json=data, headers=headers)
                else:
                    response = requests.put(
                        endpoint, data=data, headers=headers)
            else:
                return None

            return response
        else:
            return None

    def _base_request(self, url: str, method: consts.Method = consts.Method.GET, data=None, is_json: bool = True):
        endpoint = self.build_url(url, is_json)
        response = self.make_request(endpoint, method, is_json, data)

        _LOGGER.debug(response)

        if response.status_code != 200:
            raise errors.UnexpectedResponseCodeError(
                response.status_code, response.text)
        if response.status_code == 200:
            if is_json:
                return response.json()
            else:
                return response.text

    def arm_home(self, sub_id: Optional[int] = None):
        sid = "0xffffffff" if sub_id is None else str(sub_id)
        return self._base_request(f"http://{self.host}{consts.Endpoints.Alarm_ArmHome.replace('{}', sid)}", consts.Method.PUT)

    def arm_away(self, sub_id: Optional[int] = None):
        sid = "0xffffffff" if sub_id is None else str(sub_id)
        return self._base_request(f"http://{self.host}{consts.Endpoints.Alarm_ArmAway.replace('{}', sid)}", consts.Method.PUT)

    def disarm(self, sub_id: Optional[int] = None):
        sid = "0xffffffff" if sub_id is None else str(sub_id)
        return self._base_request(f"http://{self.host}{consts.Endpoints.Alarm_Disarm.replace('{}', sid)}", consts.Method.PUT)

    def subsystem_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.SubSystemStatus}")

    def peripherals_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.PeripheralsStatus}")

    def zone_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.ZoneStatus}")

    def bypass_zone(self, zone_id):
        return self._base_request(f"http://{self.host}{consts.Endpoints.BypassZone}{zone_id}", consts.Method.PUT)

    def recover_bypass_zone(self, zone_id):
        return self._base_request(f"http://{self.host}{consts.Endpoints.RecoverBypassZone}{zone_id}", consts.Method.PUT)

    def get_area_arm_status(self, area_id):
        data = {"SubSysList": [{"SubSys": {"id": area_id}}]}

        response = self._base_request(
            f"http://{self.host}{consts.Endpoints.AreaArmStatus}", consts.Method.POST, data)

        return response["ArmStatusList"][0]["ArmStatus"]["status"]

    def host_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.HostStatus}")

    def siren_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.SirenStatus}")

    def keypad_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.KeypadStatus}")

    def repeater_status(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.RepeaterStatus}")

    def get_device_info(self):
        response = self._base_request(
            f"http://{self.host}/ISAPI/System/deviceInfo", is_json=False)

        return xmltodict.parse(response)

    def load_devices(self):
        return self._base_request(f"http://{self.host}{consts.Endpoints.ZonesConfig}")
