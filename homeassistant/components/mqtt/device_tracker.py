"""Support for tracking MQTT enabled devices."""
import logging

import voluptuous as vol

from homeassistant.components import device_tracker, mqtt
from homeassistant.components.device_tracker import PLATFORM_SCHEMA, SOURCE_TYPES
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.mqtt import (
    ATTR_DISCOVERY_HASH,
    CONF_QOS,
    clear_discovery_hash,
    log_messages,
    subscription,
)
from homeassistant.components.mqtt.discovery import MQTT_DISCOVERY_NEW
from homeassistant.const import CONF_DEVICES, STATE_HOME, STATE_NOT_HOME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

_LOGGER = logging.getLogger(__name__)

CONF_PAYLOAD_HOME = "payload_home"
CONF_PAYLOAD_NOT_HOME = "payload_not_home"
CONF_SOURCE_TYPE = "source_type"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(mqtt.SCHEMA_BASE).extend(
    {
        vol.Required(CONF_DEVICES): {cv.string: mqtt.valid_subscribe_topic},
        vol.Optional(CONF_PAYLOAD_HOME, default=STATE_HOME): cv.string,
        vol.Optional(CONF_PAYLOAD_NOT_HOME, default=STATE_NOT_HOME): cv.string,
        vol.Optional(CONF_SOURCE_TYPE): vol.In(SOURCE_TYPES),
    }
)


async def async_setup_platform(
    hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up MQTT device tracker through configuration.yaml."""
    await _async_setup_entity(config, async_add_entities)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up MQTT device tracker dynamically through MQTT discovery."""

    async def async_discover(discovery_payload):
        """Discover and add a MQTT device tracker."""
        discovery_data = discovery_payload.discovery_data
        try:
            config = PLATFORM_SCHEMA(discovery_payload)
            await _async_setup_entity(
                config, async_add_entities, config_entry, discovery_data
            )
        except Exception:
            clear_discovery_hash(hass, discovery_data[ATTR_DISCOVERY_HASH])
            raise

    async_dispatcher_connect(
        hass, MQTT_DISCOVERY_NEW.format(device_tracker.DOMAIN, "mqtt"), async_discover
    )


async def _async_setup_entity(
    config, async_add_entities, config_entry=None, discovery_data=None
):
    """Set up the MQTT device tracker."""
    async_add_entities(
        [
            MqttScannerEntity(config, dev_id, topic)
            for dev_id, topic in config[CONF_DEVICES]
        ]
    )


class MqttScannerEntity(ScannerEntity, RestoreEntity):
    """Represent a tracked device."""

    def __init__(self, config, name, topic):
        """Set up MQTT entity."""
        self._config = config
        self._name = name
        self._topic = topic
        self._state = None
        self._sub_state = None

    async def async_added_to_hass(self):
        """Subscribe MQTT events."""
        await super().async_added_to_hass()
        await self._subscribe_topics()

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""

        @callback
        @log_messages(self.hass, self.entity_id)
        def message_received(msg):
            """Handle new MQTT messages."""
            if msg.payload == self._config[CONF_PAYLOAD_HOME]:
                self._state = True
            elif msg.payload == self._config[CONF_PAYLOAD_NOT_HOME]:
                self._state = False
            else:
                self._state = None

            self.async_write_ha_state()

        self._sub_state = await subscription.async_subscribe_topics(
            self.hass,
            self._sub_state,
            {
                "state_topic": {
                    "topic": self._topic,
                    "msg_callback": message_received,
                    "qos": self._config[CONF_QOS],
                }
            },
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe when removed."""
        self._sub_state = await subscription.async_unsubscribe_topics(
            self.hass, self._sub_state
        )

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._name

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return self._config.get(CONF_SOURCE_TYPE)

    @property
    def is_connected(self):
        """Return the state of the device."""
        return self._state
