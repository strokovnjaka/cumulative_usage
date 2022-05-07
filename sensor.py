"""Support for cumulative usage sensor."""
import logging
import os
import sys
import json
import voluptuous as vol
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_FILE_PATH,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_ON,
    STATE_OFF,
)

_LOGGER = logging.getLogger(__name__)

# Base component constants
NAME = "Cumulative Usage Sensor"
DOMAIN = "cumulative_usage"
VERSION = "0.0.1"
ISSUE_URL = "https://github.com/strokovnjaka/ha-cumulative_usage/issues"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have ANY issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

CONF_FILEPATH = 'filepath'

SERVICE_RESET_TIMER = "reset_timer"

DEFAULT_NAME = 'Cumulative usage'
DEFAULT_UNIT_OF_MEASUREMENT = 'h'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_FILE_PATH, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    _LOGGER.info(STARTUP_MESSAGE)
    unique_id = config.get(CONF_UNIQUE_ID)
    entity_id = config.get(CONF_ENTITY_ID)
    name = config.get(CONF_NAME)
    filepath = config.get(CONF_FILE_PATH)
    unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
    async_add_entities([CumulativeUsageSensor(hass, unique_id, entity_id, name, filepath, unit_of_measurement)])
    _LOGGER.debug("Registering service.")
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(SERVICE_RESET_TIMER, {}, "reset_timer")
    _LOGGER.debug("Setup done.")


class CumulativeUsageSensor(SensorEntity):
    """Cumulative usage sensor entity."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, unique_id, entity_id, name, filepath, unit_of_measurement):
        """Initialize the sensor."""
        _LOGGER.debug("Creating CumulativeUsageSensor(%s, %s, %s, %s, %s)",
                      unique_id, entity_id, name, filepath, unit_of_measurement
                      )
        self._unique_id = unique_id if unique_id else f"{entity_id}_cumulative_usage"
        self._entity_id = entity_id
        self._name = name
        self._attr_native_unit_of_measurement = unit_of_measurement  # one of 'h', 'm', 's', default is 'h'
        self._filepath = filepath if filepath else f'/config/custom_components/cumulative_usage/data/d_{unique_id}.json'
        self._state = None
        self._load_persisted()

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        if not self._state:
            return None
        u = self.native_unit_of_measurement.lower()
        c = self._state['usage_in_sec']
        if u == 'h':
            return c/3600.0
        elif u == 'm':
            return c/60.0
        return c

    @property
    def extra_state_attributes(self):
        _LOGGER.debug("Extra state attributes: %s", self._state)
        ret = dict(self._state)
        ret.pop('usage_in_sec')
        return ret

    async def async_added_to_hass(self):
        """Register callbacks."""
        _LOGGER.debug("Registering callbacks")
        self.async_on_remove(self.hass.helpers.event.async_track_state_change(
            self._entity_id, self._handle_state_change, STATE_ON, STATE_OFF))

    def reset_timer(self):
        _LOGGER.debug("Resetting timer...")
        self._state = {
            'last_reset_at': datetime.now(),
            'last_update_at': datetime.now(),
            'usage_in_sec': 0
        }
        self._save_persisted()
        self.async_write_ha_state()
        _LOGGER.debug("Timer reset!")

    def _handle_state_change(self, entity, old_state, new_state):
        """Handle sensor value update."""
        _LOGGER.debug("State change of '%s' from '%s' to '%s'", entity, old_state.last_changed, new_state.last_changed)
        if old_state is None or new_state is None:
            return
        diff = new_state.last_changed - old_state.last_changed
        if (not self._state) or (not 'usage_in_sec' in self._state):
            self._default_state()
        self._state['usage_in_sec'] += diff.total_seconds()
        self._state['last_update_at'] = datetime.now()
        self._save_persisted()
        self.async_write_ha_state()

    def _default_state(self):
        self._state = {
            'last_reset_at': datetime.now(),
            'last_update_at': datetime.now(),
            'usage_in_sec': 0
        }

    def _load_persisted(self):
        _LOGGER.debug("Loading persisted from '%s' (exists: %s)", self._filepath, os.path.exists(self._filepath))
        if not os.path.exists(self._filepath):
            return
        with open(self._filepath) as f:
            try:
                self._state = json.load(f)
                self._state['last_reset_at'] = datetime.fromisoformat(self._state['last_reset_at'])
                self._state['last_update_at'] = datetime.fromisoformat(self._state['last_update_at'])
                _LOGGER.debug("Loaded persisted: %s", self._state)
            except Exception as e:
                _LOGGER.error("Exception loading persisted data for CumulativeUsageSensor(%s) from '%s': error %s",
                              self._name,
                              self._filepath,
                              e
                              )
                self._state = None

    def _save_persisted(self):
        def isoconverter(o):
            if isinstance(o, datetime):
                return o.isoformat()
        _LOGGER.debug("Saving persisted to '%s' (exists: %s)", self._filepath, os.path.exists(self._filepath))
        try:
            _LOGGER.debug("Saving state: %s", self._state)
            with open(self._filepath, mode="w") as f:
                json.dump(self._state, f, default=isoconverter)
        except Exception as e:
            _LOGGER.error("Exception saving persisted data for CumulativeUsageSensor(%s) to '%s': error %s",
                          self._name,
                          self._filepath,
                          e
                          )
