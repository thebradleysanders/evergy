"""Support for interfacing with Evergy.com unofficial pulic API."""
from code import interact
import logging

from homeassistant import core
try:
    from homeassistant.components.sensor import (
        SensorEntity as SensorEntity,
    )
except ImportError:
    from homeassistant.components.sensor import SensorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ICON,
    DOMAIN,
    FIRST_RUN,
    EVERGY_OBJECT
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Evergy platform."""
    username = config_entry.data[CONF_USERNAME]
    evergy = hass.data[DOMAIN][config_entry.entry_id][EVERGY_OBJECT]

    entities = [] 
    _LOGGER.info("Adding sensor entities for Evergy account %s", username)
    entities.append(EvergySensor(evergy, "period", config_entry.entry_id, "Period", "mdi:clipboard-text-clock-outline"))
    entities.append(EvergySensor(evergy, "billStart", config_entry.entry_id, "Bill Start", "mdi:calendar-range"))
    entities.append(EvergySensor(evergy, "billEnd", config_entry.entry_id, "Bill End", "mdi:calendar-range"))
    entities.append(EvergySensor(evergy, "billDate", config_entry.entry_id, "Bill Date", "mdi:calendar-range"))
    entities.append(EvergySensor(evergy, "date", config_entry.entry_id, "Date", "mdi:calendar-range"))
    entities.append(EvergySensor(evergy, "usage", config_entry.entry_id, "Usage", "mdi:transmission-tower"))
    entities.append(EvergySensor(evergy, "demand", config_entry.entry_id, "Demand", "mdi:transmission-tower"))
    entities.append(EvergySensor(evergy, "avgDemand", config_entry.entry_id, "Average Demand", "mdi:transmission-tower"))
    entities.append(EvergySensor(evergy, "peakDemand", config_entry.entry_id, "Peak Demand", "mdi:transmission-tower"))
    entities.append(EvergySensor(evergy, "peakDateTime", config_entry.entry_id, "Peak Date Time", "mdi:calendar-range"))
    entities.append(EvergySensor(evergy, "maxTemp", config_entry.entry_id, "Max Temp", "mdi:thermometer-high"))
    entities.append(EvergySensor(evergy, "minTemp", config_entry.entry_id, "Min Temp", "mdi:thermometer-low"))
    entities.append(EvergySensor(evergy, "avgTemp", config_entry.entry_id, "Average Temp", "mdi:thermometer-auto"))
    entities.append(EvergySensor(evergy, "cost", config_entry.entry_id, "Cost", "mdi:currency-usd"))
    entities.append(EvergySensor(evergy, "balance", config_entry.entry_id, "Balance", "mdi:currency-usd"))
    entities.append(EvergySensor(evergy, "isPartial", config_entry.entry_id, "Is Partial", "mdi:circle-half"))

    # only call update before add if it's the first run so we can try to detect zones
    first_run = hass.data[DOMAIN][config_entry.entry_id][FIRST_RUN]
    async_add_entities(entities, first_run)

    platform = entity_platform.async_get_current_platform()

    @service.verify_domain_control(hass, DOMAIN)
    async def async_service_handle(service_call: core.ServiceCall) -> None:
        """Handle for services."""
        entities = await platform.async_extract_from_service(service_call)

        if not entities:
            return



class EvergySensor(SensorEntity):
    def __init__(self, evergy, sensor_type: str, namespace, nicename: str, icon: str) -> None:
        """Initialize new sensors."""
        self._evergy = evergy
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{namespace}_{self._sensor_type}"
	self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_name = f"{nicename}"
        self._attr_native_value = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN)},
            manufacturer="Evergy",
            model="Evergy.com Utility Account",
            name=f"Evergy"
        )
        self._update_success = True

    def update(self):
        """Retrieve latest value."""
#        try:
        state = self._evergy
#        except SerialException:
#            self._update_success = False
#            _LOGGER.warning("Could not update sensor")
#            return

        if not state:
            self._update_success = False
            return

        self._attr_native_value = str(state[-1][self._sensor_type])


    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._update_success
