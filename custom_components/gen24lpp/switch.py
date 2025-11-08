"""Number platform for gen24lpp."""

from __future__ import annotations

import json
import logging
# import random

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

        # self._mqtt_broker = entry.data[MqttBroker]
        # self._mqtt_user = entry.data[MqttUser]
        # self._mqtt_password = entry.data[MqttPassword]
        # self._mqtt_port = entry.data[MqttPort]
        # self._mqtt_client = mqtt.Client()
        # self._mqtt_client.username_pw_set(self._mqtt_user, self._mqtt_password)
        # self._client_id = f"gen24lpp_{random.randint(0, 1000)}"
        # self._topic = "gen24lpp/lpp"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    # def publish_mqtt(self, state) -> None:
    #     """Publish the limit, power limit, and state using MQTT."""
    #     payload = {
    #         "state": state,
    #     }
    #     for topic, value in payload.items():
    #         _LOGGER.debug("Publishing to MQTT topic '%s': %s", topic, value)
    #         topic_full = f"{self._topic}/{topic.replace(' ', '_').lower()}"
    #         self._mqtt_client.publish(topic_full, value, 1)

    # def subscribe_mqtt(self) -> None:
    #     """Subscribe to MQTT topics if needed."""

    #     def on_message(client, userdata, msg):
    #         match msg.topic:
    #             case str(x) if "state" in x:
    #                 if msg.payload.decode().lower() == "true":
    #                     self._is_on = True
    #                 else:
    #                     self._is_on = False

    #     self._mqtt_client.subscribe(f"{self._topic}/#")
    #     self._mqtt_client.on_message = on_message

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        lpp = self._fronius.lpp_on
        lpp["visualization"]["wattPeakReferenceValue"] = self._entry.data[CONF_SIZE]
        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="POST",
            payload=json.dumps(lpp),
            add_praefix=True,
        )
        self._is_on = True
        # self.publish_mqtt(self._is_on)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        lpp = self._fronius.lpp_off
        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="POST",
            payload=json.dumps(lpp),
            add_praefix=True,
        )
        self._is_on = False
        # self.publish_mqtt(self._is_on)
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch updates from the device."""

        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True,
        )
        if self.response:
            res = json.loads(self.response)
            self._is_on_set = res["exportLimits"]["activePower"]["softLimit"]["enabled"]
        if str(self._is_on_set).lower() == "false":
            self._is_on_set_bool = False
        else:
            self._is_on_set_bool = True
        if self._is_on_set_bool:
            if not self._is_on:
                await self.async_turn_off()
        else:
            if self._is_on:
                await self.async_turn_on()

        # self._attr_is_on = self._is_on
        # self.publish_mqtt(self._is_on)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                # self.subscribe_mqtt()
                _LOGGER.info("Connected to MQTT Broker!")
            else:
                _LOGGER.error("Failed to connect, return code %d\n", rc)

        # try:
        #     self._mqtt_client.connect(self._mqtt_broker, self._mqtt_port, 60)
        #     self._mqtt_client.on_connect = on_connect
        #     self._mqtt_client.loop_start()
        # except Exception as e:
        #     _LOGGER.error("Connection attempt failed: %s", e)

        self.response = await self._fronius.send_request(
            "config/limit_settings/powerLimits",
            method="GET",
            payload={},
            add_praefix=True,
        )
        if self.response:
            res = json.loads(self.response)
            state_string = res["exportLimits"]["activePower"]["softLimit"]["enabled"]
            if str(state_string).lower() == "true":
                state = True
            else:
                state = False
        else:
            state = False
        # self.publish_mqtt(state)
        self._is_on = state
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity which will be removed."""
        await self._fronius.close()

        # self._mqtt_client.loop_stop()
        # self._mqtt_client.disconnect()
