"""Samsung TV Volume Control MediaPlayer entity."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import callback, HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SamsungTVCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Samsung TV MediaPlayer from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Create MediaPlayer entity
    entity = SamsungTVMediaPlayer(coordinator)

    async_add_entities([entity], True)


class SamsungTVMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Samsung TV MediaPlayer entity with volume control."""

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        """Initialize the MediaPlayer entity."""
        super().__init__(coordinator)
        self._attr_name = coordinator.name
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.location.replace(':', '_').replace('/', '_')}"
        )
        self._attr_supported_features = MediaPlayerEntityFeature.VOLUME_SET

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info for the Samsung TV."""
        upnp_device_info = self.coordinator.get_device_info()
        if not upnp_device_info:
            return None

        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=upnp_device_info["friendly_name"],
            manufacturer=upnp_device_info["manufacturer"],
            model=upnp_device_info["model_name"],
            serial_number=upnp_device_info.get("serial_number"),
            sw_version=upnp_device_info.get("model_number"),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available

    @property
    def state(self) -> str:
        """Return the state of the media player."""
        if self.available:
            return STATE_ON
        return STATE_OFF

    @property
    def volume_level(self) -> float | None:
        """Return volume level of the media player (0..1)."""
        if self.coordinator.data:
            return self.coordinator.data.get("volume_level")
        return None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return True if volume is currently muted."""
        if self.coordinator.data:
            return self.coordinator.data.get("is_volume_muted")
        return None

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self.coordinator.async_set_volume(volume)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Called when entity is added to hass."""
        await super().async_added_to_hass()
        _LOGGER.debug("Samsung TV MediaPlayer entity added to Home Assistant")
