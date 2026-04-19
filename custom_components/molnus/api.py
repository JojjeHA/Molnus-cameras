from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncio
import time

from aiohttp import ClientSession


@dataclass
class MolnusTokens:
    access_token: str
    refresh_token: str
    obtained_at: float


class MolnusApiClient:
    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        email: str,
        password: str,
    ) -> None:
        self._session = session

        # Force new Molnus API host
        self._base_url = "https://client-api.molnus.com"

        self._email = email
        self._password = password

        self._tokens: MolnusTokens | None = None
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        url = f"{self._base_url}/auth/token"
        payload = {
            "email": self._email,
            "password": self._password,
        }

        async with self._session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        # Support both old and new token formats
        token_obj = (data or {}).get("token") or data or {}

        access = token_obj.get("accessToken")
        refresh = token_obj.get("refreshToken")

        if not access:
            raise ValueError(
                f"Molnus login succeeded but access token missing. Keys: {list(data.keys()) if isinstance(data, dict) else data}"
            )

        if not refresh:
            refresh = ""

        self._tokens = MolnusTokens(
            access_token=access,
            refresh_token=refresh,
            obtained_at=time.time(),
        )

    async def ensure_token(self) -> str:
        async with self._lock:
            if self._tokens is None:
                await self._login()
                return self._tokens.access_token

            age = time.time() - self._tokens.obtained_at

            # renew every 25 min
            if age > 25 * 60:
                await self._login()

            return self._tokens.access_token

    async def get_images(
        self,
        camera_id: str,
        offset: int = 0,
        limit: int = 1,
        wildlife_required: bool = False,
    ) -> list[dict[str, Any]]:
        token = await self.ensure_token()

        # Keep old endpoint first (may still work on new host)
        url = (
            f"{self._base_url}/images/get"
            f"?CameraId={camera_id}"
            f"&offset={offset}"
            f"&limit={limit}"
            f"&wildlifeRequired={'true' if wildlife_required else 'false'}"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        async with self._session.get(url, headers=headers) as resp:
            if resp.status == 401:
                async with self._lock:
                    self._tokens = None

                token = await self.ensure_token()
                headers["Authorization"] = f"Bearer {token}"

                async with self._session.get(url, headers=headers) as resp2:
                    resp2.raise_for_status()
                    data = await resp2.json()
            else:
                resp.raise_for_status()
                data = await resp.json()

        return self._extract_images(data)

    def _extract_images(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            if "images" in data and isinstance(data["images"], list):
                return data["images"]

            if "cameras" in data and isinstance(data["cameras"], list):
                return data["cameras"]

        if isinstance(data, list):
            return data

        raise ValueError(
            f"Unexpected images response format: {type(data)} keys={list(data.keys()) if isinstance(data, dict) else ''}"
        )

    async def fetch_bytes(self, url: str) -> bytes:
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()
