"""Number platform for gen24lpp."""

from __future__ import annotations

import json
import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_USERNAME,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SIZE
from .lpp_a import FroniusGEN24

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""

    entities = []

    sls = SoftLimitSwitch(
        SwitchEntityDescription(
            key="soft_limit_enabled",
            name="Soft Limit Enabled",
            entity_category=EntityCategory.CONFIG,
        ),
        entry,
    )
    entities.append(sls)

    async_add_entities(entities)


class SoftLimitSwitch(SwitchEntity):
    """Companion on/off switch that is part of the same device as the number."""

    def __init__(
        self,
        description: SwitchEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        self._is_on = False
        self._entry = entry
        self.entity_description = description
        self._ensure_runtime_called = False
        self._attr_unique_id = f"{entry.entry_id}_soft_limit_enabled"
        self._attr_has_entity_name = True
        self._attr_name = "Soft limit enabled"
        self._attr_icon = "mdi:lightning-bolt-circle"
        self._fronius = FroniusGEN24(
            entry.data[CONF_IP_ADDRESS],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        self.response = ""
        # Device info mirrors the number entity so both appear under the same device
        self._attr_device_info = DeviceInfo(
            identifiers={(entry.domain, entry.entry_id)},
            name=entry.title or "Gen24LPP device",
            manufacturer="Gen24",
            model="Gen24LPP",
        )

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        lpp = self._fronius.lpp_on
        lpp["visualization"]["wattPeakReferenceValue"] = self._entry.data[CONF_SIZE]
        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="POST",
            payload=json.dumps(lpp),
            add_praefix=True
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        lpp = self._fronius.lpp_off
        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="POST",
            payload=json.dumps(lpp),
            add_praefix=True
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch updates from the device."""

        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True
        )
        if self.response:
            res = json.loads(self.response)
            self._is_on = res["exportLimits"]["activePower"]["softLimit"]["enabled"]

        self._attr_is_on = self._is_on
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity which will be removed."""
        await self._fronius.close()
