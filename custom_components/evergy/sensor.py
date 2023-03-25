"""Support for interfacing with Evergy.com unofficial pulic API."""
from code import interact
from datetime import timedelta
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
SCAN_INTERVAL = timedelta(seconds=60)
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
    entities.append(EvergySensor(evergy, "period", config_entry.entry_id, "Period", "mdi:clipboard-text-clock-outline", None))
    entities.append(EvergySensor(evergy, "billDate", config_entry.entry_id, "Total Bill Date", "mdi:calendar-range", None))
    entities.append(EvergySensor(evergy, "usage", config_entry.entry_id, "Usage Today", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(evergy, "demand", config_entry.entry_id, "Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(evergy, "avgDemand", config_entry.entry_id, "Average Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(evergy, "peakDemand", config_entry.entry_id, "Peak Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(evergy, "peakDateTime", config_entry.entry_id, "Peak Time", "mdi:calendar-range", None))
    entities.append(EvergySensor(evergy, "maxTemp", config_entry.entry_id, "Max Temp", "mdi:thermometer-high", "°F"))
    entities.append(EvergySensor(evergy, "minTemp", config_entry.entry_id, "Min Temp", "mdi:thermometer-low", "°F"))
    entities.append(EvergySensor(evergy, "avgTemp", config_entry.entry_id, "Average Temp", "mdi:thermometer-auto", "°F"))
    entities.append(EvergySensor(evergy, "cost", config_entry.entry_id, "Cost Today", "mdi:currency-usd", None))
    entities.append(EvergySensor(evergy, "balance", config_entry.entry_id, "Balance", "mdi:currency-usd", None))
    
    entities.append(EvergySensor(evergy, "address", config_entry.entry_id, "Address", "mdi:home", None))
    entities.append(EvergySensor(evergy, "billAmount", config_entry.entry_id, "Bill Amount", "mdi:currency-usd", None))
    entities.append(EvergySensor(evergy, "isPastDue", config_entry.entry_id, "Is Past Due", "mdi:calendar-range", None))
    entities.append(EvergySensor(evergy, "test", config_entry.entry_id, "DevTest", "mdi:calendar-range", None))

    async_add_entities(entities, True)

    platform = entity_platform.async_get_current_platform()

    @service.verify_domain_control(hass, DOMAIN)
    async def async_service_handle(service_call: core.ServiceCall) -> None:
        """Handle for services."""
        entities = await platform.async_extract_from_service(service_call)

        if not entities:
            return



class EvergySensor(SensorEntity):
    def __init__(self, evergy, sensor_type: str, namespace, nicename: str, icon: str, uom: str) -> None:
        """Initialize new sensors."""
        self._evergy = evergy
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{namespace}_{self._sensor_type}"
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_name = f"{nicename}"
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = uom
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(evergy['dashboard']['addresses'][0]['street']))},
            manufacturer="Evergy",
            model="Evergy.com Utility Account",
            name=str(evergy['dashboard']['addresses'][0]['street'])
        )
        self._update_success = True
   

    def update(self):
        """Retrieve latest value."""

        state = self._evergy
        if not state:
            self._update_success = False
            return
        
        if self._sensor_type == "address":
            self._attr_native_value = str(state['dashboard']['addresses'][0]['street'])
        elif(self._sensor_type == "billAmount" or self._sensor_type == "isPastDue"):
            self._attr_native_value = str(state['dashboard'][self._sensor_type])
        else:
            self._attr_native_value = str(state['usage'][-1][self._sensor_type])


    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._update_success
