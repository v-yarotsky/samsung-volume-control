"""UPnP device management for Samsung TV Volume Control."""
from __future__ import annotations

import logging
from typing import Any

from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.profiles.dlna import DmrDevice

_LOGGER = logging.getLogger(__name__)


class SamsungTVUPnPDevice:
    """Manages UPnP connection and volume control for Samsung TV."""

    def __init__(self, location: str) -> None:
        """Initialize the UPnP device manager."""
        self.location = location
        self._dmr_device: DmrDevice | None = None
        self._requester: AiohttpRequester | None = None

    async def async_setup(self) -> None:
        """Set up the UPnP device connection."""
        _LOGGER.debug("Setting up UPnP device at %s", self.location)
        
        try:
            self._requester = AiohttpRequester(timeout=10)
            factory = UpnpFactory(self._requester)
            upnp_device = await factory.async_create_device(self.location)
            self._dmr_device = DmrDevice(upnp_device)
            
            _LOGGER.debug("Successfully created DmrDevice for %s", self.location)
            
        except Exception as err:
            _LOGGER.error("Failed to create UPnP device at %s: %s", self.location, err)
            raise

    async def async_get_volume(self) -> int:
        """Get current volume level."""
        if not self._dmr_device:
            raise RuntimeError("Device not set up")
            
        try:
            volume = await self._dmr_device.async_get_volume()
            _LOGGER.debug("Current volume: %s", volume)
            return volume
        except Exception as err:
            _LOGGER.error("Failed to get volume: %s", err)
            raise

    async def async_set_volume(self, volume: int) -> None:
        """Set volume level."""
        if not self._dmr_device:
            raise RuntimeError("Device not set up")
            
        if not 0 <= volume <= 100:
            raise ValueError(f"Volume must be between 0 and 100, got {volume}")
            
        try:
            await self._dmr_device.async_set_volume(volume)
            _LOGGER.debug("Set volume to %s", volume)
        except Exception as err:
            _LOGGER.error("Failed to set volume to %s: %s", volume, err)
            raise

    async def async_close(self) -> None:
        """Close the UPnP device connection."""
        if self._requester:
            await self._requester.close()
            self._requester = None
        self._dmr_device = None
        _LOGGER.debug("Closed UPnP device connection")

    @property
    def is_connected(self) -> bool:
        """Return if device is connected."""
        return self._dmr_device is not None