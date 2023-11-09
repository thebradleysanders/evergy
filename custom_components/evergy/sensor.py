"""Support for interfacing with Evergy.com unofficial pulic API."""
from code import interact
from datetime import timedelta
import logging
import async_timeout

from homeassistant import core
try:
    from homeassistant.components.sensor import (
        SensorEntity as SensorEntity,
        SensorStateClass,
        SensorDeviceClass
    )
except ImportError:
    from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    ICON,
    DOMAIN,
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
    
    async def async_update_data():
        evergy_api = hass.data[DOMAIN][config_entry.entry_id][EVERGY_OBJECT]
        await hass.async_add_executor_job(evergy_api.get_usage)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5400), #90 min.
    )

    # Immediate refresh
    await coordinator.async_request_refresh()

    _LOGGER.info("Adding sensor entities for Evergy account %s", config_entry.data[CONF_USERNAME])
    entities = [] 
    entities.append(EvergySensor(coordinator, hass, "period", config_entry.entry_id, "Period", "mdi:clipboard-text-clock-outline", None))
    entities.append(EvergySensor(coordinator, hass, "billDate", config_entry.entry_id, "Total Bill Date", "mdi:calendar-range", None))
    entities.append(EvergySensor(coordinator, hass, "usage", config_entry.entry_id, "Usage Today", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(coordinator, hass, "demand", config_entry.entry_id, "Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(coordinator, hass, "avgDemand", config_entry.entry_id, "Average Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(coordinator, hass, "peakDemand", config_entry.entry_id, "Peak Demand", "mdi:transmission-tower", "kWh"))
    entities.append(EvergySensor(coordinator, hass, "peakDateTime", config_entry.entry_id, "Peak Time", "mdi:calendar-range", None))
    entities.append(EvergySensor(coordinator, hass, "maxTemp", config_entry.entry_id, "Max Temp", "mdi:thermometer-high", "°F"))
    entities.append(EvergySensor(coordinator, hass, "minTemp", config_entry.entry_id, "Min Temp", "mdi:thermometer-low", "°F"))
    entities.append(EvergySensor(coordinator, hass, "avgTemp", config_entry.entry_id, "Average Temp", "mdi:thermometer-auto", "°F"))
    entities.append(EvergySensor(coordinator, hass, "balance", config_entry.entry_id, "Balance", "mdi:currency-usd", None))
    entities.append(EvergySensor(coordinator, hass, "address", config_entry.entry_id, "Address", "mdi:home", None))
    entities.append(EvergySensor(coordinator, hass, "billAmount", config_entry.entry_id, "Bill Amount", "mdi:currency-usd", None))
    entities.append(EvergySensor(coordinator, hass, "isPastDue", config_entry.entry_id, "Is Past Due", "mdi:calendar-range", None))
    async_add_entities(entities, True)

    platform = entity_platform.async_get_current_platform()

    @service.verify_domain_control(hass, DOMAIN)
    async def async_service_handle(service_call: core.ServiceCall) -> None:
        """Handle for services."""
        entities = await platform.async_extract_from_service(service_call)

        if not entities:
            return


class EvergySensor(SensorEntity):
    def __init__(self, coordinator, hass, sensor_type: str, namespace, nicename: str, icon: str, uom: str) -> None:
        self._coordinator = coordinator
        self._evergy_api = hass.data[DOMAIN][namespace][EVERGY_OBJECT]
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{namespace}_{self._sensor_type}"
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_name = f"{nicename}"
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = uom
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._evergy_api.dashboard_data['addresses'][0]['street']))},
            manufacturer="Evergy",
            model="Evergy.com Utility Account",
            name=str(self._evergy_api.dashboard_data['addresses'][0]['street'])
        )

    @property
    def native_value(self):
        if self._sensor_type == "address":
            return str(self._evergy_api.dashboard_data['addresses'][0]['street'])
        elif(self._sensor_type == "billAmount" or self._sensor_type == "isPastDue"):
            return str(self._evergy_api.dashboard_data[self._sensor_type])
        elif self._evergy_api.usage_data != None:
            return str(self._evergy_api.usage_data[-1][self._sensor_type])
        else:
            return None

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return True

    @property
    def device_class(self):
        if(self._attr_native_unit_of_measurement == "kWh"): return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        if(self._sensor_type == "usage"): return SensorStateClass.TOTAL_INCREASING
        if(self._sensor_type == "cost"): return SensorStateClass.TOTAL_INCREASING
    

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )
