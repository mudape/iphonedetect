"""Config flow for iPhone Device Tracker integration."""
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, AddressValueError, ip_interface
from typing import Any, List

import voluptuous as vol

from homeassistant.components import network
from homeassistant.components.device_tracker.const import (
    CONF_CONSIDER_HOME,
)
from homeassistant.components.network.const import MDNS_TARGET_IP
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_IP_ADDRESS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_CONSIDER_HOME,
    MIN_CONSIDER_HOME,
    MAX_CONSIDER_HOME,
)


async def validate_input(subnets: List[IPv4Network], devices: list, ip: str) -> dict:
    """Try to validate user input"""
    errors = {}

    if ip in devices:
        errors["base"] = "ip_already_configured"

    if not errors:
        try:
            ip_address = IPv4Address(ip)
        except AddressValueError:
            errors["base"] = "ip_invalid"
            return errors

    if not errors:
        if not any(ip_address in subnet for subnet in subnets):
            errors["base"] = "ip_range"

    return errors


async def async_get_networks(hass: HomeAssistant) -> List[IPv4Network]:
    """Search adapters for the networks."""
    networks = []
    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)

    for adapter in await network.async_get_adapters(hass):
        for ipv4 in adapter["ipv4"]:
            if ipv4["address"] == local_ip or ipv4["address"] is not None:
                network_prefix = ipv4["network_prefix"]
                networks.append(ip_interface(f"{ipv4['address']}/{network_prefix}").network)
   
    return networks


class IphoneDetectFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            devices = [
                dev.data[CONF_IP_ADDRESS] for dev in self._async_current_entries()
            ]
            subnets = await async_get_networks(self.hass)
            ip = user_input[CONF_IP_ADDRESS]

            errors = await validate_input(subnets, devices, ip)

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                    },
                    options={
                        CONF_CONSIDER_HOME: DEFAULT_CONSIDER_HOME,
                    },
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=user_input.get(CONF_HOST, "My iPhone"),
                    ): str,
                    vol.Required(
                        CONF_IP_ADDRESS, default=user_input.get(CONF_IP_ADDRESS, "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_config):
        """Import from config."""

        self._async_abort_entries_match({CONF_HOST: import_config[CONF_HOST]})

        return self.async_create_entry(
            title=import_config[CONF_HOST],
            data={
                CONF_HOST: import_config[CONF_HOST],
                CONF_IP_ADDRESS: import_config[CONF_IP_ADDRESS],
            },
            options={
                CONF_CONSIDER_HOME: import_config[CONF_CONSIDER_HOME],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return IphoneDetectOptionsFlowHandler(config_entry)


class IphoneDetectOptionsFlowHandler(OptionsFlow):
    """iPhone Detect config flow options handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONSIDER_HOME,
                        default=self.config_entry.options.get(CONF_CONSIDER_HOME),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_CONSIDER_HOME, max=MAX_CONSIDER_HOME),
                    ),
                }
            ),
        )
