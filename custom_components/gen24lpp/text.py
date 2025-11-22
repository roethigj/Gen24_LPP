"""Text-Platform für Home Assistant."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ALLOWED_LIMIT,
    LIMITED_PRODUCTION,
    CONF_SIZE,
    MqttBroker,
    MqttPassword,
    MqttPort,
    MqttUser,
)

CONFIG_FIELDS = {
    "mqtt_broker": {"mode": TextMode.TEXT},
    "mqtt_user": {"mode": TextMode.TEXT},
    "mqtt_password": {"mode": TextMode.PASSWORD},
    "mqtt_topic_limit": {"mode": TextMode.TEXT},
    "mqtt_topic_active": {"mode": TextMode.TEXT},
    "inverter_ip": {"mode": TextMode.TEXT, "pattern": r"[0-9.]+"},
    "inverter_password": {"mode": TextMode.PASSWORD},
    "pv_size": {"mode": TextMode.TEXT, "pattern": r"\\d+"},
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up configurable text entities for the integration."""

    entry = config_entry

    entities = []

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_Inverter_IP",
            name="Inverter IP",
            entry=entry,
            hass=hass,
            native_value=entry.data[CONF_IP_ADDRESS],
            mode=TextMode.TEXT,
            pattern=r"[0-9.]+",
            option=CONF_IP_ADDRESS,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_Technician_Password",
            name="Technician Password",
            entry=entry,
            hass=hass,
            native_value=entry.data[CONF_PASSWORD],
            mode=TextMode.PASSWORD,
            option=CONF_PASSWORD,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_PV_Size",
            name="PV Size in W",
            entry=entry,
            hass=hass,
            native_value=str(entry.data[CONF_SIZE]),
            mode=TextMode.TEXT,
            pattern=r"\d+",
            option=CONF_SIZE,
            number=True,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_Broker_IP",
            name="Mqtt Broker IP",
            entry=entry,
            hass=hass,
            native_value=entry.data[MqttBroker],
            mode=TextMode.TEXT,
            pattern=r"[0-9.]+",
            option=MqttBroker,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_Port",
            name="Mqtt Port",
            entry=entry,
            hass=hass,
            native_value=str(entry.data[MqttPort]),
            mode=TextMode.TEXT,
            # pattern=r"\\d+",
            option=MqttPort,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_User",
            name="Mqtt User",
            entry=entry,
            hass=hass,
            native_value=entry.data[MqttUser],
            mode=TextMode.TEXT,
            option=MqttUser,
        )
    )
    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_Password",
            name="Mqtt Password",
            entry=entry,
            hass=hass,
            native_value=entry.data[MqttPassword],
            mode=TextMode.PASSWORD,
            option=MqttPassword,
        )
    )

    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_Topic_Limit",
            name="Mqtt Topic Limit",
            entry=entry,
            hass=hass,
            native_value=entry.data[ALLOWED_LIMIT],
            mode=TextMode.TEXT,
            option=ALLOWED_LIMIT,
        )
    )
    entities.append(
        ConfigTextEntity(
            unique_id=f"{entry.entry_id}_MQTT_Topic_Limit_Active",
            name="Mqtt Topic Limit active",
            entry=entry,
            hass=hass,
            native_value=entry.data[LIMITED_PRODUCTION],
            mode=TextMode.TEXT,
            option=LIMITED_PRODUCTION,
        )
    )

    async_add_entities(entities)


class ConfigTextEntity(TextEntity):
    """Representation of a configuration-backed text entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        name: str,
        entry: ConfigEntry,
        hass: HomeAssistant,
        option: str,
        native_value: str | None,
        mode: TextMode,
        pattern: str | None = None,
        number: bool | None = False,
    ) -> None:
        self._attr_unique_id = unique_id
        self._attr_native_value = native_value
        self._attr_mode = mode
        self._attr_name = name
        self._attr_entity_category = EntityCategory.CONFIG
        self.hass = hass
        self.entry = entry
        self.option = option
        self.number = number

        if pattern is not None:
            self._attr_pattern = pattern

        self._attr_device_info = DeviceInfo(
            identifiers={(entry.domain, entry.entry_id)},
            name=entry.title or "Gen24LPP device",
            manufacturer="Gen24",
            model="Gen24LPP",
        )

    async def async_set_value(self, value: str) -> None:
        """Update the value in ConfigEntry and reload integration."""
        self._attr_native_value = value
        self.async_write_ha_state()

        # Update ConfigEntry
        new_data = {**self.entry.data}
        if self.number:
            new_data[self.option] = int(self._attr_native_value)
        else:
            new_data[self.option] = self._attr_native_value
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

        # Reload integration
        await self.hass.config_entries.async_reload(self.entry.entry_id)
