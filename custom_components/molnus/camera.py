
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CAMERA_ID
from .coordinator import MolnusCoordinator
from .api import MolnusApiClient


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: MolnusCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client: MolnusApiClient = hass.data[DOMAIN][entry.entry_id]["client"]

    camera_id = str(entry.data[CONF_CAMERA_ID])
    camera_name = (entry.title or "").strip() or "Molnus Camera"

    async_add_entities(
        [
            MolnusLatestCamera(
                coordinator,
                client,
                camera_id,
                camera_name,
            )
        ],
        True,
    )


class MolnusLatestCamera(CoordinatorEntity[MolnusCoordinator], Camera):
    _attr_name = "Latest"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MolnusCoordinator,
        client: MolnusApiClient,
        camera_id: str,
        camera_name: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)

        self._client = client
        self._camera_id = camera_id
        self._camera_name = camera_name

        # Preserve the existing unique ID.
        self._attr_unique_id = f"molnus_{camera_id}_camera_latest"

        self._last_url: str | None = None
        self._last_bytes: bytes | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._camera_id)},
            name=self._camera_name,
            manufacturer="Molnus",
            model="Wildlife camera",
        )

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        latest = self.coordinator.data.get("latest") or {}
        url = latest.get("url")

        if not url:
            return None

        # Cache by URL (new upload => new URL).
        if self._last_url == url and self._last_bytes is not None:
            return self._last_bytes

        img = await self._client.fetch_bytes(url)

        self._last_url = url
        self._last_bytes = img

        return img
