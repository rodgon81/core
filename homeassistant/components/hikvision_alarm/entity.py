"""A entity class for Bravia TV integration."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify

from .coordinator import HikAlarmDataUpdateCoordinator
from .const import MANUFACTURER, DOMAIN, DATA_COORDINATOR
from .model import ZoneConfig, RelayConfig, SirenConfig


def format_id_base_0(zone_id: int) -> str:
    zone_id_final: int = zone_id + 1

    if zone_id_final < 10:
        return f"0{zone_id_final}"

    return str(zone_id_final)


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
        identifiers={(DOMAIN, str(coordinator.id) + "-relay_group")},
        manufacturer=MANUFACTURER,
        name="Reles",
        model="Reles de Alarma",
        via_device=(DOMAIN, str(coordinator.id)),
    )

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(coordinator.id) + "-siren_group")},
        manufacturer=MANUFACTURER,
        name="Sirenas",
        model="Sirenas de Alarma",
        via_device=(DOMAIN, str(coordinator.id)),
    )

    if coordinator.zone_config is not None:
        zone_config: ZoneConfig

        for zone_config in coordinator.zone_config.values():
            device_registry.async_get_or_create(
                config_entry_id=coordinator.entry.entry_id,
                identifiers={(DOMAIN, str(coordinator.id) + "-zone-" + str(zone_config.id))},
                manufacturer=MANUFACTURER,
                name=zone_config.zone_name,
                model=f"Zona {format_id_base_0(zone_config.id)}",
                via_device=((DOMAIN, str(coordinator.id) + "-zone_group")),
            )

    if coordinator.relay_config is not None:
        relay_config: RelayConfig

        for relay_config in coordinator.relay_config.values():
            device_registry.async_get_or_create(
                config_entry_id=coordinator.entry.entry_id,
                identifiers={(DOMAIN, str(coordinator.id) + "-relay-" + str(relay_config.id))},
                manufacturer=MANUFACTURER,
                name=relay_config.name,
                model=f"Rele {format_id_base_0(relay_config.id)}",
                via_device=((DOMAIN, str(coordinator.id) + "-relay_group")),
            )

    if coordinator.siren_config is not None:
        siren_config: SirenConfig

        for siren_config in coordinator.siren_config.values():
            device_registry.async_get_or_create(
                config_entry_id=coordinator.entry.entry_id,
                identifiers={(DOMAIN, str(coordinator.id) + "-siren-" + str(siren_config.id))},
                manufacturer=MANUFACTURER,
                name=siren_config.name,
                model=f"Sirena {siren_config.id}",
                via_device=((DOMAIN, str(coordinator.id) + "-siren_group")),
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


class HikGroupEntity(CoordinatorEntity[HikAlarmDataUpdateCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, zone_id: int, type: str, domain: str, group: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self.zone_id: int = zone_id
        self.group: str = group

        self._attr_unique_id = f"{coordinator.id}_{type}_{group}_{format_id_base_0(self.zone_id)}"
        self.entity_id = f"{domain}.{slugify(coordinator.device_name)}_{type}_{group}_{format_id_base_0(self.zone_id)}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for device registry."""

        return DeviceInfo(
            identifiers={(DOMAIN, str(self.coordinator.id) + "-" + self.group + "-" + str(self.zone_id))},
        )
