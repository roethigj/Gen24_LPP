"""Number platform for gen24lpp."""

from __future__ import annotations

import json
import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription
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

    sln = SoftLimitNumber(
        NumberEntityDescription(
            key="soft_limit",
            name="Soft Limit",
            entity_category=EntityCategory.CONFIG,
            native_min_value=0,
            native_max_value=100,
            native_step=1,
        ),
        entry,
    )

    entities.append(sln)

    async_add_entities(entities)


class SoftLimitNumber(NumberEntity):
    """Number entity for soft limit control."""

    def __init__(
        self,
        description: NumberEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_soft_limit"
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_native_value = 0
        self._attr_mode = "slider"
        self._size = entry.data[CONF_SIZE]
        self._limit = 0
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

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._limit = int(value * self._size / 100)

        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True
        )
        if self.response:
            lpp = json.loads(self.response)
            state = lpp["exportLimits"]["activePower"]["softLimit"]["enabled"]
        if state:
            lpp = self._fronius.lpp_on
            lpp["exportLimits"]["activePower"]["softLimit"]["powerLimit"] = self._limit
            lpp["visualization"]["wattPeakReferenceValue"] = self._entry.data[CONF_SIZE]
            self.response = await self._fronius.send_request(
                "config/limit_settings/powerLimits",
                method="POST",
                payload=json.dumps(lpp),
                add_praefix=True
            )
        else:
            self._fronius.lpp_on["exportLimits"]["activePower"]["softLimit"]["powerLimit"] = self._limit


        self._attr_native_value = int(self._limit * 100 / self._size)
        self.async_write_ha_state()

    async def async_update(self):
        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True
        )

        if self.response:
            res = json.loads(self.response)
            limit = res["exportLimits"]["activePower"]["softLimit"]["powerLimit"]
            state = res["exportLimits"]["activePower"]["softLimit"]["enabled"]
        else:
            limit = 0
        if state:
            self._attr_native_value = limit * 100 / self._size
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""

        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True
        )
        if self.response:
            res = json.loads(self.response)
            limit = res["exportLimits"]["activePower"]["softLimit"]["powerLimit"]
        else:
            limit = 0
        self._attr_native_value = limit * 100 / self._size
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity which will be removed."""
        await self._fronius.close()

