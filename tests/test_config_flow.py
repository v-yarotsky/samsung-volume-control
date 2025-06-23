"""Test Samsung TV Volume config flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant import config_entries, data_entry_flow
from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST, CONF_NAME
from pytest_homeassistant_custom_component.common import mock_config_flow, MockConfigEntry
from custom_components.samsung_tv_volume import config_flow
from custom_components.samsung_tv_volume.const import DOMAIN


class TestSamsungTVVolumeConfigFlow:
    """Test Samsung TV Volume config flow."""

    async def test_ssdp_discovery_success(self, hass, mock_ssdp_info):
        """Test successful SSDP discovery creates config entry."""
        with patch('custom_components.samsung_tv_volume.config_flow.UpnpFactory') as mock_factory:
            mock_device = AsyncMock()
            mock_device.device_info = {
                "friendly_name": "[TV]Samsung LED60",
                "manufacturer": "Samsung Electronics",
                "model_name": "UN60H7100",
                "udn": "uuid:08583b01-008c-1000-817d-bc148594dddb"
            }
            # Make the factory.async_create_device() call return the mock device
            mock_factory_instance = AsyncMock()
            mock_factory_instance.async_create_device = AsyncMock(return_value=mock_device)
            mock_factory.return_value = mock_factory_instance
            
            # Test config flow directly
            flow = config_flow.SamsungTVVolumeConfigFlow()
            flow.hass = hass
            flow.context = {"source": config_entries.SOURCE_SSDP}
            
            result = await flow.async_step_ssdp(mock_ssdp_info)
            
            assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
            assert result["title"] == "[TV]Samsung LED60"
            assert result["data"][CONF_HOST] == "192.168.1.219"
            assert result["data"][CONF_NAME] == "[TV]Samsung LED60"
            assert result["data"]["location"] == "http://192.168.1.219:7676/smp_14_"
            assert result["data"]["udn"] == "uuid:08583b01-008c-1000-817d-bc148594dddb"

    async def test_ssdp_discovery_already_configured(self, hass, mock_ssdp_info):
        """Test SSDP discovery aborts if device already configured."""
        # First add a config entry to make it appear already configured
        mock_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="uuid:08583b01-008c-1000-817d-bc148594dddb",
            data={"host": "192.168.1.219", "name": "[TV]Samsung LED60"},
        )
        mock_entry.add_to_hass(hass)
        
        flow = config_flow.SamsungTVVolumeConfigFlow()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_SSDP}
        
        # Mock the UPnP factory to avoid network call
        with patch('custom_components.samsung_tv_volume.config_flow.UpnpFactory') as mock_factory:
            mock_factory.return_value.async_create_device.side_effect = Exception("Should not reach here")
            
            with pytest.raises(data_entry_flow.AbortFlow) as exc_info:
                await flow.async_step_ssdp(mock_ssdp_info)
        
        assert exc_info.value.reason == "already_configured"

    async def test_ssdp_discovery_non_samsung_device(self, hass):
        """Test SSDP discovery ignores non-Samsung devices."""
        flow = config_flow.SamsungTVVolumeConfigFlow()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_SSDP}
        
        # Non-Samsung device
        mock_ssdp_info = ssdp.SsdpServiceInfo(
            ssdp_usn="uuid:12345678-1234-1234-1234-123456789abc::urn:schemas-upnp-org:service:RenderingControl:1",
            ssdp_st="urn:schemas-upnp-org:service:RenderingControl:1", 
            ssdp_location="http://192.168.1.100:8080/description.xml",
            upnp={
                "manufacturer": "Sony Corporation",
                "friendlyName": "Sony TV"
            },
            ssdp_headers={
                "SERVER": "Linux/3.14.0 UPnP/1.0 Sony-UPnP-Stack/1.0"
            }
        )
        
        result = await flow.async_step_ssdp(mock_ssdp_info)
        
        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "not_samsung_tv"

    async def test_ssdp_discovery_connection_error(self, hass, mock_ssdp_info):
        """Test SSDP discovery handles connection errors gracefully."""
        flow = config_flow.SamsungTVVolumeConfigFlow()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_SSDP}
        
        with patch('custom_components.samsung_tv_volume.config_flow.UpnpFactory') as mock_factory:
            mock_factory.return_value.async_create_device.side_effect = ConnectionError("Device unreachable")
            
            result = await flow.async_step_ssdp(mock_ssdp_info)
            
            assert result["type"] == data_entry_flow.FlowResultType.ABORT
            assert result["reason"] == "cannot_connect"

    async def test_ssdp_discovery_invalid_device(self, hass, mock_ssdp_info):
        """Test SSDP discovery handles invalid UPnP devices."""
        flow = config_flow.SamsungTVVolumeConfigFlow()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_SSDP}
        
        with patch('custom_components.samsung_tv_volume.config_flow.UpnpFactory') as mock_factory:
            mock_factory.return_value.async_create_device.side_effect = Exception("Invalid device description")
            
            result = await flow.async_step_ssdp(mock_ssdp_info)
            
            assert result["type"] == data_entry_flow.FlowResultType.ABORT
            assert result["reason"] == "invalid_device"