import voluptuous as vol
import logging
import homeassistant.util.dt as dt_util
from typing import Any

from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.websocket_api import decorators, async_register_command, ActiveConnection, BASE_COMMAND_MESSAGE_SCHEMA

# from .coordinator import HikAlarmDataUpdateCoordinator
# from .alarm_control_panel import AlarmoAreaEntity, AlarmoMasterEntity
from .const import DOMAIN, DATA_COORDINATOR, DATA_AREAS, DATA_MASTER, CONF_HIK_CODE_ARM_REQUIRED, CONF_HIK_CODE_DISARM_REQUIRED, CONF_HIK_CODE_FORMAT

_LOGGER = logging.getLogger(__name__)


@callback
@decorators.websocket_command(
    {
        vol.Required("type"): "hikvision_alarm/updated",
    }
)
@decorators.async_response
async def handle_subscribe_updates(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]):
    """Handle subscribe updates."""

    # con esto desde el cliente damos inicio a la comunicacion wensoket con el servidor y de esta forma el servidor reenvia los eventos al cliente
    @callback
    def async_handle_event(event: str, area_id: str, args: dict = {}):
        """Forward events to websocket."""
        data = dict(**args, **{"event": event, "area_id": area_id})

        connection.send_message({"id": msg["id"], "type": "event", "event": {"data": data}})

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, "alarmo_event", async_handle_event)

    connection.send_result(msg["id"])


@callback
def websocket_get_config(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]):
    """Publish config data."""
    result = ""

    for (key, val) in hass.data[DOMAIN].items():
        coordinator = val[DATA_COORDINATOR]
        config = coordinator.store.async_get_alarm_config()

        result = {
            CONF_HIK_CODE_ARM_REQUIRED: config[CONF_HIK_CODE_ARM_REQUIRED],
            CONF_HIK_CODE_DISARM_REQUIRED: config[CONF_HIK_CODE_DISARM_REQUIRED],
            CONF_HIK_CODE_FORMAT: config[CONF_HIK_CODE_FORMAT],
        }

    connection.send_result(msg["id"], result)


@callback
def websocket_get_alarm_entities(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]):
    """Publish alarm entity data."""
    result = ""

    for (key, val) in hass.data[DOMAIN].items():
        result = [{"entity_id": entity.entity_id, "area_id": area_id} for (area_id, entity) in val[DATA_AREAS].items()]

        if val[DATA_MASTER]:
            result.append({"entity_id": val[DATA_MASTER].entity_id, "area_id": 0})

    connection.send_result(msg["id"], result)


@callback
def websocket_get_countdown(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]):
    """Publish countdown time for alarm entity."""
    entity_id = msg["entity_id"]
    result = ""

    for (key, val) in hass.data[DOMAIN].items():
        item = next((entity for entity in val[DATA_AREAS].values() if entity.entity_id == entity_id), None)

        if val[DATA_MASTER] and not item and val[DATA_MASTER].entity_id == entity_id:
            item = val[DATA_MASTER]

        result = {"delay": item.delay if item else 0, "remaining": round((item.expiration - dt_util.utcnow()).total_seconds(), 2) if item and item.expiration else 0}

    connection.send_result(msg["id"], result)


async def async_register_websockets(hass: HomeAssistant):
    async_register_command(
        hass,
        "hikvision_alarm/config",
        websocket_get_config,
        BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/config"}),
    )
    async_register_command(
        hass,
        "hikvision_alarm/entities",
        websocket_get_alarm_entities,
        BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/entities"}),
    )
    async_register_command(
        hass,
        "hikvision_alarm/countdown",
        websocket_get_countdown,
        BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/countdown", vol.Required("entity_id"): cv.entity_id}),
    )
    async_register_command(
        hass,
        handle_subscribe_updates,
    )
