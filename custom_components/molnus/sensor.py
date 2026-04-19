from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CAMERA_ID
from .coordinator import MolnusCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: MolnusCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    camera_id = str(entry.data[CONF_CAMERA_ID])

    entry_title = (entry.title or "").strip() or "Molnus Camera"

    async_add_entities(
        [
            MolnusLatestImageIdSensor(
                coordinator=coordinator,
                camera_id=camera_id,
                device_name=entry_title,
            )
        ],
        True,
    )


class MolnusLatestImageIdSensor(
    CoordinatorEntity[MolnusCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True
    _attr_icon = "mdi:camera-wireless"

    def __init__(
        self,
        coordinator: MolnusCoordinator,
        camera_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator)

        self._camera_id = str(camera_id)
        self._device_name = str(device_name)

        self._attr_unique_id = (
            f"molnus_{self._camera_id}_latest_image_id"
        )

        self._attr_name = "Latest image ID"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._camera_id)},
            name=self._device_name,
            manufacturer="Molnus",
            model="Wildlife camera",
        )

    @property
    def native_value(self) -> Any:
        latest = self.coordinator.data.get("latest") or {}

        image_id = latest.get("id")

        if image_id is None:
            return None

        return str(image_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self.coordinator.data.get("latest") or {}

        # NEW API uses lowercase imagePredictions
        preds = (
            latest.get("imagePredictions")
            or latest.get("ImagePredictions")
            or []
        )

        if not isinstance(preds, list):
            preds = []

        labels: list[str] = []

        for p in preds:
            if isinstance(p, dict):
                label = p.get("label")
                if label is not None:
                    labels.append(str(label))

        species_labels = sorted(set(labels))

        best = None
        best_acc = -1.0

        for p in preds:
            if not isinstance(p, dict):
                continue

            try:
                acc = float(p.get("accuracy", -1))
            except Exception:
                acc = -1.0

            if acc > best_acc:
                best_acc = acc
                best = p

        top_label = ""
        top_acc = None

        if isinstance(best, dict):
            top_label = str(best.get("label") or "")
            try:
                top_acc = float(best.get("accuracy"))
            except Exception:
                top_acc = None

        attrs: dict[str, Any] = {}

        for key in [
            "url",
            "thumbnailUrl",
            "captureDate",
            "createdAt",
            "updatedAt",
            "deviceFilename",
            "CameraId",
        ]:
            if key in latest:
                attrs[key] = latest.get(key)

        attrs["ImagePredictions"] = preds
        attrs["species_labels"] = species_labels
        attrs["species_top"] = top_label
        attrs["species_top_accuracy"] = top_acc

        return attrs
