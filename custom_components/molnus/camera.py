from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CAMERA_ID
from .coordinator import MolnusCoordinator
from .api import MolnusApiClient


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: MolnusCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client: MolnusApiClient = hass.data[DOMAIN][entry.entry_id]["client"]
    camera_id = entry.data[CONF_CAMERA_ID]
    async_add_entities([MolnusLatestCamera(coordinator, client, camera_id)], True)


class MolnusLatestCamera(CoordinatorEntity[MolnusCoordinator], Camera):
    _attr_name = "Molnus Latest"
    _attr_has_entity_name = True

    def __init__(self, coordinator: MolnusCoordinator, client: MolnusApiClient, camera_id: str) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._client = client
        self._camera_id = camera_id
        self._attr_unique_id = f"molnus_{camera_id}_camera_latest"

        self._last_url: str | None = None
        self._last_bytes: bytes | None = None

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        latest = self.coordinator.data.get("latest") or {}
        url = latest.get("url")
        if not url:
            return None

        # Cache by URL (new upload => new URL)
        if self._last_url == url and self._last_bytes is not None:
            return self._last_bytes

        img = await self._client.fetch_bytes(url)
        self._last_url = url
        self._last_bytes = img
        return img
