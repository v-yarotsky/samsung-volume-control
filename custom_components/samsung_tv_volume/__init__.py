"""Samsung TV Volume Control integration for Home Assistant."""

from typing import TYPE_CHECKING

from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, LOGGER
from .coordinator import SamsungTVCoordinator

if TYPE_CHECKING:
    pass

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Samsung TV Volume Control from a config entry."""
    LOGGER.debug("Setting up Samsung TV Volume Control: %s", entry.data)

    # Create coordinator
    coordinator = SamsungTVCoordinator(
        hass, entry.data["location"], entry.data[CONF_NAME]
    )

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Initial refresh
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        LOGGER.error("Error setting up Samsung TV coordinator: %s", err)
        return False

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Samsung TV Volume Control config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
        coordinator = entry_data.get("coordinator")
        if coordinator:
            await coordinator.async_shutdown()

        # Remove stored data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok
