"""Config flow for hikvision_axpro integration."""
import logging
import voluptuous as vol
import bcrypt
import base64

from typing import Any, Final
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .hikax import HikAx
from . import const

_LOGGER = logging.getLogger(__name__)


CONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_HIK_HOST, default=const.DEFAULT_HOST): cv.string,
        vol.Required(const.CONF_HIK_USERNAME, default=const.DEFAULT_USERNAME): cv.string,
        vol.Required(const.CONF_HIK_PASSWORD, default=const.DEFAULT_PASSWORD): cv.string,
        vol.Optional(const.CONF_HIK_CODE_ARM_REQUIRED, default=const.DEFAULT_CODE_ARM_REQUIRED): cv.boolean,
        vol.Required(const.CONF_HIK_CODE_DISARM_REQUIRED, default=const.DEFAULT_CODE_DISARM_REQUIRED): cv.boolean,
        vol.Optional(const.CONF_HIK_CODE, default=const.DEFAULT_CODE): str,
        vol.Required(const.CONF_HIK_MASTER_ENABLED, default=const.DEFAULT_MASTER_ENABLED): cv.boolean,
        vol.Optional(const.CONF_HIK_MASTER_NAME, default=const.DEFAULT_MASTER_NAME): cv.string,
        vol.Required(const.CONF_HIK_SCAN_INTERVAL, default=const.DEFAULT_SCAN_INTERVAL.total_seconds()): int,
        vol.Optional(const.CONF_HIK_ENABLE_DEBUG_OUTPUT, default=const.DEFAULT_ENABLE_DEBUG_OUTPUT): cv.boolean,
    }
)


def schema_defaults(schema, dps_list=None, **defaults):
    """Create a new schema with default values filled in."""
    copy = schema.extend({})

    for field, field_type in copy.schema.items():
        if isinstance(field_type, vol.In):
            value = None

            for dps in dps_list or []:
                if dps.startswith(f"{defaults.get(field)} "):
                    value = dps
                    break

            if value in field_type.container:
                field.default = vol.default_factory(value)
                continue

        if field.schema in defaults:
            field.default = vol.default_factory(defaults[field])
    return copy


class AxHub:
    """Helper class for validation and setup ops."""

    def __init__(self, host: str, username: str, password: str, hass: HomeAssistant) -> None:
        self.axpro = HikAx(host, username, password)
        self.hass = hass

    async def authenticate(self) -> bool:
        """Check the provided credentials by connecting to ax pro."""
        is_connect_success = await self.hass.async_add_executor_job(self.axpro.connect)

        return is_connect_success


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    if data[const.CONF_HIK_CODE_ARM_REQUIRED] or data[const.CONF_HIK_CODE_DISARM_REQUIRED]:
        if data[const.CONF_HIK_CODE] is None or data[const.CONF_HIK_CODE] == "" or len(data[const.CONF_HIK_CODE]) < 4:
            raise InvalidCode

    hub = AxHub(data[const.CONF_HIK_HOST], data[const.CONF_HIK_USERNAME], data[const.CONF_HIK_PASSWORD], hass)

    if not await hub.authenticate():
        raise InvalidAuth

    return {"title": f"{const.DOMAIN}_{data[const.CONF_HIK_HOST]}"}


async def format_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    data_master: dict = {}
    data_master[const.CONF_HIK_NAME] = data[const.CONF_HIK_MASTER_NAME]
    data_master[const.CONF_HIK_ENABLED] = data[const.CONF_HIK_MASTER_ENABLED]

    data[const.CONF_HIK_MASTER_CONFIG] = data_master

    del data[const.CONF_HIK_MASTER_NAME]
    del data[const.CONF_HIK_MASTER_ENABLED]

    data_alarm: dict = {}
    data_alarm[const.CONF_HIK_USERNAME] = data[const.CONF_HIK_USERNAME]
    data_alarm[const.CONF_HIK_CODE_ARM_REQUIRED] = data[const.CONF_HIK_CODE_ARM_REQUIRED]
    data_alarm[const.CONF_HIK_CODE_DISARM_REQUIRED] = data[const.CONF_HIK_CODE_DISARM_REQUIRED]
    data_alarm[const.CONF_HIK_CAN_ARM] = const.DEFAULT_CAN_ARM
    data_alarm[const.CONF_HIK_CAN_DISARM] = const.DEFAULT_CAN_DISARM
    data_alarm[const.CONF_HIK_AREA_LIMIT] = const.DEFAULT_AREA_LIMIT
    data_alarm[const.CONF_HIK_ZONE_BYPASS] = const.DEFAULT_ZONE_BYPASS

    if len(data[const.CONF_HIK_CODE]) >= 4:
        data_alarm[const.CONF_HIK_CODE_LENGTH] = len(data[const.CONF_HIK_CODE])
        data_alarm[const.CONF_HIK_CODE_FORMAT] = const.CodeFormat.NUMBER if data[const.CONF_HIK_CODE].isdigit() else const.CodeFormat.TEXT

        hashed = bcrypt.hashpw(data[const.CONF_HIK_CODE].encode("utf-8"), bcrypt.gensalt(rounds=12))
        hashed = base64.b64encode(hashed)

        data_alarm[const.CONF_HIK_CODE] = hashed.decode()
    else:
        data_alarm[const.CONF_HIK_CODE_LENGTH] = 0
        data_alarm[const.CONF_HIK_CODE_FORMAT] = const.CodeFormat.NUMBER
        data_alarm[const.CONF_HIK_CODE] = ""

    data[const.CONF_HIK_ALARM_CONFIG] = data_alarm

    del data[const.CONF_HIK_CODE_ARM_REQUIRED]
    del data[const.CONF_HIK_CODE_DISARM_REQUIRED]
    del data[const.CONF_HIK_CODE]

    return data


class AxProConfigFlow(config_entries.ConfigFlow, domain=const.DOMAIN):
    """Handle a config flow for hikvision_axpro."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow for this handler."""
        return AxProOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=CONFIGURE_SCHEMA)

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except InvalidCode:
            errors["base"] = "invalid_code"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            user_input = await format_config(user_input)

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=CONFIGURE_SCHEMA, errors=errors)


class AxProOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for AxPro integration."""

    def __init__(self, config_entry):
        """Initialize AxPro options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage basic options."""
        defaults = self.config_entry.data.copy()
        defaults.update(user_input or {})

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=schema_defaults(CONFIGURE_SCHEMA, **defaults),
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except InvalidCode:
            errors["base"] = "invalid_code"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            _LOGGER.debug("Saving options %s %s", info["title"], user_input)

            user_input = await format_config(user_input)

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=user_input,
            )

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="init", data_schema=schema_defaults(CONFIGURE_SCHEMA, None, **defaults), errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidCode(HomeAssistantError):
    """Error to indicate the code is in wrong format"""
