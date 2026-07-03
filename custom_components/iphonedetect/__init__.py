"""iPhone Device Tracker"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICES, CONF_IP_ADDRESS, Platform
from homeassistant.exceptions import PlatformNotReady
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

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.DEVICE_TRACKER]
TRACKER_INTERVAL = timedelta(seconds=PROBE_INTERVAL)
DATA_COORDINATORS = "coordinators"
DATA_SCANNER = "scanner"
DATA_UNSUB_UPDATE = "unsub_update"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entries."""
    data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    devices: dict[str, DeviceData] = data.setdefault(CONF_DEVICES, {})
    coordinators: dict[str, IphoneDetectUpdateCoordinator] = data.setdefault(DATA_COORDINATORS, {})

    scanner: Scanner | None = data.get(DATA_SCANNER)
    if scanner is None:
        try:
            scanner = await async_get_scanner(hass)
        except ScannerException as error:
            raise PlatformNotReady(error) from error
        data[DATA_SCANNER] = scanner
    assert scanner is not None

    if data.get(DATA_UNSUB_UPDATE) is None:
        async def _update_devices(*_) -> None:
            """Update reachability for all tracked devices."""
            await async_update_devices(hass, scanner, devices)

        data[DATA_UNSUB_UPDATE] = async_track_time_interval(
            hass,
            _update_devices,
            TRACKER_INTERVAL,
            cancel_on_shutdown=True,
        )

    _LOGGER.debug("Adding '%s' to tracked devices", entry.options[CONF_IP_ADDRESS])

    device = devices[entry.entry_id] = DeviceData(
        ip_address=entry.options[CONF_IP_ADDRESS],
        consider_home=timedelta(seconds=entry.options[CONF_CONSIDER_HOME]),
        title=entry.title,
    )

    await async_update_devices(hass, scanner, devices)

    coordinator = IphoneDetectUpdateCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()
    coordinators[entry.entry_id] = coordinator

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
        data: dict[str, Any] = hass.data[DOMAIN]
        _LOGGER.debug("Removing '%s' from tracked devices", entry.options[CONF_IP_ADDRESS])
        data[CONF_DEVICES].pop(entry.entry_id, None)
        data.get(DATA_COORDINATORS, {}).pop(entry.entry_id, None)

        if not data[CONF_DEVICES]:
            if unsub_update := data.pop(DATA_UNSUB_UPDATE, None):
                unsub_update()
            data.pop(DATA_SCANNER, None)

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
