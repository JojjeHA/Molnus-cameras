from __future__ import annotations

import re
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

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _normalize_camera_id(value: str) -> str:
    """Accept raw UUID or a string containing CameraId=<uuid>."""
    raw = (value or "").strip()

    # First, if user pasted a URL or query string, extract UUID anywhere in it.
    m = _UUID_RE.search(raw)
    if m:
        return m.group(0)

    # Otherwise return trimmed raw (may still be invalid, validated later)
    return raw


class MolnusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            camera_id = _normalize_camera_id(user_input.get(CONF_CAMERA_ID, ""))

            # UUID-ish validation
            if not _UUID_RE.fullmatch(camera_id):
                errors["base"] = "invalid_camera_id"
            else:
                await self.async_set_unique_id(f"molnus_{camera_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Molnus {camera_id[:8]}…",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_CAMERA_ID: camera_id,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CAMERA_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MolnusOptionsFlow(config_entry)


class MolnusOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Sanitize values
            cleaned = dict(user_input)
            cleaned[CONF_LIMIT] = max(1, int(cleaned.get(CONF_LIMIT, DEFAULT_LIMIT)))
            cleaned[CONF_SCAN_INTERVAL] = max(10, int(cleaned.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
            return self.async_create_entry(title="", data=cleaned)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_WILDLIFE_REQUIRED,
                    default=self._config_entry.options.get(CONF_WILDLIFE_REQUIRED, DEFAULT_WILDLIFE_REQUIRED),
                ): bool,
                vol.Optional(
                    CONF_LIMIT,
                    default=self._config_entry.options.get(CONF_LIMIT, DEFAULT_LIMIT),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
