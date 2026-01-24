from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CAMERA_ID
from .coordinator import MolnusCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: MolnusCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    camera_id = entry.data[CONF_CAMERA_ID]
    async_add_entities([MolnusLatestImageIdSensor(coordinator, camera_id)], True)


class MolnusLatestImageIdSensor(CoordinatorEntity[MolnusCoordinator], SensorEntity):
    _attr_name = "Molnus Latest Image ID"
    _attr_icon = "mdi:camera"
    _attr_has_entity_name = True

    def __init__(self, coordinator: MolnusCoordinator, camera_id: str) -> None:
        super().__init__(coordinator)
        self._camera_id = camera_id
        self._attr_unique_id = f"molnus_{camera_id}_latest_image_id"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._camera_id)},
            name="Molnus Camera",
            manufacturer="Molnus",
            model="Cloud camera",
        )

    @property
    def native_value(self) -> Any:
        latest = self.coordinator.data.get("latest") or {}
        return latest.get("id")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self.coordinator.data.get("latest") or {}
        # Pass through useful fields for automations/notifications
        keys = [
            "url",
            "thumbnailUrl",
            "captureDate",
            "createdAt",
            "deviceFilename",
            "CameraId",
        ]
        return {k: latest.get(k) for k in keys if k in latest}
