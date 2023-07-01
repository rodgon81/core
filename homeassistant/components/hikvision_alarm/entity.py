"""A entity class for Bravia TV integration."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HikAlarmDataUpdateCoordinator
from .const import MANUFACTURER, DOMAIN


class HikAlarmEntity(CoordinatorEntity[HikAlarmDataUpdateCoordinator]):
    """BraviaTV entity class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HikAlarmDataUpdateCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.id}_{key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.id)},
            manufacturer=MANUFACTURER,
            name=coordinator.device_name,
            model=coordinator.device_model,
            sw_version=coordinator.firmware_version,
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

        self.entity_id = f"{domain}.{coordinator.device_name}-{type}-Zone_{zone_id_str}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(coordinator.id) + "-" + str(self.zone_id))},
        )
