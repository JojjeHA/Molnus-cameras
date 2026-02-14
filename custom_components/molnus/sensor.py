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
    camera_id = str(entry.data[CONF_CAMERA_ID])
    async_add_entities([MolnusLatestImageIdSensor(coordinator, camera_id)], True)


class MolnusLatestImageIdSensor(CoordinatorEntity[MolnusCoordinator], SensorEntity):
    """
    Latest image id for a specific Molnus camera.

    NOTE:
    - unique_id includes camera_id to keep entities stable and distinct.
    - name includes camera_id so Home Assistant auto-generates entity_id
      with a suffix: sensor.molnus_camera_latest_image_id_<camera_id>
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:camera-wireless"

    def __init__(self, coordinator: MolnusCoordinator, camera_id: str) -> None:
        super().__init__(coordinator)
        self._camera_id = str(camera_id)

        # Stable + unique per camera (keeps registry uniqueness)
        self._attr_unique_id = f"molnus_{self._camera_id}_latest_image_id"

        # CRITICAL: include camera_id in the entity's name so HA generates
        # an entity_id with suffix "_<camera_id>"
        #
        # With _attr_has_entity_name=True, the final shown name becomes:
        # "Molnus Camera Latest image ID <camera_id>"
        #
        # And the generated entity_id typically becomes:
        # sensor.molnus_camera_latest_image_id_<camera_id>
        self._attr_name = f"Latest image ID {self._camera_id}"

    @property
    def device_info(self) -> DeviceInfo:
        # OPTIONAL: you may want the device name to include the camera id too,
        # so devices don't all show as "Molnus Camera" in the UI.
        return DeviceInfo(
            identifiers={(DOMAIN, self._camera_id)},
            name=f"Molnus Camera {self._camera_id}",
            manufacturer="Molnus",
            model="Wildlife camera",
        )

    @property
    def native_value(self) -> Any:
        latest = self.coordinator.data.get("latest") or {}
        return latest.get("id")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self.coordinator.data.get("latest") or {}

        # Raw predictions list from API (may be missing)
        preds = latest.get("ImagePredictions") or []
        if not isinstance(preds, list):
            preds = []

        # Unique labels
        labels = []
        for p in preds:
            if isinstance(p, dict) and "label" in p and p["label"] is not None:
                labels.append(str(p["label"]))
        species_labels = sorted(set(labels))

        # Top prediction by accuracy
        top_label = ""
        top_acc = None
        best = None
        best_acc = -1.0
        for p in preds:
            if not isinstance(p, dict):
                continue
            acc = p.get("accuracy")
            try:
                acc_f = float(acc)
            except Exception:
                acc_f = -1.0
            if acc_f > best_acc:
                best_acc = acc_f
                best = p

        if isinstance(best, dict):
            top_label = str(best.get("label") or "")
            try:
                top_acc = float(best.get("accuracy"))
            except Exception:
                top_acc = None

        # Keep existing useful attrs too
        attrs: dict[str, Any] = {}
        for k in [
            "url",
            "thumbnailUrl",
            "captureDate",
            "createdAt",
            "deviceFilename",
            "CameraId",
        ]:
            if k in latest:
                attrs[k] = latest.get(k)

        # New attrs for automation use
        attrs["ImagePredictions"] = preds
        attrs["species_labels"] = species_labels
        attrs["species_top"] = top_label
        attrs["species_top_accuracy"] = top_acc

        return attrs
