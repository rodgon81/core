"""Config flow for hikvision_axpro integration."""
import logging
import voluptuous as vol
import bcrypt
import base64

from typing import Any
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult, FlowHandler
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


def schema_defaults(schema, **defaults):
    """Create a new schema with default values filled in."""
    copy = schema.extend({})

    _LOGGER.debug("defaults: %s", defaults)
    _LOGGER.debug("copy: %s", copy)

    for field, field_type in copy.schema.items():
        _LOGGER.debug("field.schema: %s", field.schema)
        if field.schema in defaults:
            _LOGGER.debug("field.default: %s", field.default)
            field.default = vol.default_factory(defaults[field])
            _LOGGER.debug("field.default: %s", field.default)
            _LOGGER.debug("vol.default_factory: %s", vol.default_factory)
    return copy


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    if data[const.CONF_HIK_CODE_ARM_REQUIRED] or data[const.CONF_HIK_CODE_DISARM_REQUIRED]:
        if data[const.CONF_HIK_CODE] is None or data[const.CONF_HIK_CODE] == "" or len(data[const.CONF_HIK_CODE]) < 4:
            raise InvalidCode

    axpro = HikAx(data[const.CONF_HIK_HOST], data[const.CONF_HIK_USERNAME], data[const.CONF_HIK_PASSWORD])

    if not await hass.async_add_executor_job(axpro.connect):
        raise InvalidAuth

    return {"title": f"{const.DOMAIN}_{data[const.CONF_HIK_HOST]}"}


async def format_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    server_config: dict = {}
    server_config[const.CONF_HIK_HOST] = data[const.CONF_HIK_HOST]
    server_config[const.CONF_HIK_USERNAME] = data[const.CONF_HIK_USERNAME]
    server_config[const.CONF_HIK_PASSWORD] = data[const.CONF_HIK_PASSWORD]
    data[const.CONF_HIK_SERVER_CONFIG] = server_config

    del data[const.CONF_HIK_HOST]
    del data[const.CONF_HIK_USERNAME]
    del data[const.CONF_HIK_PASSWORD]

    master_config: dict = {}
    master_config[const.CONF_HIK_NAME] = data[const.CONF_HIK_MASTER_NAME]
    master_config[const.CONF_HIK_ENABLED] = data[const.CONF_HIK_MASTER_ENABLED]
    data[const.CONF_HIK_MASTER_CONFIG] = master_config

    del data[const.CONF_HIK_MASTER_NAME]
    del data[const.CONF_HIK_MASTER_ENABLED]

    alarm_config: dict = {}
    alarm_config[const.CONF_HIK_USERNAME] = data[const.CONF_HIK_SERVER_CONFIG][const.CONF_HIK_USERNAME]
    alarm_config[const.CONF_HIK_CODE_ARM_REQUIRED] = data[const.CONF_HIK_CODE_ARM_REQUIRED]
    alarm_config[const.CONF_HIK_CODE_DISARM_REQUIRED] = data[const.CONF_HIK_CODE_DISARM_REQUIRED]
    alarm_config[const.CONF_HIK_CAN_ARM] = const.DEFAULT_CAN_ARM
    alarm_config[const.CONF_HIK_CAN_DISARM] = const.DEFAULT_CAN_DISARM
    alarm_config[const.CONF_HIK_AREA_LIMIT] = const.DEFAULT_AREA_LIMIT
    alarm_config[const.CONF_HIK_ZONE_BYPASS] = const.DEFAULT_ZONE_BYPASS

    if len(data[const.CONF_HIK_CODE]) >= 4:
        alarm_config[const.CONF_HIK_CODE_LENGTH] = len(data[const.CONF_HIK_CODE])
        alarm_config[const.CONF_HIK_CODE_FORMAT] = const.CodeFormat.NUMBER if data[const.CONF_HIK_CODE].isdigit() else const.CodeFormat.TEXT

        hashed = bcrypt.hashpw(data[const.CONF_HIK_CODE].encode("utf-8"), bcrypt.gensalt(rounds=12))
        hashed = base64.b64encode(hashed)

        alarm_config[const.CONF_HIK_CODE] = hashed.decode()
    else:
        alarm_config[const.CONF_HIK_CODE_LENGTH] = 0
        alarm_config[const.CONF_HIK_CODE_FORMAT] = const.CodeFormat.NUMBER
        alarm_config[const.CONF_HIK_CODE] = ""

    data[const.CONF_HIK_ALARM_CONFIG] = alarm_config

    del data[const.CONF_HIK_CODE_ARM_REQUIRED]
    del data[const.CONF_HIK_CODE_DISARM_REQUIRED]
    del data[const.CONF_HIK_CODE]

    return data


class AxProConfigFlow(ConfigFlow, domain=const.DOMAIN):
    """Handle a config flow for hikvision_axpro."""

    VERSION = "1.0.0"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get options flow for this handler."""
        return AxProOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""

        defaults = user_input or {}

        return await flow_handler(self, defaults, user_input, "user")


class AxProOptionsFlowHandler(OptionsFlow):
    """Handle options flow for AxPro integration."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize AxPro options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage basic options."""
        _LOGGER.debug("user_input: %s", user_input)

        defaults = self.config_entry.data.copy()
        defaults.update(user_input or {})

        return await flow_handler(self, defaults, user_input, "init")


async def flow_handler(self: FlowHandler, defaults, user_input, step: str) -> FlowResult:
    if user_input is None:
        return self.async_show_form(
            step_id=step,
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
        user_input = await format_config(user_input)

        _LOGGER.debug("Saving options %s %s", info["title"], user_input)

        # self.hass.config_entries.async_update_entry(
        #   self.config_entry,
        #   data=user_input,
        # )

        return self.async_create_entry(title=info["title"], data=user_input)

    return self.async_show_form(
        step_id=step,
        data_schema=schema_defaults(CONFIGURE_SCHEMA, **defaults),
        errors=errors,
    )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidCode(HomeAssistantError):
    """Error to indicate the code is in wrong format"""
