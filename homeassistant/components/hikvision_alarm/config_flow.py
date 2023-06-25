"""Config flow for hikvision_axpro integration."""
import logging
import voluptuous as vol

from typing import Any, Final
from .hikax import HikAx
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from datetime import timedelta
from homeassistant.const import (
    CONF_CODE,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    ATTR_NAME,
    ATTR_CODE_FORMAT,
)
from . import HikAxProDataUpdateCoordinator
from homeassistant.helpers import config_validation as cv

from homeassistant.components.alarm_control_panel import (
    CodeFormat,
    ATTR_CODE_ARM_REQUIRED,
)

from . import const

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL: Final = timedelta(seconds=5)

CONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.9"): cv.string,
        vol.Required(CONF_USERNAME, default="admin"): cv.string,
        vol.Required(CONF_PASSWORD, default="Elparaiso81"): cv.string,
        vol.Optional(ATTR_CODE_ARM_REQUIRED, default=True): cv.boolean,
        vol.Required(const.ATTR_CODE_DISARM_REQUIRED, default=True): cv.boolean,
        vol.Required(ATTR_CODE_FORMAT, default=CodeFormat.NUMBER): vol.In([CodeFormat.NUMBER, CodeFormat.TEXT]),
        vol.Required(const.ATTR_ENABLED, default=True): cv.boolean,
        vol.Optional(ATTR_NAME, default="Maestro"): cv.string,
        vol.Optional(const.CONF_CODE, default="2854"): str,
        vol.Required(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL.total_seconds()): int,
        vol.Optional(const.CONF_ENABLE_DEBUG_OUTPUT, default=True): cv.boolean,
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
        self.host = host
        self.username = username
        self.password = password
        self.axpro = HikAx(host, username, password)
        self.hass = hass

    async def authenticate(self) -> bool:
        """Check the provided credentials by connecting to ax pro."""
        is_connect_success = await self.hass.async_add_executor_job(self.axpro.connect)
        return is_connect_success


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    if data[ATTR_CODE_ARM_REQUIRED] or data[const.ATTR_CODE_DISARM_REQUIRED]:
        if data[CONF_CODE] is None or data[CONF_CODE] == "" or not str.isdigit(data[CONF_CODE]):
            raise InvalidCode

    hub = AxHub(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD], hass)

    if not await hub.authenticate():
        raise InvalidAuth

    return {"title": f"{const.DOMAIN}_{data[CONF_HOST]}"}


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

            coordinator: HikAxProDataUpdateCoordinator = self.hass.data[const.DOMAIN][const.DATA_COORDINATOR]
            await coordinator.async_update_config(user_input)

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
