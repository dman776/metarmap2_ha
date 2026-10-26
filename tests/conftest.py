"""Fixtures for METARMap tests."""

from __future__ import annotations

import copy

import pytest

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

pytest_plugins = "pytest_homeassistant_custom_component"

BASE = "http://192.168.1.50:80"

ENTRY_DATA = {
    CONF_HOST: "192.168.1.50",
    CONF_PORT: 80,
    CONF_USERNAME: "metar",
    CONF_PASSWORD: "map",
}

STATUS = {
    "version": "1.16.2",
    "ip": "192.168.1.50",
    "brightness": 0.5,
    "visualizer": {"active": 0, "name": "Flight Category", "exclusive": False},
    "visualizers": [
        {"index": 0, "name": "Flight Category", "exclusive": False},
        {"index": 1, "name": "Wind", "exclusive": False},
        {"index": 2, "name": "Rainbow", "exclusive": True},
    ],
    "config": {
        "visualizer.active": 0,
        "visualizer.auto_rotate.enabled": False,
        "visualizer.auto_rotate.delay_seconds": 60,
        "lightning.animation": True,
        "display_screen.enabled": True,
        "display_screen.locate_active": True,
        "display_screen.delay": 5.0,
        "led.inittest": True,
        "led.brightness.normal": 0.5,
        "led.brightness.dimmed": 0.1,
        "led.brightness.off": 0.01,
    },
    "display": {"enabled": True, "on": True},
    "suntimes": {
        "dawn": "2026-10-23T07:00:00-05:00",
        "sunrise": "2026-10-23T07:25:00-05:00",
        "sunset": "2026-10-23T18:45:00-05:00",
        "dusk": "2026-10-23T19:10:00-05:00",
    },
    "lastFetchTime": "2026-10-23T12:00:00.123456",
    "missingStations": ["KXYZ"],
    "airports": [
        {"code": "KIAH", "pixel": 0, "text": "IAH", "display": True, "flightCategory": "VFR",
         "raw": "KIAH 231753Z 18010KT 10SM CLR 28/18 A3001", "windDir": "180", "windSpeed": 10,
         "windGustSpeed": 0, "vis": 10, "obs": "", "tempC": 28, "dewpointC": 18, "altimHg": 30.01,
         "lightning": False, "obsTime": "2026-10-23T17:53:00+00:00"},
        {"code": "KGLS", "pixel": 1, "text": "Galveston", "display": True, "flightCategory": "IFR",
         "raw": "KGLS ...", "windDir": "VRB", "windSpeed": 3, "windGustSpeed": 0, "vis": 2,
         "obs": "BR", "tempC": 24, "dewpointC": 23, "altimHg": 30.0, "lightning": False,
         "obsTime": "2026-10-23T17:53:00+00:00"},
        {"code": "KXYZ", "pixel": 3, "text": 3, "display": False, "flightCategory": None,
         "raw": None, "windDir": None, "windSpeed": None, "windGustSpeed": None, "vis": None,
         "obs": None, "tempC": None, "dewpointC": None, "altimHg": None, "lightning": None,
         "obsTime": None},
    ],
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def status():
    return copy.deepcopy(STATUS)
