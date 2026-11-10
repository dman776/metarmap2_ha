# MetarMap2 for Home Assistant

A Home Assistant custom integration for [MetarMap2](https://github.com/dman776/metarmap2). It controls and monitors the Chart (the physical map) through the Chart's built-in web server (MetarMap2 Web).

Versions are named by date (`YY.MM.DD`, like MetarMap2 itself), e.g. `26.11.10`.

## Requirements

The Chart must be running a MetarMap2 version that has the read-only `GET /api/status` JSON endpoint. All other control endpoints (`/brightness`, `/visualizer`, `/config/edit`, ...) already exist in older versions. To get the endpoint, update the Chart: press **Update** on the Web Home page (or **Config > System > Software**), or run `git pull`, then restart.

## Installation

### HACS
1. In HACS, go to **Integrations → ⋮ → Custom repositories**, add `https://github.com/dman776/metarmap2_ha` with the category **Integration**.
2. Install **MetarMap2**, then restart Home Assistant.

### Manual
Copy `custom_components/metarmap` into your Home Assistant `config/custom_components/` folder, then restart.

## Setup

Go to **Settings → Devices & services → Add integration → MetarMap2** and enter:

| Field    | Default | Notes                                         |
|----------|---------|-----------------------------------------------|
| Host     |         | IP address or hostname of the Chart's Pi              |
| Port     | `80`    | `web_server.port` in `config.json`            |
| Username | `metar` | the Web login: **Config > System > Access** on the Chart, or `web_server.user` in `config.json` |
| Password | `map`   | the same login's password (`web_server.password`) |

The integration polls the Chart every 30 seconds.

## Entities

The device is named "MetarMap2" (model "MetarMap2 Chart"), so entity IDs look like `light.metarmap2_leds`. Installs made before this version keep their old `metarmap_` entity IDs (for example `light.metarmap_leds`); use those in place of the `metarmap2_` IDs below.

| Entity | Type | Chart endpoint |
|---|---|---|
| LEDs | light (brightness) | `/brightness/<0-1>`; turning it off sets brightness to 0 |
| Visualizer | select | `/visualizer/<id>` (by number on a Chart from before visualizer ids); attributes `exclusive`, plus `description` and `legend` on Chart software 2.1+ |
| Next / Previous visualizer | button | `/visualizer/next`, `/visualizer/previous` |
| Fetch METARs | button | `/fetch` |
| Restart | button | `/restart` (auth) |
| Update software | button (disabled by default) | `/update` (auth); press Restart afterwards |
| Default visualizer | select (config) | `config.json` `visualizer.active` (an id, or a number on a Chart from before visualizer ids) |
| OLED screen (the Micro) | switch | `/display/on`, `/display/off`: the screen on or off now, like the switch on the Web Home page. Not saved: it's on again when the Chart restarts. Unavailable while OLED screen enabled is off. Only on newer Chart software (with `display` in `/api/status`) |
| Lightning animation, Highlight active airport, OLED screen enabled†, Auto-rotate visualizers\*, Test pattern on startup | switch (config) | `/config/edit/...` (auth) |
| Display delay, Auto-rotate delay\*, Daytime / Dawn-dusk / Night brightness | number (config) | `/config/edit/...` (auth) |
| VFR / MVFR / IFR / LIFR airports | sensor | count of airports in each category |
| Last METAR fetch, Missing stations | sensor (diagnostic) | |
| Dawn / Sunrise / Sunset / Dusk | sensor (diagnostic, disabled by default) | the Chart's dimming schedule |
| One sensor per airport (e.g. `sensor.metarmap2_kiah`) | sensor (disabled by default) | flight category; the raw METAR, wind, visibility, temperature, `name` and so on are attributes. An airport on more than one pixel has one sensor; `pixels` lists them |

\* These settings only take effect after the Chart restarts.

† The saved setting for whether the Chart has an OLED screen (the Micro). On newer Chart software it applies right away; older software needs a restart.

Notes on brightness:
- Brightness set from the LEDs light (the Chart's LED strip) is not saved. The Chart's own schedule overrides it at dawn, sunrise, sunset and dusk.
- To change the brightness each time period uses, set the Daytime, Dawn/dusk and Night brightness numbers. The Chart loads new levels at midnight or when it restarts.

## Visualizer legend

On Chart software 2.1 or later, the Visualizer select has two more attributes for the visualizer that's running:

- `description`: one sentence on what it shows.
- `legend`: what the pixels mean, as a list of entries. Each entry has `label` (e.g. `VFR`), `detail` (e.g. `Green`), `colors` (CSS hex colors; two or more mean a gradient, except for `flash` and `alternate`), `effect` (`solid`, `blink`, `pulse`, `flash`, `alternate` (the two colors in turn), `chase` or `off`), `period` (seconds per blink or pulse, or `null`) and, on newer Chart software, `low` (a pulse's dimmest point, e.g. `0.3`, or `null`).

These attributes aren't saved in the recorder history. To show the legend on a dashboard, use a Markdown card:

```yaml
type: markdown
content: >
  **{{ states('select.metarmap2_visualizer') }}**:
  {{ state_attr('select.metarmap2_visualizer', 'description') }}

  {% for item in state_attr('select.metarmap2_visualizer', 'legend') or [] %}
  - <font color="{{ item.colors[0] if item.colors else 'gray' }}">●</font> **{{ item.label }}**: {{ item.detail }}
  {% endfor %}
```

## Service: `metarmap.locate`

Pulses one airport's pixel on the Chart. You can pick the airport by ICAO code or by pixel index:

```yaml
action: metarmap.locate
target:
  entity_id: light.metarmap2_leds
data:
  airport: KIAH
```

The Chart ignores this while an exclusive visualizer (Rainbow, Chase, Precipitation) is running.

## Development

```sh
uv venv -p 3.13 .venv
uv pip install -p .venv/bin/python pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```
