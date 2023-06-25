import voluptuous as vol
import logging

from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.websocket_api import decorators, async_register_command

from . import const

import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)


@callback
@decorators.websocket_command(
    {
        vol.Required("type"): "hikvision_alarm/updated",
    }
)
@decorators.async_response
async def handle_subscribe_updates(hass, connection, msg):
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
def websocket_get_config(hass, connection, msg):
    """Publish config data."""
    coordinator = hass.data[const.DOMAIN][const.DATA_COORDINATOR]

    config = coordinator.store.async_get_config()

    connection.send_result(msg["id"], config)


@callback
def websocket_get_alarm_entities(hass, connection, msg):
    """Publish alarm entity data."""
    result = [{"entity_id": entity.entity_id, "area_id": area_id} for (area_id, entity) in hass.data[const.DOMAIN][const.DATA_AREAS].items()]

    if hass.data[const.DOMAIN][const.DATA_MASTER]:
        result.append({"entity_id": hass.data[const.DOMAIN][const.DATA_MASTER].entity_id, "area_id": 0})

    connection.send_result(msg["id"], result)


@callback
def websocket_get_countdown(hass, connection, msg):
    """Publish countdown time for alarm entity."""
    entity_id = msg["entity_id"]

    item = next((entity for entity in hass.data[const.DOMAIN][const.DATA_AREAS].values() if entity.entity_id == entity_id), None)

    if hass.data[const.DOMAIN][const.DATA_MASTER] and not item and hass.data[const.DOMAIN][const.DATA_MASTER].entity_id == entity_id:
        item = hass.data[const.DOMAIN][const.DATA_MASTER]

    data = {"delay": item.delay if item else 0, "remaining": round((item.expiration - dt_util.utcnow()).total_seconds(), 2) if item and item.expiration else 0}

    connection.send_result(msg["id"], data)


async def async_register_websockets(hass):
    async_register_command(
        hass,
        "hikvision_alarm/config",
        websocket_get_config,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/config"}),
    )
    async_register_command(
        hass,
        "hikvision_alarm/entities",
        websocket_get_alarm_entities,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/entities"}),
    )
    async_register_command(
        hass,
        "hikvision_alarm/countdown",
        websocket_get_countdown,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required("type"): "hikvision_alarm/countdown", vol.Required("entity_id"): cv.entity_id}),
    )
    async_register_command(hass, handle_subscribe_updates)
