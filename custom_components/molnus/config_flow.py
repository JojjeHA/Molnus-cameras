from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
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

# Local-only config key (we use it for the entry title; we don't store it in entry.data)
CONF_CAMERA_NAME = "camera_name"


class MolnusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            camera_id = str(user_input[CONF_CAMERA_ID]).strip()
            camera_name = str(user_input[CONF_CAMERA_NAME]).strip()

            # One config entry per camera id
            await self.async_set_unique_id(camera_id)
            self._abort_if_unique_id_configured()

            data = {
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_CAMERA_ID: camera_id,
            }

            # Use friendly camera name as config entry title (shows as device name via your sensor.py)
            return self.async_create_entry(title=camera_name, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_CAMERA_NAME, default="Molnus Camera"): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CAMERA_ID): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Support YAML import if ever used (kept minimal)."""
        camera_id = str(user_input[CONF_CAMERA_ID]).strip()
        await self.async_set_unique_id(camera_id)
        self._abort_if_unique_id_configured()

        title = str(user_input.get(CONF_CAMERA_NAME) or f"Molnus Camera {camera_id}").strip()

        data = {
            CONF_EMAIL: user_input[CONF_EMAIL],
            CONF_PASSWORD: user_input[CONF_PASSWORD],
            CONF_CAMERA_ID: camera_id,
        }
        return self.async_create_entry(title=title, data=data)


class MolnusOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_WILDLIFE_REQUIRED,
                    default=self.config_entry.options.get(CONF_WILDLIFE_REQUIRED, DEFAULT_WILDLIFE_REQUIRED),
                ): bool,
                vol.Optional(
                    CONF_LIMIT,
                    default=self.config_entry.options.get(CONF_LIMIT, DEFAULT_LIMIT),
                ): int,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> MolnusOptionsFlowHandler:
    return MolnusOptionsFlowHandler(config_entry)
