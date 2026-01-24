from __future__ import annotations

from datetime import timedelta
from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MolnusApiClient

_LOGGER = logging.getLogger(__name__)


class MolnusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        client: MolnusApiClient,
        camera_id: str,
        wildlife_required: bool,
        limit: int,
        scan_interval_s: int,
    ) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Molnus",
            update_interval=timedelta(seconds=scan_interval_s),
        )
        self.client = client
        self.camera_id = camera_id
        self.wildlife_required = wildlife_required
        self.limit = limit

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            images = await self.client.get_images(
                camera_id=self.camera_id,
                offset=0,
                limit=max(1, self.limit),
                wildlife_required=self.wildlife_required,
            )
            latest = images[0] if images else {}
            return {"images": images, "latest": latest}
        except Exception as err:
            raise UpdateFailed(str(err)) from err
