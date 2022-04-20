"""iPhone Device Tracker"""
from __future__ import annotations
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.device_tracker.const import (
    DOMAIN as DEVICE_TRACKER,
    CONF_CONSIDER_HOME,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_HOSTS,
    CONF_IP_ADDRESS,
    CONF_PLATFORM,
    CONF_SOURCE,
)

from .const import (
    DEFAULT_CONSIDER_HOME,
    DOMAIN,
    MAX_CONSIDER_HOME,
    MIN_CONSIDER_HOME,
    PLATFORMS,
)
from .scanner import IphoneDetectScanner


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration from configuration.yaml (DEPRECATED)."""

    if DEVICE_TRACKER in config:

        for entry in config[DEVICE_TRACKER]:

            if entry[CONF_PLATFORM] == DOMAIN:
                if CONF_CONSIDER_HOME in entry:
                    con_home = entry[CONF_CONSIDER_HOME]
                    if isinstance(con_home, timedelta):
                        con_home = con_home.seconds
                        
                    if MIN_CONSIDER_HOME <= con_home >= MAX_CONSIDER_HOME:
                        con_home = (
                            MAX_CONSIDER_HOME
                            if con_home > MAX_CONSIDER_HOME
                            else MIN_CONSIDER_HOME
                        )
                else:
                    con_home = DEFAULT_CONSIDER_HOME

                for host, ip in entry[CONF_HOSTS].items():
                    hass.async_create_task(
                        hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={CONF_SOURCE: SOURCE_IMPORT},
                            data={
                                CONF_HOST: host,
                                CONF_IP_ADDRESS: ip,
                                CONF_CONSIDER_HOME: con_home,
                            },
                        )
                    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration."""
    hass.data.setdefault(DOMAIN, {})

    if CONNECTION_NETWORK_MAC not in entry.data:
        _mac = await IphoneDetectScanner.get_mac_address(entry.data[CONF_IP_ADDRESS])
        if _mac is None:
            raise ConfigEntryNotReady("No MAC address found yet")
        else:
            data = dict(entry.data)
            data[CONNECTION_NETWORK_MAC] = _mac
            hass.config_entries.async_update_entry(entry, data=data)

    hass.data[DOMAIN][entry.entry_id] = entry.entry_id

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
