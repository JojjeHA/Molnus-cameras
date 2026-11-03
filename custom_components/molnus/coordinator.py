
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MolnusApiClient

_LOGGER = logging.getLogger(__name__)


def _parse_dt(value: str | None) -> datetime:
    """Parse Molnus ISO datetime (often ends with Z)."""
    if not value:
        return datetime.min

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.min


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
        self.limit = max(1, int(limit))
        self.scan_interval_s = int(scan_interval_s)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest images from Molnus."""

        try:
            images = await self.client.get_images(
                camera_id=self.camera_id,
                offset=0,
                limit=self.limit,
                wildlife_required=self.wildlife_required,
            )

            # Always select the newest image, regardless of API order.
            images_sorted: list[dict[str, Any]] = sorted(
                images or [],
                key=lambda x: _parse_dt(
                    x.get("captureDate") or x.get("createdAt")
                ),
                reverse=True,
            )

            latest = images_sorted[0] if images_sorted else {}

            return {
                "images": images_sorted,
                "latest": latest,
            }

        except ConfigEntryAuthFailed:
            raise

        except ClientResponseError as err:
            if err.status in (401, 403):
                raise ConfigEntryAuthFailed(
                    "Molnus authentication failed"
                ) from err

            raise UpdateFailed(
                f"Molnus API request failed: HTTP {err.status}"
            ) from err

        except Exception as err:
            raise UpdateFailed(
                f"Molnus update failed: {err}"
            ) from err
