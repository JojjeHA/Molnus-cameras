
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponseError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MolnusApiClient
from .const import (
    DOMAIN,
    BASE_URL,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_CAMERA_ID,
    CONF_LIMIT,
    CONF_SCAN_INTERVAL,
    DEFAULT_LIMIT,
    DEFAULT_SCAN_INTERVAL,
)

CONF_CAMERA_NAME = "camera_name"


class MolnusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Molnus configuration."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MolnusOptionsFlowHandler:
        """Return the options flow."""
        return MolnusOptionsFlowHandler()

    async def _async_validate(
        self,
        email: str,
        password: str,
        camera_id: str,
    ) -> str | None:
        """Validate credentials and camera API access."""

        if not camera_id:
            return "invalid_camera_id"

        client = MolnusApiClient(
            session=async_get_clientsession(self.hass),
            base_url=BASE_URL,
            email=email,
            password=password,
        )

        try:
            await client.get_images(
                camera_id=camera_id,
                offset=0,
                limit=1,
            )

        except ClientResponseError as err:
            if err.status in (401, 403):
                return "invalid_auth"

            if err.status in (400, 404):
                return "invalid_camera_id"

            return "cannot_connect"

        except (ClientError, asyncio.TimeoutError, OSError):
            return "cannot_connect"

        except (ValueError, TypeError):
            return "cannot_connect"

        return None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle initial configuration."""

        errors: dict[str, str] = {}

        if user_input is not None:
            camera_id = str(
                user_input[CONF_CAMERA_ID]
            ).strip()

            camera_name = str(
                user_input[CONF_CAMERA_NAME]
            ).strip()

            email = str(
                user_input[CONF_EMAIL]
            ).strip()

            password = user_input[CONF_PASSWORD]

            error = await self._async_validate(
                email,
                password,
                camera_id,
            )

            if error is None:
                await self.async_set_unique_id(camera_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=camera_name or f"Molnus Camera {camera_id}",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_CAMERA_ID: camera_id,
                    },
                )

            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CAMERA_NAME,
                    default="Molnus Camera",
                ): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CAMERA_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> FlowResult:
        """Start reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm new credentials."""

        errors: dict[str, str] = {}

        entry = self._get_reauth_entry()

        if user_input is not None:
            email = str(
                user_input[CONF_EMAIL]
            ).strip()

            password = user_input[CONF_PASSWORD]

            camera_id = str(
                entry.data[CONF_CAMERA_ID]
            ).strip()

            error = await self._async_validate(
                email,
                password,
                camera_id,
            )

            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_EMAIL,
                    default=entry.data[CONF_EMAIL],
                ): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_import(
        self,
        user_input: dict[str, Any],
    ) -> FlowResult:
        """Handle YAML import."""

        return await self.async_step_user(
            {
                CONF_CAMERA_NAME: user_input.get(
                    CONF_CAMERA_NAME,
                    "Molnus Camera",
                ),
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_CAMERA_ID: user_input[CONF_CAMERA_ID],
            }
        )


class MolnusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Molnus options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage integration options."""

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        options = self.config_entry.options

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LIMIT,
                    default=options.get(
                        CONF_LIMIT,
                        DEFAULT_LIMIT,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=500),
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=10, max=86400),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
