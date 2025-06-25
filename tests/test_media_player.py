"""Test Samsung TV MediaPlayer entity."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.samsung_tv_volume.media_player import SamsungTVMediaPlayer
from custom_components.samsung_tv_volume.coordinator import SamsungTVCoordinator


class TestSamsungTVMediaPlayer:
    """Test Samsung TV MediaPlayer entity."""

    async def test_media_player_setup(self, hass, mock_upnp_factory):
        """Test MediaPlayer entity initialization."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )

        entity = SamsungTVMediaPlayer(coordinator)

        # Test initial state
        assert entity.coordinator == coordinator
        assert entity.name == "Test TV"
        assert entity.unique_id is not None
        assert entity.supported_features == MediaPlayerEntityFeature.VOLUME_SET

    async def test_media_player_volume_level(self, hass, mock_upnp_factory):
        """Test MediaPlayer volume level property."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )

        # Mock coordinator data
        coordinator.data = {"volume_level": 0.75, "is_volume_muted": False}

        entity = SamsungTVMediaPlayer(coordinator)

        assert entity.volume_level == 0.75

    async def test_media_player_availability(self, hass, mock_upnp_factory):
        """Test MediaPlayer availability based on coordinator."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )
        entity = SamsungTVMediaPlayer(coordinator)
        
        # Test successful state
        await coordinator.async_refresh()
        assert coordinator.last_update_success is True
        assert entity.available is True

        # Test failure state - mock device to raise exception
        from aiohttp import ClientError
        mock_upnp_factory["dmr_device"].async_update.side_effect = ClientError("Connection failed")
        await coordinator.async_refresh()
        
        assert coordinator.last_update_success is False
        assert entity.available is False

    async def test_media_player_state(self, hass, mock_upnp_factory):
        """Test MediaPlayer state based on availability."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )
        entity = SamsungTVMediaPlayer(coordinator)

        # Test available state
        await coordinator.async_refresh()
        assert coordinator.last_update_success is True
        assert entity.state == STATE_ON

        # Test unavailable state - simulate device failure
        from aiohttp import ClientError
        mock_upnp_factory["dmr_device"].async_update.side_effect = ClientError("Connection failed")
        await coordinator.async_refresh()
        
        assert coordinator.last_update_success is False
        assert entity.state == STATE_OFF

    async def test_media_player_set_volume(self, hass, mock_upnp_factory):
        """Test MediaPlayer set volume calls coordinator."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )
        coordinator.async_set_volume = AsyncMock()

        entity = SamsungTVMediaPlayer(coordinator)

        # Test setting volume
        await entity.async_set_volume_level(0.6)

        # Verify coordinator method was called
        coordinator.async_set_volume.assert_called_once_with(0.6)

    async def test_media_player_coordinator_update(self, hass, mock_upnp_factory):
        """Test MediaPlayer responds to coordinator data updates."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )

        entity = SamsungTVMediaPlayer(coordinator)
        entity.async_write_ha_state = MagicMock()

        # Simulate coordinator data update
        coordinator.data = {"volume_level": 0.8, "is_volume_muted": False}
        entity._handle_coordinator_update()

        # Verify entity updated its state
        assert entity.volume_level == 0.8
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.parametrize("expected_lingering_timers", [True])
    async def test_media_player_device_info(self, hass, mock_upnp_factory):
        """Test MediaPlayer device info."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )

        # Set up coordinator to populate device info
        await coordinator.async_refresh()

        entity = SamsungTVMediaPlayer(coordinator)
        device_info = entity.device_info

        assert device_info is not None
        assert device_info["name"] == "[TV]Samsung LED60"  # From mock
        assert device_info["manufacturer"] == "Samsung Electronics"  # From mock
        assert device_info["model"] == "UN60H7100"  # From mock
        assert "identifiers" in device_info

    @pytest.mark.parametrize("expected_lingering_timers", [True])
    async def test_media_player_entity_integration(self, hass, mock_upnp_factory):
        """Test MediaPlayer entity integration with Home Assistant."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )

        # Mock coordinator data and availability
        mock_upnp_factory["dmr_device"].volume_level = 0.5
        await coordinator.async_refresh()

        entity = SamsungTVMediaPlayer(coordinator)

        # Add entity to hass
        await entity.async_added_to_hass()

        # Test entity state
        assert entity.volume_level == 0.5  # 50/100
        assert entity.state == STATE_ON
        assert entity.available is True

    @pytest.mark.parametrize("expected_lingering_timers", [True])
    async def test_media_player_real_time_updates(self, hass, mock_upnp_factory):
        """Test MediaPlayer receives real-time volume updates."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )
        await coordinator.async_refresh()

        entity = SamsungTVMediaPlayer(coordinator)
        entity.async_write_ha_state = MagicMock()

        # Simulate real-time volume event from TV
        coordinator.handle_volume_event(85)

        # Verify entity received the update
        assert entity.volume_level == 0.85  # 85/100

        # Note: async_write_ha_state would be called by coordinator update mechanism

    async def test_media_player_error_handling(self, hass, mock_upnp_factory):
        """Test MediaPlayer handles errors gracefully."""
        coordinator = SamsungTVCoordinator(
            hass, "http://192.168.1.219:7676/smp_14_", "Test TV", "uuid:test-udn"
        )
        coordinator.async_set_volume = AsyncMock(side_effect=Exception("Device error"))

        entity = SamsungTVMediaPlayer(coordinator)

        # Test setting volume with error should raise exception
        with pytest.raises(Exception, match="Device error"):
            await entity.async_set_volume_level(0.5)

