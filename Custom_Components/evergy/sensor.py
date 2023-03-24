import logging

from datetime import timedelta
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

CONF_USERNAME="username"
CONF_PASSWORD="password"

ICON = 'mdi:transmission-tower'

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=12)

def setup_platform(hass, config, add_entities, discovery_info=None):
    username = str(config.get(CONF_USERNAME))
    password = str(config.get(CONF_PASSWORD))

    add_entities([
	    evergy_sensor(username=username, password=password, getattribute="Status"),
      evergy_sensor(username=username, password=password, getattribute="Credit Rating"),
      evergy_sensor(username=username, password=password, getattribute="Consumption"),
      evergy_sensor(username=username, password=password, getattribute="Address"),
      evergy_sensor(username=username, password=password, getattribute="Last Payment Date"),
      evergy_sensor(username=username, password=password, getattribute="Last Payment"),
      evergy_sensor(username=username, password=password, getattribute="Amount Due"),
      evergy_sensor(username=username, password=password, getattribute="Due Date"),
      evergy_sensor(username=username, password=password, getattribute="Past Due")
	], True) 


class ks_gas_sensor(Entity):
    def __init__(self, username, password, getattribute):
        self._username = username
        self._password = password
        self._getattribute = getattribute
        self.update = Throttle(interval)(self._update)

    def _update(self):
      pass
   

    @property
    def name(self):
        name = "KS Gas " + self._getattribute
        return name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        """Return the attributes of the sensor."""
        return self._attributes

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return True
