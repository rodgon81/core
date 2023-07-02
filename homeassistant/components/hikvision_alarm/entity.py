"""A entity class for Bravia TV integration."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify

from .coordinator import HikAlarmDataUpdateCoordinator
from .const import MANUFACTURER, DOMAIN, DATA_COORDINATOR


def device_registry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator: HikAlarmDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    device_registry = dr.async_get(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.id)},
        manufacturer=MANUFACTURER,
        name=coordinator.device_name,
        model=coordinator.device_model,
        sw_version=coordinator.firmware_version,
    )

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(coordinator.id) + "-zone_group")},
        manufacturer=MANUFACTURER,
        name="Zonas",
        model="Zonas de Alarma",
        via_device=(DOMAIN, str(coordinator.id)),
    )

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(coordinator.id) + "-sirenas_group")},
        manufacturer=MANUFACTURER,
        name="Sirenas",
        model="Sirenas de Alarma",
        via_device=(DOMAIN, str(coordinator.id)),
    )

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(coordinator.id) + "-reles_group")},
        manufacturer=MANUFACTURER,
        name="Reles",
        model="Reles de Alarma",
        via_device=(DOMAIN, str(coordinator.id)),
    )

    if coordinator.zone_status is not None:
        for zone in coordinator.zone_status.zone_list:
            zone_config = coordinator.devices.get(zone.zone.id)

            device_registry.async_get_or_create(
                config_entry_id=coordinator.entry.entry_id,
                identifiers={(DOMAIN, str(coordinator.id) + "-" + str(zone_config.id))},
                manufacturer=MANUFACTURER,
                name=zone_config.zone_name,
                model="Zona de Alarma",
                via_device=((DOMAIN, str(coordinator.id) + "-zone_group")),
            )


class HikAlarmEntity(CoordinatorEntity[HikAlarmDataUpdateCoordinator]):
    """BraviaTV entity class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, key: str, domain: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.id}_{key}"
        self.entity_id = f"{domain}.{slugify(coordinator.device_name)}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for device registry."""

        return DeviceInfo(
            identifiers={(DOMAIN, str(self.coordinator.id))},
        )


class HikZoneEntity(CoordinatorEntity[HikAlarmDataUpdateCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, zone_id: int, type: str, domain: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self.zone_id: int = zone_id

        self._attr_unique_id = f"{coordinator.id}_{type}_Zone_{self.zone_id}"

        zone_id = self.zone_id + 1
        zone_id_str: str = zone_id

        if zone_id < 10:
            zone_id_str = f"0{zone_id}"

        self.entity_id = f"{domain}.{slugify(coordinator.device_name)}_{type}_Zone_{zone_id_str}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for device registry."""

        return DeviceInfo(
            identifiers={(DOMAIN, str(self.coordinator.id) + "-" + str(self.zone_id))},
        )
