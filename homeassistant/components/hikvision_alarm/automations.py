import logging
import copy
import re

from homeassistant.core import HomeAssistant, callback, SERVICE_CALL_LIMIT
from homeassistant.components.notify import ATTR_MESSAGE
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.binary_sensor.device_condition import ENTITY_CONDITIONS
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    DATA_COORDINATOR,
    ATTR_ENABLED,
    ARM_MODES,
    ATTR_TRIGGERS,
    EVENT_FAILED_TO_ARM,
    ATTR_SERVICE,
    STATE_OPEN,
    ATTR_ACTIONS,
    CONF_SERVICE_DATA,
    ATTR_ENTITY_ID,
    CONF_TYPE,
    ATTR_NOTIFICATION,
    EVENT_ARM_FAILURE,
    STATE_CLOSED,
    STATE_UNAVAILABLE,
    ATTR_EVENT,
    ATTR_MODES,
    ATTR_AREA,
    DATA_AREAS,
    DATA_MASTER,
)

from .coordinator import HikAlarmDataUpdateCoordinator
from .alarm_control_panel import AlarmoBaseEntity

_LOGGER = logging.getLogger(__name__)


class AutomationHandler:
    def __init__(self, hass: HomeAssistant, entry_id):
        self.hass = hass
        self._config = None
        self.entry_id = entry_id
        self._subscriptions = []
        self._sensorTranslationCache = {}
        self._alarmTranslationCache = {}
        self._sensorTranslationLang = None
        self._alarmTranslationLang = None

        @callback
        def async_update_config():
            """automation config updated, reload the configuration."""
            coordinator: HikAlarmDataUpdateCoordinator = self.hass.data[DOMAIN][self.entry_id][DATA_COORDINATOR]
            self._config = coordinator.store.async_get_automations()

        self._subscriptions.append(async_dispatcher_connect(self.hass, "alarmo_automations_updated", async_update_config))

        async_update_config()

        @callback
        async def async_alarm_state_changed(area_id: str, old_state: str, new_state: str):
            if not old_state:
                # ignore automations at startup/restoring
                return
            if area_id:
                alarm_entity: AlarmoBaseEntity = self.hass.data[DOMAIN][self.entry_id][DATA_AREAS][area_id]
            else:
                alarm_entity: AlarmoBaseEntity = self.hass.data[DOMAIN][self.entry_id][DATA_MASTER]

            if not alarm_entity:
                return

            _LOGGER.debug("state of {} is updated from {} to {}".format(alarm_entity.entity_id, old_state, new_state))

            if new_state in ARM_MODES:
                # we don't distinguish between armed modes for automations, they are handled separately
                new_state = "armed"

            for automation_id, config in self._config.items():
                if not config[ATTR_ENABLED]:
                    continue
                for trigger in config[ATTR_TRIGGERS]:
                    if self.validate_area(trigger, area_id, self.hass) and self.validate_modes(trigger, alarm_entity._arm_mode) and self.validate_trigger(trigger, new_state, old_state):
                        await self.async_execute_automation(automation_id, alarm_entity)

        self._subscriptions.append(async_dispatcher_connect(self.hass, "alarmo_state_updated", async_alarm_state_changed))

        @callback
        async def async_handle_event(event: str, area_id: str, args: dict = {}):
            if event != EVENT_FAILED_TO_ARM:
                return

            if area_id:
                alarm_entity: AlarmoBaseEntity = self.hass.data[DOMAIN][self.entry_id][DATA_AREAS][area_id]
            else:
                alarm_entity: AlarmoBaseEntity = self.hass.data[DOMAIN][self.entry_id][DATA_MASTER]

            _LOGGER.debug("{} has failed to arm".format(alarm_entity.entity_id))

            for automation_id, config in self._config.items():
                if not config[ATTR_ENABLED]:
                    continue

                for trigger in config[ATTR_TRIGGERS]:
                    if self.validate_area(trigger, area_id, self.hass) and self.validate_modes(trigger, alarm_entity._arm_mode) and self.validate_trigger(trigger, EVENT_ARM_FAILURE):
                        await self.async_execute_automation(automation_id, alarm_entity)

        self._subscriptions.append(async_dispatcher_connect(self.hass, "alarmo_event", async_handle_event))

    def __del__(self):
        """prepare for removal"""
        while len(self._subscriptions):
            self._subscriptions.pop()()

    async def async_execute_automation(self, automation_id: str, alarm_entity: AlarmoBaseEntity):
        # automation is a dict of AutomationEntry
        _LOGGER.debug("Executing automation {}".format(automation_id))

        actions = self._config[automation_id][ATTR_ACTIONS]

        for action in actions:
            try:
                service_data = copy.copy(action[CONF_SERVICE_DATA])

                if ATTR_ENTITY_ID in action and action[ATTR_ENTITY_ID]:
                    service_data[ATTR_ENTITY_ID] = action[ATTR_ENTITY_ID]

                if self._config[automation_id][CONF_TYPE] == ATTR_NOTIFICATION and ATTR_MESSAGE in service_data:
                    res = re.search(r"{{open_sensors(\|lang=([^}]+))?(\|format=short)?}}", service_data[ATTR_MESSAGE])
                    if res:
                        lang = res.group(2) if res.group(2) else "en"
                        names_only = True if res.group(3) else False

                        open_sensors = ""

                        if alarm_entity.open_sensors:
                            parts = []

                            for (entity_id, status) in alarm_entity.open_sensors.items():
                                if names_only:
                                    parts.append(self.friendly_name_for_entity_id(entity_id, self.hass))
                                else:
                                    parts.append(await self.async_get_open_sensor_string(entity_id, status, lang))

                            open_sensors = ", ".join(parts)

                        service_data[ATTR_MESSAGE] = service_data[ATTR_MESSAGE].replace(res.group(0), open_sensors)

                    if "{{bypassed_sensors}}" in service_data[ATTR_MESSAGE]:
                        bypassed_sensors = ""

                        if alarm_entity.bypassed_sensors and len(alarm_entity.bypassed_sensors):
                            parts = []

                            for entity_id in alarm_entity.bypassed_sensors:
                                name = self.friendly_name_for_entity_id(entity_id, self.hass)
                                parts.append(name)

                            bypassed_sensors = ", ".join(parts)

                        service_data[ATTR_MESSAGE] = service_data[ATTR_MESSAGE].replace("{{bypassed_sensors}}", bypassed_sensors)

                    res = re.search(r"{{arm_mode(\|lang=([^}]+))?}}", service_data[ATTR_MESSAGE])

                    if res:
                        lang = res.group(2) if res.group(2) else "en"
                        arm_mode = await self.async_get_arm_mode_string(alarm_entity.arm_mode, lang)

                        service_data[ATTR_MESSAGE] = service_data[ATTR_MESSAGE].replace(res.group(0), arm_mode)

                    if "{{changed_by}}" in service_data[ATTR_MESSAGE]:
                        changed_by = alarm_entity.changed_by if alarm_entity.changed_by else ""
                        service_data[ATTR_MESSAGE] = service_data[ATTR_MESSAGE].replace("{{changed_by}}", changed_by)

                domain, service = action[ATTR_SERVICE].split(".")

                await self.hass.async_create_task(
                    self.hass.services.async_call(
                        domain,
                        service,
                        service_data,
                        blocking=True,
                        context={},
                        limit=SERVICE_CALL_LIMIT,
                    )
                )
            except HomeAssistantError as e:
                _LOGGER.error("Execution of action {} failed, reason: {}".format(automation_id, e))

    def get_automations_by_area(self, area_id: str):
        result = []

        for (automation_id, config) in self._config.items():
            if any(el[ATTR_AREA] == area_id for el in config[ATTR_TRIGGERS]):
                result.append(automation_id)

        return result

    async def async_get_open_sensor_string(self, entity_id: str, state: str, language: str):
        """get translation for sensor states"""

        if self._sensorTranslationCache and self._sensorTranslationLang == language:
            translations = self._sensorTranslationCache
        else:
            translations = await self.hass.helpers.translation.async_get_translations(language, "device_automation", ["binary_sensor"])

            self._sensorTranslationCache = translations
            self._sensorTranslationLang = language

        entity = self.hass.states.get(entity_id)

        device_type = entity.attributes["device_class"] if entity and "device_class" in entity.attributes else None

        if state == STATE_OPEN:
            translation_key = "component.binary_sensor.device_automation.condition_type.{}".format(ENTITY_CONDITIONS[device_type][0]["type"]) if device_type in ENTITY_CONDITIONS else None

            if translation_key and translation_key in translations:
                string = translations[translation_key]
            else:
                string = "{entity_name} is open"
        elif state == STATE_CLOSED:
            translation_key = "component.binary_sensor.device_automation.condition_type.{}".format(ENTITY_CONDITIONS[device_type][1]["type"]) if device_type in ENTITY_CONDITIONS else None

            if translation_key and translation_key in translations:
                string = translations[translation_key]
            else:
                string = "{entity_name} is closed"
        elif state == STATE_UNAVAILABLE:
            string = "{entity_name} is unavailable"

        else:
            string = "{entity_name} is unknown"

        name = self.friendly_name_for_entity_id(entity_id, self.hass)
        string = string.replace("{entity_name}", name)

        return string

    async def async_get_arm_mode_string(self, arm_mode: str, language: str):
        """get translation for alarm arm mode"""
        if self._alarmTranslationCache and self._alarmTranslationLang == language:
            translations = self._alarmTranslationCache
        else:
            translations = await self.hass.helpers.translation.async_get_translations(language, "entity_component", ["alarm_control_panel"])

            self._alarmTranslationCache = translations
            self._alarmTranslationLang = language

        translation_key = ("component.alarm_control_panel.entity_component._.state.{}".format(arm_mode)) if arm_mode else None

        if translation_key and translation_key in translations:
            return translations[translation_key]
        elif arm_mode:
            return " ".join(w.capitalize() for w in arm_mode.split("_"))
        else:
            return ""

    def friendly_name_for_entity_id(self, entity_id: str, hass: HomeAssistant):
        """helper to get friendly name for entity"""
        state = hass.states.get(entity_id)

        if state and state.attributes.get("friendly_name"):
            return state.attributes["friendly_name"]

        return entity_id

    def validate_area(self, trigger, area_id, hass):
        if ATTR_AREA not in trigger:
            return False
        elif trigger[ATTR_AREA]:
            return trigger[ATTR_AREA] == area_id
        elif len(hass.data[DOMAIN][self.entry_id][DATA_AREAS]) == 1:
            return True
        else:
            return area_id is None

    def validate_modes(self, trigger, mode):
        if ATTR_MODES not in trigger:
            return False
        elif not trigger[ATTR_MODES]:
            return True
        else:
            return mode in trigger[ATTR_MODES]

    def validate_trigger(self, trigger, to_state, from_state=None):
        if ATTR_EVENT not in trigger:
            return False
        elif trigger[ATTR_EVENT] == "untriggered" and from_state == "triggered":
            return True
        elif trigger[ATTR_EVENT] == to_state:
            return True
        else:
            return False
