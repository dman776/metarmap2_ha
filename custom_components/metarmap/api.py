"""Async client for the MetarMap2 web server REST API."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import aiohttp

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)
# /fetch waits up to 20s for a fetch that is already running (then answers 503),
# and a fetch itself can be slow on a slow Pi
FETCH_TIMEOUT = aiohttp.ClientTimeout(total=100)


class MetarMapError(Exception):
    """Generic error talking to the map."""


class MetarMapConnectionError(MetarMapError):
    """The map could not be reached."""


class MetarMapAuthError(MetarMapError):
    """The map rejected the configured credentials."""


class MetarMapUnsupportedError(MetarMapError):
    """The map's software does not provide /api/status (needs updating)."""


class MetarMapBusyError(MetarMapError):
    """The map answered 503 to /fetch: a fetch is already running."""


class MetarMapClient:
    """Thin wrapper around the MetarMap2 bottle web server."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._auth = aiohttp.BasicAuth(username, password)

    async def _get(
        self,
        path: str,
        *,
        auth: bool = False,
        timeout: aiohttp.ClientTimeout = REQUEST_TIMEOUT,
    ) -> aiohttp.ClientResponse:
        try:
            resp = await self._session.get(
                self._base + path,
                auth=self._auth if auth else None,
                timeout=timeout,
                # config edits answer with a redirect to an HTML page we don't need
                allow_redirects=False,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise MetarMapConnectionError(f"Error requesting {path}: {err}") from err
        if resp.status == 401:
            raise MetarMapAuthError("Invalid username or password")
        if resp.status == 404 and path == "/api/status":
            raise MetarMapUnsupportedError("Map software does not expose /api/status")
        if resp.status == 503 and path == "/fetch":
            raise MetarMapBusyError("A fetch is already running")
        if resp.status >= 400:
            raise MetarMapError(f"{path} returned HTTP {resp.status}")
        return resp

    async def get_status(self) -> dict[str, Any]:
        """Return the JSON status snapshot."""
        resp = await self._get("/api/status")
        try:
            return await resp.json(content_type=None)
        except (aiohttp.ContentTypeError, ValueError) as err:
            raise MetarMapUnsupportedError("Invalid /api/status response") from err

    async def validate_auth(self) -> None:
        """Hit an authenticated read-only page to verify credentials."""
        await self._get("/config", auth=True)

    async def set_brightness(self, level: float) -> None:
        """Set the Chart's brightness, 0.0 - 1.0 (not persisted; the sun schedule overrides it)."""
        await self._get(f"/brightness/{max(0.0, min(1.0, level)):.2f}")

    async def set_display(self, on: bool) -> None:
        """Turn the OLED screen on or off now (newer maps, with /display). Not saved: the screen is on again
        after a restart. The map answers 409 if the screen is turned off in its config (display_screen.enabled)."""
        await self._get(f"/display/{'on' if on else 'off'}")

    async def set_visualizer(self, key: str | int) -> None:
        """By id ("wind_direction", maps with visualizer ids) or by number (3, any map)."""
        await self._get(f"/visualizer/{quote(str(key), safe='')}")

    async def next_visualizer(self) -> None:
        await self._get("/visualizer/next")

    async def previous_visualizer(self) -> None:
        await self._get("/visualizer/previous")

    async def locate(self, pixel: int) -> None:
        """Pulse a single airport pixel (ignored by exclusive visualizers)."""
        await self._get(f"/locate/{int(pixel)}")

    async def fetch_metars(self) -> None:
        await self._get("/fetch", timeout=FETCH_TIMEOUT)

    async def edit_config(self, key: str, value: Any) -> None:
        """Persist a config.json value, e.g. ("lightning.animation", True)."""
        if isinstance(value, bool):
            value = "true" if value else "false"
        await self._get(f"/config/edit/{key}/{quote(str(value), safe='')}", auth=True)

    async def update_software(self) -> str:
        """git pull on the device; returns the HTML log. A restart is needed afterwards."""
        resp = await self._get("/update", auth=True, timeout=aiohttp.ClientTimeout(total=120))
        return await resp.text()

    async def restart(self) -> None:
        """Restart the controller process. The device execs itself, so the
        connection usually drops before a response is sent."""
        try:
            await self._get("/restart", auth=True, timeout=aiohttp.ClientTimeout(total=5))
        except MetarMapConnectionError:
            pass
