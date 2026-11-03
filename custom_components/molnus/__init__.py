
from __future__ import annotations

import logging

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
    CONF_LIMIT,
    CONF_SCAN_INTERVAL,
    DEFAULT_LIMIT,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import MolnusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Molnus from a config entry."""

    session: ClientSession = async_get_clientsession(hass)

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    camera_id = entry.data[CONF_CAMERA_ID]

    limit = entry.options.get(
        CONF_LIMIT,
        DEFAULT_LIMIT,
    )
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL,
    )

    client = MolnusApiClient(
        session=session,
        base_url=BASE_URL,
        email=email,
        password=password,
    )

    coordinator = MolnusCoordinator(
        hass=hass,
        client=client,
        camera_id=camera_id,
        limit=limit,
        scan_interval_s=scan_interval,
    )

    # Do not start entities if the initial refresh fails.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    # Reload the integration when options change.
    entry.async_on_unload(
        entry.add_update_listener(async_update_options)
    )

    return True


async def async_update_options(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload Molnus when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a Molnus config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Preserve existing entity IDs without forced renaming."""

    _LOGGER.debug(
        "Molnus config entry migration check: %s",
        entry.entry_id,
    )

    if entry.version < 2:
        hass.config_entries.async_update_entry(
            entry,
            version=2,
        )

    return True
