"""Constants for the iPhone Device Tracker integration."""

from homeassistant.const import Platform

NAME = "iPhone Device Tracker"
DOMAIN = "iphonedetect"

PLATFORMS = [
    Platform.DEVICE_TRACKER,
]

DEFAULT_SCAN_INTERVAL: int = 12

DEFAULT_CONSIDER_HOME: int = 42
MIN_CONSIDER_HOME: int = 20
MAX_CONSIDER_HOME: int = 120

CONF_NUD_STATE = {
    0: {"state": "None", "home": False},
    1: {"state": "Incomplete", "home": False},
    2: {"state": "Reachable", "home": True},
    4: {"state": "Stale", "home": True},
    8: {"state": "Delay", "home": True},
    16: {"state": "Probe", "home": False},
    32: {"state": "Failed", "home": False},
    64: {"state": "Noarp", "home": False},
    128: {"state": "Permanent", "home": True},
}
