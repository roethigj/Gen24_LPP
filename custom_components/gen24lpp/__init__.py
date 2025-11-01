"""The Gen24_LPP integration."""

from __future__ import annotations

import logging
import asyncio

from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

# from homeassistant.const import CONF_NAME, CONF_HOST, CONF_USER, CONF_PASSWORD, CONF_SIZE

from .const import (
    DOMAIN,
    CONF_SIZE,
    CONF_NAME,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
_PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up Gen24_LPP from a config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
