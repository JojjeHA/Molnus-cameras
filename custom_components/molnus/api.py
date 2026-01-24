from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncio
import time

from aiohttp import ClientSession, ClientResponseError


@dataclass
class MolnusTokens:
    access_token: str
    refresh_token: str
    # Molnus did not give explicit expires_in in your sample; we keep a soft TTL
    obtained_at: float


class MolnusApiClient:
    def __init__(self, session: ClientSession, base_url: str, email: str, password: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password

        self._tokens: MolnusTokens | None = None
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        url = f"{self._base_url}/auth/token"
        payload = {"email": self._email, "password": self._password}
        async with self._session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
            resp.raise_for_status()
            data = await resp.json()

        token_obj = (data or {}).get("token") or {}
        access = token_obj.get("accessToken")
        refresh = token_obj.get("refreshToken")

        if not access or not refresh:
            raise ValueError("Molnus login succeeded but tokens missing in response")

        self._tokens = MolnusTokens(
            access_token=access,
            refresh_token=refresh,
            obtained_at=time.time(),
        )

    async def ensure_token(self) -> str:
        # Soft TTL: refresh every ~25 minutes (token length issue avoided; we keep in memory)
        async with self._lock:
            if self._tokens is None:
                await self._login()
                return self._tokens.access_token  # type: ignore[union-attr]

            age = time.time() - self._tokens.obtained_at
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
        url = (
            f"{self._base_url}/images/get"
            f"?CameraId={camera_id}&offset={offset}&limit={limit}&wildlifeRequired={'true' if wildlife_required else 'false'}"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        async with self._session.get(url, headers=headers) as resp:
            # If token expired unexpectedly, re-login once and retry.
            if resp.status == 401:
                async with self._lock:
                    self._tokens = None
                token = await self.ensure_token()
                headers["Authorization"] = f"Bearer {token}"
                async with self._session.get(url, headers=headers) as resp2:
                    resp2.raise_for_status()
                    data2 = await resp2.json()
                return self._extract_images(data2)

            resp.raise_for_status()
            data = await resp.json()

        return self._extract_images(data)

    def _extract_images(self, data: Any) -> list[dict[str, Any]]:
        # Based on your observed response: {"success": true, "images": [ ... ]}
        if isinstance(data, dict) and "images" in data and isinstance(data["images"], list):
            return data["images"]

        # Some APIs might return list directly
        if isinstance(data, list):
            return data

        # Otherwise, surface a readable error
        raise ValueError(f"Unexpected images response format: {type(data)} keys={list(data.keys()) if isinstance(data, dict) else ''}")

    async def fetch_bytes(self, url: str) -> bytes:
        # CDN URLs are public in your case; we still use session to fetch
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()
