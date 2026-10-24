"""Constants for the METARMap integration."""

from datetime import timedelta

DOMAIN = "metarmap"
MANUFACTURER = "Darryl Quinn"

DEFAULT_PORT = 80
DEFAULT_USERNAME = "metar"
DEFAULT_PASSWORD = "map"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

FLIGHT_CATEGORIES = ["VFR", "MVFR", "IFR", "LIFR"]

SERVICE_LOCATE = "locate"
ATTR_AIRPORT = "airport"
ATTR_PIXEL = "pixel"
