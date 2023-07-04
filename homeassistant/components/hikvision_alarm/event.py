# fire events in HA for use with automations

import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import EVENT_FAILED_TO_ARM, EVENT_COMMAND_NOT_ALLOWED, EVENT_INVALID_CODE_PROVIDED, EVENT_NO_CODE_PROVIDED, EVENT_ARM, EVENT_DISARM, STATE_TO_ARM_MODE

_LOGGER = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, hass, entry_id):
        """Class constructor."""
        self.hass = hass
        self.entry_id = entry_id

        self._subscription = async_dispatcher_connect(self.hass, "alarmo_event", self.async_handle_event)

    def __del__(self):
        """Class destructor."""
        self._subscription()

    @callback
    async def async_handle_event(self, event: str, area_id: str, args: dict = {}):
        """handle event"""

        if event in [EVENT_FAILED_TO_ARM, EVENT_COMMAND_NOT_ALLOWED, EVENT_INVALID_CODE_PROVIDED, EVENT_NO_CODE_PROVIDED]:
            reasons = {
                EVENT_FAILED_TO_ARM: "open_sensors",
                EVENT_COMMAND_NOT_ALLOWED: "not_allowed",
                EVENT_INVALID_CODE_PROVIDED: "invalid_code",
                EVENT_NO_CODE_PROVIDED: "invalid_code",
            }

            data = dict(**args, **{"area_id": area_id, "reason": reasons[event]})

            if "open_sensors" in data:
                data["sensors"] = list(data["open_sensors"].keys())

                del data["open_sensors"]

            self.hass.bus.fire("alarmo_failed_to_arm", data)

        elif event in [EVENT_ARM, EVENT_DISARM]:
            data = dict(**args, **{"area_id": area_id, "action": event})

            if "arm_mode" in data:
                data["mode"] = STATE_TO_ARM_MODE[data["arm_mode"]]

                del data["arm_mode"]

            self.hass.bus.fire("alarmo_command_success", data)
