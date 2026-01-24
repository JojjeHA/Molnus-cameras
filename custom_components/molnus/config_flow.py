from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

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


class MolnusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Minimal validation: camera id looks UUID-ish
            camera_id = (user_input.get(CONF_CAMERA_ID) or "").strip()
            if len(camera_id) < 30:
                errors["base"] = "invalid_camera_id"
            else:
                await self.async_set_unique_id(f"molnus_{camera_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Molnus {camera_id[:8]}…",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CAMERA_ID): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MolnusOptionsFlow(config_entry)


class MolnusOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_WILDLIFE_REQUIRED, default=self.config_entry.options.get(CONF_WILDLIFE_REQUIRED, DEFAULT_WILDLIFE_REQUIRED)): bool,
                vol.Optional(CONF_LIMIT, default=self.config_entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)): vol.Coerce(int),
                vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
