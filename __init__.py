'''Component for cumulative usage of an entity.'''
# import logging
# import time
# from datetime import datetime

# import voluptuous as vol

# DOMAIN = 'cumulative_usage'

# from homeassistant.const import (
#     STATE_ON,
#     STATE_OFF,
#     CONF_SENSORS,
#     CONF_UNIT_OF_MEASUREMENT,
# )
# import homeassistant.helpers.config_validation as cv
# from homeassistant.helpers.discovery import async_load_platform

# _LOGGER = logging.getLogger(__name__)

# CONF_MONITORING_ENTITY_ID = 'monitoring_entity_id'
# CONF_FILEPATH = 'filepath'

# SERVICE_RESET_TIMER = "reset_timer"

# DEFAULT_UNIT_OF_MEASUREMENT = 'h'

# # SCHEMA_SENSORS = vol.Schema(
# #     {
# #         vol.Required(CONF_MONITORING_ENTITY_ID): cv.string,
# #         vol.Optional(CONF_FILEPATH, default=None): vol.Any(None, cv.string),
# #         vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
# #     }
# # )

# # CONFIG_SCHEMA = vol.Schema(
# #     {
# #         DOMAIN: vol.Schema(
# #             {
# #                 vol.Required(CONF_SENSORS): { cv.string: SCHEMA_SENSORS },
# #             }
# #         )
# #     },
# #     extra=vol.ALLOW_EXTRA,
# # )

# async def async_setup(hass, config):
#     '''Set up cumulative usage component.'''
#     _LOGGER.info('Initializing component...')
#     await async_load_platform(hass, "sensor", DOMAIN, {}, config)
#     _LOGGER.info('Component initialized.')
#     return True
