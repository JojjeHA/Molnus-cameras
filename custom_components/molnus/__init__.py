from __future__ import annotations

from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
