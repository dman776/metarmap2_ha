# METARMap for Home Assistant

A Home Assistant custom integration for [METARMap2](https://github.com/dman776/metarmap2). It controls and monitors the map through the map's built-in web server.

## Requirements

The map must be running a metarmap2 version that has the read-only `GET /api/status` JSON endpoint. All other control endpoints (`/brightness`, `/visualizer`, `/config/edit`, ...) already exist in older versions. To get the endpoint, update the map: press **Update** on the map's web page, or run `git pull`, then restart.

## Installation

### HACS
1. In HACS, go to **Integrations → ⋮ → Custom repositories**, add `https://github.com/dman776/metarmap2_ha` with the category **Integration**.
2. Install **METARMap**, then restart Home Assistant.

### Manual
Copy `custom_components/metarmap` into your Home Assistant `config/custom_components/` folder, then restart.

## Setup

Go to **Settings → Devices & services → Add integration → METARMap** and enter:

| Field    | Default | Notes                                         |
|----------|---------|-----------------------------------------------|
| Host     |         | IP address or hostname of the Pi              |
| Port     | `80`    | `web_server.port` in `config.json`            |
| Username | `metar` | `web_server.user` in `config.json`            |
| Password | `map`   | `web_server.password` in `config.json`        |

The integration polls the map every 30 seconds.

## Entities

| Entity | Type | Map endpoint |
|---|---|---|
| LEDs | light (brightness) | `/brightness/<0-1>`; turning it off sets brightness to 0 |
| Visualizer | select | `/visualizer/<n>`; attributes `exclusive`, plus `description` and `legend` on map 2.1+ |
| Next / Previous visualizer | button | `/visualizer/next`, `/visualizer/previous` |
| Fetch METARs | button | `/fetch` |
| Restart | button | `/restart` (auth) |
| Update software | button (disabled by default) | `/update` (auth); press Restart afterwards |
| Default visualizer | select (config) | `config.json` `visualizer.active` |
| Lightning animation, Highlight active airport, Display screen\*, Auto-rotate visualizers\*, Test pattern on startup | switch (config) | `/config/edit/...` (auth) |
| Display delay, Auto-rotate delay\*, Daytime / Dawn-dusk / Night brightness | number (config) | `/config/edit/...` (auth) |
| VFR / MVFR / IFR / LIFR airports | sensor | count of airports in each category |
| Last METAR fetch, Missing stations | sensor (diagnostic) | |
| Dawn / Sunrise / Sunset / Dusk | sensor (diagnostic, disabled by default) | the map's dimming schedule |
| One sensor per airport (e.g. `sensor.metarmap_kiah`) | sensor (disabled by default) | flight category; the raw METAR, wind, visibility, temperature and so on are attributes |

\* These settings only take effect after the map restarts.

Notes on brightness:
- Brightness set from the LEDs light is not saved. The map's own schedule overrides it at dawn, sunrise, sunset and dusk.
- To change the brightness each time period uses, set the Daytime, Dawn/dusk and Night brightness numbers. The map loads new levels at midnight or when it restarts.

## Visualizer legend

On map software 2.1 or later, the Visualizer select has two more attributes for the visualizer that's running:

- `description`: one sentence on what it shows.
- `legend`: what the LEDs mean, as a list of entries. Each entry has `label` (e.g. `VFR`), `detail` (e.g. `Green`), `colors` (CSS hex colors; two or more mean a gradient), `effect` (`solid`, `blink`, `pulse`, `flash`, `chase` or `off`) and `period` (seconds per blink or pulse, or `null`).

These attributes aren't saved in the recorder history. To show the legend on a dashboard, use a Markdown card:

```yaml
type: markdown
content: >
  **{{ states('select.metarmap_visualizer') }}**:
  {{ state_attr('select.metarmap_visualizer', 'description') }}

  {% for item in state_attr('select.metarmap_visualizer', 'legend') or [] %}
  - <font color="{{ item.colors[0] if item.colors else 'gray' }}">●</font> **{{ item.label }}**: {{ item.detail }}
  {% endfor %}
```

## Service: `metarmap.locate`

Pulses one airport's LED. You can pick the airport by ICAO code or by pixel index:

```yaml
action: metarmap.locate
target:
  entity_id: light.metarmap_leds
data:
  airport: KIAH
```

The map ignores this while an exclusive visualizer (Rainbow, Chase, Precipitation) is running.

## Development

```sh
uv venv -p 3.13 .venv
uv pip install -p .venv/bin/python pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```
