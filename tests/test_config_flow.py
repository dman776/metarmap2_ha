"""Config flow tests."""

from __future__ import annotations

import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.metarmap.const import DOMAIN

from .conftest import BASE, ENTRY_DATA


async def _start(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return result


async def test_user_flow_success(hass: HomeAssistant, aioclient_mock, status) -> None:
    aioclient_mock.get(f"{BASE}/api/status", json=status)
    aioclient_mock.get(f"{BASE}/config", text="<html/>")
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == ENTRY_DATA
    assert result["title"] == "METARMap (192.168.1.50)"


async def test_user_flow_errors(hass: HomeAssistant, aioclient_mock, status) -> None:
    result = await _start(hass)

    aioclient_mock.get(f"{BASE}/api/status", exc=aiohttp.ClientError)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/api/status", status=404)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["errors"] == {"base": "unsupported"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/api/status", json=status)
    aioclient_mock.get(f"{BASE}/config", status=401)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_DATA)
    assert result["errors"] == {"base": "invalid_auth"}
