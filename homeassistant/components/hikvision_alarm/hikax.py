import hashlib
import logging
import urllib.parse
import xmltodict
import requests

from typing import Any
from datetime import datetime

from .const import Endpoints, Method, MsgType, UrlApi, ArmType, OutputState, ApiPayloadArm
from . import errors

_LOGGER = logging.getLogger(__name__)


class SessionLoginCap:
    def __init__(self, session_id, challenge, iterations, is_irreversible, session_id_version, salt):
        self.session_id = session_id
        self.challenge = challenge
        self.iterations = iterations
        self.is_irreversible = is_irreversible
        self.session_id_version = session_id_version
        self.salt = salt


class HikAx:
    """HikVisison Ax Pro Alarm panel coordinator."""

    def __init__(self, host, username, password):
        self.host = host
        self.username = urllib.parse.quote(username)
        self.password = urllib.parse.quote(password)
        self.cookie = ""
        self.is_connected = False
        self.url_base = f"http://{self.host}"

    def _serialize_object(self, username, encoded_password, session_id, session_id_version):
        result = f"<SessionLogin>"
        result += f"<userName>{username}</userName>"
        result += f"<password>{encoded_password}</password>"
        result += f"<sessionID>{session_id}</sessionID>"
        result += f"<sessionIDVersion>{session_id_version}</sessionIDVersion>"
        result += f"</SessionLogin>"

        return result

    def _get_session_params(self):
        url = Endpoints.session_capabilities.url.replace("{}", self.username)

        response = requests.get(f"http://{self.username}:{self.password}@{self.host}{url}")

        _LOGGER.debug("response get_session_params: %s", response.text)

        if response.status_code == 200:
            try:
                xml = xmltodict.parse(response.text)

                return SessionLoginCap(
                    session_id=xml["SessionLoginCap"]["sessionID"],
                    challenge=xml["SessionLoginCap"]["challenge"],
                    iterations=int(xml["SessionLoginCap"]["iterations"]),
                    is_irreversible=bool(xml["SessionLoginCap"]["isIrreversible"]),
                    session_id_version=xml["SessionLoginCap"]["sessionIDVersion"],
                    salt=xml["SessionLoginCap"]["salt"],
                )
            except:
                raise errors.IncorrectResponseContentError()
        else:
            return None

    def _encode_password(self, session_cap: SessionLoginCap):
        if session_cap.is_irreversible:
            result = hashlib.sha256(str(f"{self.username}{session_cap.salt}{self.password}").encode("utf-8")).hexdigest()
            result = hashlib.sha256(str(f"{result}{session_cap.challenge}").encode("utf-8")).hexdigest()

            for i in range(2, session_cap.iterations):
                result = hashlib.sha256(str(result).encode("utf-8")).hexdigest()
        else:
            result = None

        return result

    def connect_to_alarm(self):
        if self.is_connected:
            return True

        params = self._get_session_params()

        if params is None:
            _LOGGER.error("Respuesta no esperada al pedir parametros de sesion")
            return False

        xml = self._serialize_object(self.username, self._encode_password(params), params.session_id, params.session_id_version)
        _LOGGER.debug("xml: %s", xml)

        # timestamp: int = datetime.timestamp(datetime.now())

        session_login_url = f"{self.url_base}{Endpoints.session_login.url}"

        _LOGGER.debug("session_login_url: %s", session_login_url)

        result = False

        try:
            login_response: requests.Response = requests.post(session_login_url, xml)

            _LOGGER.debug("login_response: %s", login_response.text)

            if login_response.status_code == 200:
                cookie = login_response.headers.get("Set-Cookie")

                if cookie is None:
                    xml = xmltodict.parse(login_response.text)
                    session_id = (xml["SessionLogin"]["sessionID"],)

                    if session_id is not None:
                        cookie = "WebSession=" + session_id
                else:
                    self.cookie = cookie.split(";")[0]

                if cookie is None:
                    raise Exception("No cookie provided")

                self.cookie = cookie
                self.is_connected = True

                _LOGGER.info("Login exitoso")
                result = True
        except Exception as e:
            _LOGGER.error("Error in parsing response", exc_info=e)
            result = False

        return result

    @staticmethod
    def _build_url(url: str, msg_type: MsgType):
        is_json: bool = False

        if msg_type is MsgType.JSON:
            is_json = True

        param_prefix = "&" if "?" in url else "?"

        return f"{url}{param_prefix}format=json" if is_json else url

    def _make_request(self, url: str, msg_type: MsgType, method: Method, data) -> requests.Response | None:
        if self.is_connected:
            headers = {"Cookie": self.cookie}

            if method == Method.GET:
                return requests.get(url, headers=headers)
            elif method == Method.POST:
                if msg_type is MsgType.JSON:
                    return requests.post(url, json=data, headers=headers)
                else:
                    return requests.post(url, data=data, headers=headers)
            elif method == Method.PUT:
                if msg_type is MsgType.JSON:
                    return requests.put(url, json=data, headers=headers)
                else:
                    return requests.put(url, data=data, headers=headers)
            else:
                _LOGGER.debug("Metodo (%s) no valido", method)

                return None
        else:
            _LOGGER.debug("No estamos conectados al servidor")

            return None

    def _base_request(self, url_api: UrlApi, id: int = None, data: dict = None):
        url = url_api.url.replace("{}", str(id)) if id is not None else url_api.url
        url = self._build_url(f"{self.url_base}{url}", url_api.msg_type)

        _LOGGER.info("Data send: %s", data)

        response = self._make_request(url, url_api.msg_type, url_api.method, data)

        if response is None:
            return None

        if response.status_code != 200:
            raise errors.UnexpectedResponseCodeError(response.status_code, response.text)

        if response.status_code == 200:
            if url_api.msg_type is MsgType.JSON:
                return response.json()
            elif url_api.msg_type is MsgType.XML:
                return xmltodict.parse(response.text)
            else:
                return response.text

    # ---

    def session_logout(self):
        return self._base_request(Endpoints.session_logout)

    # ---

    def get_user_info(self):
        return self._base_request(Endpoints.user_info)

    def get_user_config(self, user_id: int):
        return self._base_request(Endpoints.user_config, user_id)

    # ---

    def zone_config(self):
        return self._base_request(Endpoints.zone_config)

    def zone_status(self):
        return self._base_request(Endpoints.zone_status)

    def zone_bypass_on(self, zone_id: int):
        return self._base_request(Endpoints.zone_bypass_on, zone_id)

    def zone_bypass_off(self, zone_id: int):
        return self._base_request(Endpoints.zone_bypass_off, zone_id)

    # ---

    def get_area_config(self):
        return self._base_request(Endpoints.area_config)

    def area_status(self):
        return self._base_request(Endpoints.area_status)

    def area_alarm_arm_stay(self, area_id: int):
        return self._base_request(Endpoints.area_alarm_arm_stay, area_id)

    def area_alarm_arm_away(self, area_id: int):
        return self._base_request(Endpoints.area_alarm_arm_away, area_id)

    def area_alarm_disarm(self, area_id: int):
        return self._base_request(Endpoints.area_alarm_disarm, area_id)

    def area_clear_alarm(self, area_id: int):
        return self._base_request(Endpoints.area_alarm_clear, area_id)

    def master_alarm_arm(self, area_list: list[ApiPayloadArm]):
        sub_sys: list = []

        for area in area_list:
            area_config = {"SubSys": {"id": area.area_id, "armType": area.arm_type}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1,"armType":"stay"}}]}:
        # {"SubSysList":[{"SubSys":{"id":1,"armType":"stay"}},{"SubSys":{"id":29,"armType":"stay"}}]}:

        # {"SubSysList":[{"SubSys":{"id":1,"armType":"away"}}]}:
        # {"SubSysList":[{"SubSys":{"id":1,"armType":"away"}},{"SubSys":{"id":29,"armType":"away"}}]}:

        return self._base_request(Endpoints.master_alarm_arm, None, data)

    def master_alarm_disarm(self, area_id_list: list[int]):
        sub_sys: list = []

        for area_id in area_id_list:
            area_config = {"SubSys": {"id": area_id}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1}}]}:
        # {"SubSysList":[{"SubSys":{"id":1}},{"SubSys":{"id":29}}]}:

        return self._base_request(Endpoints.master_alarm_disarm, None, data)

    def master_clear_alarm(self, area_id_list: list[int]):
        sub_sys: list = []

        for area_id in area_id_list:
            area_config = {"SubSys": {"id": area_id}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1}}]}:
        # {"SubSysList":[{"SubSys":{"id":1}},{"SubSys":{"id":29}}]}:

        return self._base_request(Endpoints.master_alarm_clear, None, data)

    def arm_fault_status(self, area_id_list: list[int]):
        sub_sys: list = []

        for area_id in area_id_list:
            area_config = {"SubSys": {"id": area_id}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1}}]}:
        # {"SubSysList":[{"SubSys":{"id":1}},{"SubSys":{"id":29}}]}:

        return self._base_request(Endpoints.arm_fault_status, None, data)

    def arm_fault_clear(self, area_id_list: list[int]):
        sub_sys: list = []

        for area_id in area_id_list:
            area_config = {"SubSys": {"id": area_id, "preventFaultArm": False}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1,"preventFaultArm":false}}]}:
        # {"SubSysList":[{"SubSys":{"id":1,"preventFaultArm":false}},{"SubSys":{"id":29,"preventFaultArm":false}}]}:

        return self._base_request(Endpoints.arm_fault_clear, None, data)

    def arm_status(self, area_id_list: list[int]):
        sub_sys: list = []

        for area_id in area_id_list:
            area_config = {"SubSys": {"id": area_id}}
            sub_sys.append(area_config)

        data = {"SubSysList": sub_sys}

        # {"SubSysList":[{"SubSys":{"id":1}}]}:
        # {"SubSysList":[{"SubSys":{"id":1}},{"SubSys":{"id":29}}]}:

        return self._base_request(Endpoints.arm_status, None, data)

    # ---

    def relay_config(self):
        return self._base_request(Endpoints.relay_config)

    def siren_config(self):
        return self._base_request(Endpoints.siren_config)

    def relay_set_state(self, state: bool, relay_id_list: list[int]):
        output_id_list: list = []

        for relay_id in relay_id_list:
            output_id = {"id": relay_id}
            output_id_list.append(output_id)

        output_state = OutputState.open if state else OutputState.close

        data = {"OutputsCtrl": {"switch": output_state, "List": output_id_list}}

        # {"OutputsCtrl":{"switch":"open","List":[{"id":0}]}}:
        # {"OutputsCtrl":{"switch":"close","List":[{"id":0}]}}:

        return self._base_request(Endpoints.relay_set_state, 1, data)

    def siren_set_state(self, state: bool, siren_id_list: list[int]):
        output_id_list: list = []

        for siren_id in siren_id_list:
            output_id = {"id": siren_id}
            output_id_list.append(output_id)

        output_state = OutputState.open if state else OutputState.close

        data = {"SirenCtrl": {"switch": output_state, "List": output_id_list}}

        # {"SirenCtrl":{"switch":"open","List":[{"id":1}]}}:
        # {"SirenCtrl":{"switch":"close","List":[{"id":1}]}}:

        return self._base_request(Endpoints.siren_set_state, 1, data)

    def output_status(self):
        return self._base_request(Endpoints.output_status)

    # ---

    def battery_status(self):
        return self._base_request(Endpoints.battery_status)

    def communication_status(self):
        return self._base_request(Endpoints.communication_status)

    def device_info(self):
        return self._base_request(Endpoints.device_info)
