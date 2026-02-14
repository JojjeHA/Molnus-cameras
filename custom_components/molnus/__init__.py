from __future__ import annotations

import logging

from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .api import MolnusApiClient
from .const import (
    DOMAIN,
    PLATFORMS,
    BASE_URL,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_CAMERA_ID,
    CONF_WILDLIFE_REQUIRED,
    CONF_LIMIT,
    CONF_SCAN_INTERVAL,
    DEFAULT_WILDLIFE_REQUIRED,
    DEFAULT_LIMIT,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import MolnusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session: ClientSession = async_get_clientsession(hass)

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    camera_id = entry.data[CONF_CAMERA_ID]

    wildlife_required = entry.options.get(CONF_WILDLIFE_REQUIRED, DEFAULT_WILDLIFE_REQUIRED)
    limit = entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    client = MolnusApiClient(session=session, base_url=BASE_URL, email=email, password=password)
    coordinator = MolnusCoordinator(
        hass=hass,
        client=client,
        camera_id=camera_id,
        wildlife_required=wildlife_required,
        limit=limit,
        scan_interval_s=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entity_ids to include camera_id suffix (slugified)."""
    camera_id_raw = str(entry.data.get(CONF_CAMERA_ID, "")).strip()
    if not camera_id_raw:
        return True

    camera_id_slug = slugify(camera_id_raw)  # converts UUID with '-' into valid entity-id-safe suffix

    ent_reg = er.async_get(hass)

    # Must match unique_id in sensor.py (unique_id can contain '-'; that's fine)
    unique_id = f"molnus_{camera_id_raw}_latest_image_id"

    current_entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
    if not current_entity_id:
        return True

    desired_entity_id = f"sensor.molnus_camera_latest_image_id_{camera_id_slug}"

    if current_entity_id == desired_entity_id:
        return True

    if ent_reg.async_get(desired_entity_id):
        _LOGGER.warning(
            "Cannot migrate %s -> %s because %s already exists",
            current_entity_id,
            desired_entity_id,
            desired_entity_id,
        )
        return True

    try:
        _LOGGER.info("Migrating entity_id %s -> %s", current_entity_id, desired_entity_id)
        ent_reg.async_update_entity(current_entity_id, new_entity_id=desired_entity_id)
    except ValueError as err:
        # Never break migrations — log and continue so entry doesn't go into "Needs attention"
        _LOGGER.error(
            "Entity ID migration failed for %s -> %s: %s",
            current_entity_id,
            desired_entity_id,
            err,
        )
        return True

    return True
