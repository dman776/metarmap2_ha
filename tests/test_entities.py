"""Entity tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.metarmap.const import DOMAIN

from .conftest import BASE, ENTRY_DATA


@pytest.fixture
async def setup(hass: HomeAssistant, aioclient_mock, status):
    aioclient_mock.get(f"{BASE}/api/status", json=status)
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="192.168.1.50:80")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    return entry


def _called(aioclient_mock, path: str) -> bool:
    return any(str(url).endswith(path) for _, url, _, _ in aioclient_mock.mock_calls)


async def test_states(hass: HomeAssistant, setup) -> None:
    light = hass.states.get("light.metarmap_leds")
    assert light.state == "on"
    assert light.attributes["brightness"] == 128

    vis = hass.states.get("select.metarmap_visualizer")
    assert vis.state == "Flight Category"
    assert vis.attributes["options"] == ["Flight Category", "Wind", "Rainbow"]

    assert hass.states.get("switch.metarmap_lightning_animation").state == "on"
    assert hass.states.get("number.metarmap_display_delay").state == "5.0"
    assert hass.states.get("number.metarmap_daytime_brightness").state == "50.0"
    assert hass.states.get("sensor.metarmap_vfr_airports").state == "1"
    assert hass.states.get("sensor.metarmap_ifr_airports").state == "1"
    assert hass.states.get("sensor.metarmap_missing_stations").state == "1"
    assert hass.states.get("sensor.metarmap_last_metar_fetch").state != "unknown"


async def test_airport_sensor_disabled_by_default(hass: HomeAssistant, setup) -> None:
    ent = er.async_get(hass).async_get("sensor.metarmap_kiah")
    assert ent is not None
    assert ent.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_light(hass: HomeAssistant, setup, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/brightness/0.20", text="ok")
    aioclient_mock.get(f"{BASE}/brightness/0.00", text="ok")
    aioclient_mock.get(f"{BASE}/brightness/0.50", text="ok")
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.metarmap_leds", "brightness": 51}, blocking=True
    )
    assert _called(aioclient_mock, "/brightness/0.20")
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.metarmap_leds"}, blocking=True
    )
    assert _called(aioclient_mock, "/brightness/0.00")


async def test_select_and_buttons(hass: HomeAssistant, setup, aioclient_mock) -> None:
    for path in ("/visualizer/1", "/visualizer/next", "/fetch", "/config/edit/visualizer.active/2"):
        aioclient_mock.get(f"{BASE}{path}", text="ok")
    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": "select.metarmap_visualizer", "option": "Wind"}, blocking=True,
    )
    assert _called(aioclient_mock, "/visualizer/1")
    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": "select.metarmap_default_visualizer", "option": "Rainbow"}, blocking=True,
    )
    assert _called(aioclient_mock, "/config/edit/visualizer.active/2")
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.metarmap_next_visualizer"}, blocking=True
    )
    assert _called(aioclient_mock, "/visualizer/next")
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.metarmap_fetch_metars"}, blocking=True
    )
    assert _called(aioclient_mock, "/fetch")


async def test_config_entities(hass: HomeAssistant, setup, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/config/edit/lightning.animation/false", text="ok")
    aioclient_mock.get(f"{BASE}/config/edit/display_screen.delay/12.0", text="ok")
    aioclient_mock.get(f"{BASE}/config/edit/led.brightness.dimmed/0.25", text="ok")
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.metarmap_lightning_animation"}, blocking=True
    )
    assert _called(aioclient_mock, "/config/edit/lightning.animation/false")
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.metarmap_display_delay", "value": 12}, blocking=True,
    )
    assert _called(aioclient_mock, "/config/edit/display_screen.delay/12.0")
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.metarmap_dawn_dusk_brightness", "value": 25}, blocking=True,
    )
    assert _called(aioclient_mock, "/config/edit/led.brightness.dimmed/0.25")


async def test_locate(hass: HomeAssistant, setup, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/locate/1", text="ok")
    aioclient_mock.get(f"{BASE}/locate/7", text="ok")
    await hass.services.async_call(
        DOMAIN, "locate", {"entity_id": "light.metarmap_leds", "airport": "kgls"}, blocking=True
    )
    assert _called(aioclient_mock, "/locate/1")
    await hass.services.async_call(
        DOMAIN, "locate", {"entity_id": "light.metarmap_leds", "pixel": 7}, blocking=True
    )
    assert _called(aioclient_mock, "/locate/7")


async def test_unload(hass: HomeAssistant, setup) -> None:
    assert await hass.config_entries.async_unload(setup.entry_id)
    assert setup.state is ConfigEntryState.NOT_LOADED
