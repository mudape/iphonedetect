"""iPhone Device Tracker"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICES, CONF_IP_ADDRESS, Platform
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, PROBE_INTERVAL
from .coordinator import IphoneDetectUpdateCoordinator
from .scanner import (
    DeviceData,
    Scanner,
    ScannerException,
    async_get_scanner,
    async_update_devices,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.DEVICE_TRACKER]
TRACKER_INTERVAL = timedelta(seconds=PROBE_INTERVAL)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    devices: dict[str, DeviceData]
    devices = hass.data.setdefault(DOMAIN, {})[CONF_DEVICES] = {}

    try:
        scanner: Scanner = await async_get_scanner(hass)
    except ScannerException as error:
        raise PlatformNotReady(error)

    async def _update_devices(*_) -> None:
        """Update reachability for all tracked devices."""
        await async_update_devices(hass, scanner, devices)

    async_track_time_interval(hass, _update_devices, TRACKER_INTERVAL, cancel_on_shutdown=True)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entries."""
    _LOGGER.debug("Adding '%s' to tracked devices", entry.options[CONF_IP_ADDRESS])

    device = hass.data[DOMAIN][CONF_DEVICES][entry.entry_id] = DeviceData(
        ip_address=entry.options[CONF_IP_ADDRESS],
        consider_home=timedelta(seconds=entry.options[CONF_CONSIDER_HOME]),
        title=entry.title,
    )

    coordinator = IphoneDetectUpdateCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN].setdefault("coordinators", {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.debug("Reloading entity '%s' with '%s'", entry.title, entry.options)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        _LOGGER.debug("Removing '%s' from tracked devices", entry.options[CONF_IP_ADDRESS])
        hass.data[DOMAIN][CONF_DEVICES].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to a new format."""

    if config_entry.version == 1:
        _LOGGER.debug("Migrating from version 1")
        # Move IP address from data to options
        new_options = config_entry.options.copy()
        if config_entry.data.get(CONF_IP_ADDRESS):
            new_options[CONF_IP_ADDRESS] = config_entry.data[CONF_IP_ADDRESS]

        # Set unique_id
        new_unique_id = config_entry.unique_id
        if not new_unique_id:
            new_unique_id = f"{DOMAIN}_{config_entry.title}".lower()

        hass.config_entries.async_update_entry(
            config_entry,
            unique_id=new_unique_id,
            data={},
            options=new_options,
            version=2,
        )

    return True
