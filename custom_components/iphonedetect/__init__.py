"""iPhone Device Tracker"""

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_PROBE_ARP, CONF_PROBE_IP_NEIGH, CONF_PROBE_IPROUTE, DOMAIN
from .coordinator import IphoneDetectUpdateCoordinator
from .scanner import _select_probe, ProbeNud, ProbeSubprocess

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.DEVICE_TRACKER]

@dataclass(slots=True)
class IphoneDetectDomainData:
    """DomainData Dataclass."""

    probe: str | None
    coordinators: dict[str, IphoneDetectUpdateCoordinator]

    
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    hass.data[DOMAIN] = IphoneDetectDomainData(
        probe = await _select_probe(),
        coordinators = {}
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entries."""
    data: IphoneDetectDomainData = hass.data[DOMAIN]
    ip: str = entry.options[CONF_IP_ADDRESS]

    if data.probe is None:
        raise ConfigEntryNotReady("Can't find a tool to use for probing devices.")
    elif data.probe == CONF_PROBE_IPROUTE:
        probe_cls = ProbeNud(hass, ip, None)
    elif data.probe == CONF_PROBE_IP_NEIGH:
        probe_cls = ProbeSubprocess(hass, ip, CONF_PROBE_IP_NEIGH)
    else:
        probe_cls = ProbeSubprocess(hass, ip, CONF_PROBE_ARP)

    coordinator = IphoneDetectUpdateCoordinator(hass, probe_cls)
    await coordinator.async_config_entry_first_refresh()

    data.coordinators[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].coordinators.pop(entry.entry_id)

    return unload_ok


async def async_reload_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to a new format."""

    if config_entry.version == 1:
        _LOGGER.debug("Migrating from version 1")
        # Move IP address from data to option so its easier to change in UI
        new_options = config_entry.options.copy()
        if config_entry.data.get(CONF_IP_ADDRESS):
            new_options[CONF_IP_ADDRESS] = config_entry.data[CONF_IP_ADDRESS]

        # Set unique_id
        new_unique_id = config_entry.unique_id
        if not new_unique_id:
            new_unique_id = f"{DOMAIN}_{config_entry.title}".lower()

        hass.config_entries.async_update_entry(config_entry, unique_id=new_unique_id, data={}, options=new_options, version=2)

    return True
