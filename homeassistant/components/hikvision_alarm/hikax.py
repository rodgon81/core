import hashlib
import logging
import urllib.parse
import xmltodict
import requests

from typing import Optional, Any
from .const import Endpoints, Method
from . import errors
from datetime import datetime


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
        self.username = username
        self.password = password
        self.cookie = ""
        self.is_connected = False

    def serialize_object(self, username, encoded_password, session_id, session_id_version):
        result = f"<SessionLogin>"
        result += f"<userName>{username}</userName>"
        result += f"<password>{encoded_password}</password>"
        result += f"<sessionID>{session_id}</sessionID>"
        result += f"<sessionIDVersion>{session_id_version}</sessionIDVersion>"
        result += f"</SessionLogin>"

        return result

    def get_session_params(self):
        q_user = urllib.parse.quote(self.username)
        q_password = urllib.parse.quote(self.password)

        response = requests.get(f"http://{q_user}:{q_password}@{self.host}{Endpoints.Session_Capabilities}{q_user}")

        _LOGGER.debug("Session_Capabilities response")
        _LOGGER.debug("Status: %s", response.status_code)
        _LOGGER.debug("Content: %s", response.content)
        _LOGGER.debug("Text: %s", response.text)
        _LOGGER.debug("Headers: %s", response.headers)
        _LOGGER.debug("End Session_Capabilities response")

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

    def encode_password(self, session_cap: SessionLoginCap):
        if session_cap.is_irreversible:
            result = hashlib.sha256(str(f"{self.username}{session_cap.salt}{self.password}").encode("utf-8")).hexdigest()
            result = hashlib.sha256(str(f"{result}{session_cap.challenge}").encode("utf-8")).hexdigest()

            for i in range(2, session_cap.iterations):
                result = hashlib.sha256(str(result).encode("utf-8")).hexdigest()
        else:
            result = None
        return result

    def connect(self):
        params = self.get_session_params()

        if params is None:
            _LOGGER.error("Respuesta no esperada al pedir parametros de sesion")
            return False

        xml = self.serialize_object(self.username, self.encode_password(params), params.session_id, params.session_id_version)

        _LOGGER.debug("xml: %s", xml)

        dt = datetime.now()
        timestamp = datetime.timestamp(dt)

        session_login_url = f"http://{self.host}{Endpoints.Session_Login}?timeStamp={int(timestamp)}"

        result = False

        try:
            login_response: requests.Response = requests.post(session_login_url, xml)

            _LOGGER.debug("Connect response")
            _LOGGER.debug("Status: %s", login_response.status_code)
            _LOGGER.debug("Content: %s", login_response.content)
            _LOGGER.debug("Text: %s", login_response.text)
            _LOGGER.debug("Headers: %s", login_response.headers)
            _LOGGER.debug("End connect response")

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

            if method == Method.GET:
                response = requests.get(endpoint, headers=headers)
            elif method == Method.POST:
                if is_json:
                    response = requests.post(endpoint, json=data, headers=headers)
                else:
                    response = requests.post(endpoint, data=data, headers=headers)
            elif method == Method.PUT:
                if is_json:
                    # _LOGGER.debug("put DISARM")
                    # _LOGGER.debug("endpoint %s", endpoint)

                    response = requests.put(endpoint, json=data, headers=headers)
                else:
                    response = requests.put(endpoint, data=data, headers=headers)
            else:
                return None

            return response
        else:
            return None

    def _base_request(self, url: str, method: Method = Method.GET, data=None, is_json: bool = True):
        endpoint = self.build_url(url, is_json)
        response = self.make_request(endpoint, method, data, is_json)

        # _LOGGER.debug("RESPONSE _base_request %s", response)

        if response.status_code != 200:
            raise errors.UnexpectedResponseCodeError(response.status_code, response.text)
        if response.status_code == 200:
            if is_json:
                return response.json()
            else:
                return response.text

    def arm_home(self, sub_id: Optional[int] = None):
        sid = "0xffffffff" if sub_id is None else str(sub_id)
        response = self._base_request(f"http://{self.host}{Endpoints.Alarm_ArmHome.replace('{}', sid)}", Method.PUT)

        # _LOGGER.debug("response = %s", response)

        return response

    def arm_away(self, sub_id: Optional[int] = None):
        sid = "0xffffffff" if sub_id is None else str(sub_id)
        response = self._base_request(f"http://{self.host}{Endpoints.Alarm_ArmAway.replace('{}', sid)}", Method.PUT)

        # _LOGGER.debug("response = %s", response)

        return response

    def disarm(self, sub_id: Optional[int] = None):
        # _LOGGER.debug("disarm en hikax")

        sid = "0xffffffff" if sub_id is None else str(sub_id)

        url = Endpoints.Alarm_Disarm.replace("{}", sid)

        response = self._base_request(f"http://{self.host}{url}", Method.PUT)

        # _LOGGER.debug("response disarm = %s", response)

        return response

    def subsystem_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.SubSystemStatus}")

    def peripherals_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.PeripheralsStatus}")

    def zone_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.ZoneStatus}")

    def bypass_zone(self, zone_id):
        return self._base_request(f"http://{self.host}{Endpoints.BypassZone}{zone_id}", Method.PUT)

    def recover_bypass_zone(self, zone_id):
        return self._base_request(f"http://{self.host}{Endpoints.RecoverBypassZone}{zone_id}", Method.PUT)

    def get_area_arm_status(self, area_id):
        data = {"SubSysList": [{"SubSys": {"id": area_id}}]}

        response = self._base_request(f"http://{self.host}{Endpoints.AreaArmStatus}", Method.POST, data)

        return response["ArmStatusList"][0]["ArmStatus"]["status"]

    def host_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.HostStatus}")

    def siren_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.SirenStatus}")

    def keypad_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.KeypadStatus}")

    def repeater_status(self):
        return self._base_request(f"http://{self.host}{Endpoints.RepeaterStatus}")

    def get_device_info(self):
        response = self._base_request(f"http://{self.host}{Endpoints.DeviceInfo}", is_json=False)

        return xmltodict.parse(response)

    def load_devices(self):
        return self._base_request(f"http://{self.host}{Endpoints.ZonesConfig}")

    def check_arm(self, area_id):
        data = {"SubSysList": [{"SubSys": {"id": area_id}}]}

        response = self._base_request(f"http://{self.host}{Endpoints.systemFault}", Method.POST, data)
        return response["ArmFault"]["status"]
