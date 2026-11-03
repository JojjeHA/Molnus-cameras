
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

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

        # Use the current Molnus API host.
        self._base_url = "https://client-api.molnus.com"

        self._email = email
        self._password = password

        self._tokens: MolnusTokens | None = None
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        """Authenticate with Molnus and store access tokens."""
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

        token_obj = (data or {}).get("token") or data or {}

        access = token_obj.get("accessToken")
        refresh = token_obj.get("refreshToken", "")

        if not access:
            raise ValueError(
                "Molnus login succeeded but access token is missing"
            )

        self._tokens = MolnusTokens(
            access_token=access,
            refresh_token=refresh,
            obtained_at=time.time(),
        )

    async def ensure_token(self) -> str:
        """Return a valid access token, refreshing when necessary."""
        async with self._lock:
            if self._tokens is None:
                await self._login()
                return self._tokens.access_token

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
        """Fetch images for a Molnus camera."""
        token = await self.ensure_token()

        url = (
            f"{self._base_url}/images"
            f"?cameraId={camera_id}"
            f"&offset={offset}"
            f"&limit={limit}"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        async with self._session.get(url, headers=headers) as resp:
            if resp.status == 401:
                # Token may have expired. Authenticate once more.
                async with self._lock:
                    self._tokens = None

                token = await self.ensure_token()
                headers["Authorization"] = f"Bearer {token}"

                async with self._session.get(
                    url,
                    headers=headers,
                ) as retry_resp:
                    retry_resp.raise_for_status()
                    data = await retry_resp.json()
            else:
                resp.raise_for_status()
                data = await resp.json()

        return self._extract_images(data, limit)

    async def validate_camera(self, camera_id: str) -> bool:
        """Check whether Molnus accepts an images request.

        An empty image list is valid. The camera may simply
        have no images yet.

        Note: A successful request does not necessarily prove
        that the camera ID exists or belongs to the account.
        """
        camera_id = str(camera_id).strip()

        if not camera_id:
            return False

        await self.get_images(
            camera_id=camera_id,
            offset=0,
            limit=1,
        )

        return True

    def _extract_images(
        self,
        data: Any,
        limit: int = 1,
    ) -> list[dict[str, Any]]:
        """Extract images from supported Molnus response formats."""
        if isinstance(data, dict):
            if "images" in data and isinstance(data["images"], list):
                return data["images"][:limit]

            if "items" in data and isinstance(data["items"], list):
                return data["items"][:limit]

        if isinstance(data, list):
            return data[:limit]

        raise ValueError(
            "Unexpected Molnus image response format"
        )

    async def fetch_bytes(self, url: str) -> bytes:
        """Download image bytes."""
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()
