"""Test Samsung TV Volume Control integration setup."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME

from custom_components.samsung_tv_volume import async_setup_entry, async_unload_entry
from custom_components.samsung_tv_volume.const import DOMAIN


class TestSamsungTVVolumeInit:
    """Test Samsung TV Volume Control integration initialization."""

    async def test_setup_entry_creates_coordinator(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry setup creates coordinator."""
        mock_config_entry.add_to_hass(hass)
        
        with patch('custom_components.samsung_tv_volume.SamsungTVCoordinator') as mock_coordinator_class:
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator
            
            with patch.object(hass.config_entries, 'async_forward_entry_setups') as mock_forward:
                # Test setup
                result = await async_setup_entry(hass, mock_config_entry)
                
                assert result is True
                
                # Verify coordinator was created with correct parameters
                mock_coordinator_class.assert_called_once_with(
                    hass,
                    mock_config_entry.data["location"],
                    mock_config_entry.data[CONF_NAME]
                )
                
                # Verify coordinator is stored
                assert DOMAIN in hass.data
                assert mock_config_entry.entry_id in hass.data[DOMAIN]
                assert "coordinator" in hass.data[DOMAIN][mock_config_entry.entry_id]
                
                # Verify initial refresh was called
                mock_coordinator.async_config_entry_first_refresh.assert_called_once()
                
                # Verify platforms were set up
                mock_forward.assert_called_once_with(mock_config_entry, ["media_player"])

    async def test_setup_entry_forwards_platforms(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry setup forwards to media_player platform."""
        mock_config_entry.add_to_hass(hass)
        
        with patch('custom_components.samsung_tv_volume.SamsungTVCoordinator') as mock_coordinator_class:
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator
            
            with patch.object(hass.config_entries, 'async_forward_entry_setups') as mock_forward:
                # Test setup
                result = await async_setup_entry(hass, mock_config_entry)
                
                assert result is True
                
                # Verify platforms were set up
                mock_forward.assert_called_once_with(mock_config_entry, ["media_player"])

    async def test_setup_entry_handles_coordinator_error(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry setup handles coordinator setup errors."""
        mock_config_entry.add_to_hass(hass)
        
        with patch('custom_components.samsung_tv_volume.SamsungTVCoordinator') as mock_coordinator_class:
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock(side_effect=Exception("Setup failed"))
            mock_coordinator_class.return_value = mock_coordinator
            
            with patch.object(hass.config_entries, 'async_forward_entry_setups'):
                # Test setup with error
                result = await async_setup_entry(hass, mock_config_entry)
                
                # Setup should fail gracefully
                assert result is False

    async def test_unload_entry_success(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry unload success."""
        # First set up the entry
        mock_config_entry.add_to_hass(hass)
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinator": AsyncMock()}}
        
        with patch.object(hass.config_entries, 'async_unload_platforms') as mock_unload:
            mock_unload.return_value = True
            
            # Test unload
            result = await async_unload_entry(hass, mock_config_entry)
            
            assert result is True
            
            # Verify platforms were unloaded
            mock_unload.assert_called_once_with(mock_config_entry, ["media_player"])
            
            # Verify data was cleaned up
            assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})

    async def test_unload_entry_failure(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry unload failure."""
        mock_config_entry.add_to_hass(hass)
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinator": AsyncMock()}}
        
        with patch.object(hass.config_entries, 'async_unload_platforms') as mock_unload:
            mock_unload.return_value = False
            
            # Test unload failure
            result = await async_unload_entry(hass, mock_config_entry)
            
            assert result is False
            
            # Verify data was NOT cleaned up on failure
            assert mock_config_entry.entry_id in hass.data[DOMAIN]

    async def test_coordinator_cleanup_on_unload(self, hass: HomeAssistant, mock_config_entry):
        """Test coordinator is properly shut down on unload."""
        mock_config_entry.add_to_hass(hass)
        
        # Set up with coordinator
        mock_coordinator = AsyncMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinator": mock_coordinator}}
        
        with patch.object(hass.config_entries, 'async_unload_platforms', return_value=True):
            # Test unload
            result = await async_unload_entry(hass, mock_config_entry)
            
            assert result is True
            
            # Verify coordinator shutdown was called
            mock_coordinator.async_shutdown.assert_called_once()