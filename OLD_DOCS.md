How to control Samsung TV using UPnP

When the TV turns on, it'll become discoverable via SSDP.
We can then discover the SOAP endpoint and use it to control the TV volume.
We should gracefully handle TV being turned off (becoming unavailable) and on (becoming available again).

We are building a custom Home Assistant component to be published via HACS that uses SSDP discovery and creates a MediaPlayer entity that supports getting/setting volume.
We use test driven development. When something is unclear, ask for clarification instead of making assumptions.
When using APIs, check documentation using the links below or context7 MCP instead of making assumptions.

Reference the following documentation:
- https://developers.home-assistant.io/docs/creating_integration_manifest/#ssdp
- https://developers.home-assistant.io/docs/network_discovery#ssdp
- https://github.com/ludeeus/integration_blueprint
- https://github.com/MatthewFlamm/pytest-homeassistant-custom-component
- https://developers.home-assistant.io/docs/core/integration_system_health
- https://developers.home-assistant.io/docs/core/entity/media-player (we'll support VOLUME_SET feature only)
- https://developers.home-assistant.io/docs/config_entries_config_flow_handler
- https://github.com/plugwise/plugwise_usb-beta/blob/main/tests/test_config_flow.py

I have previously had this JavaScript code to discover the device, use it to figure out how to do it with HomeAssistant:
```
// uses ssdp npm package
var client = new ssdp.Client({});

client.search('urn:schemas-upnp-org:service:RenderingControl:1');

client.on('response', function(headers, statusCode, rinfo) {
  if (headers.ST != 'urn:schemas-upnp-org:service:RenderingControl:1' ||
      !headers.SERVER.includes('Samsung')) {
      return;
  }
  node.send({
    url: headers.LOCATION
  });
  client.stop();
});

setTimeout(function() {
    client.stop();
}, 5000);

var services = msg.payload.root.device[0].serviceList[0].service;
var service = services.find(function(svc) {
    return svc.serviceType[0] == "urn:schemas-upnp-org:service:RenderingControl:1";
});
var url = new URL(msg.url);
url.pathname = service.controlURL[0];

url.toString(); // this is the upnp endpoint used for all requests


The payloads and headers I used to control the device:

Get volume:
```
// Headers
{
  "User-Agent": "node-red",
  "Accept": "*/*",
  "Content-Type": 'text/xml; charset="utf-8"',
  "Content-Length": msg.payload.length,
  "SOAPACTION": '"urn:schemas-upnp-org:service:RenderingControl:1#GetVolume"',
  "Connection": "close"
}

// Payload
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetVolume xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
      <InstanceID>0</InstanceID>
      <Channel>Master</Channel>
    </u:GetVolume>
  </s:Body>
</s:Envelope>
```

Set volume:
```
// Headers
{
  "User-Agent": "node-red",
  "Accept": "*/*",
  "Content-Type": 'text/xml; charset="utf-8"',
  "Content-Length": msg.payload.length,
  "SOAPACTION": '"urn:schemas-upnp-org:service:RenderingControl:1#SetVolume"',
  "Connection": "close"
}

// Payload
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:SetVolume xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
      <InstanceID>0</InstanceID>
      <DesiredVolume>VALUE_0_TO_100</DesiredVolume>
      <Channel>Master</Channel>
    </u:SetVolume>
  </s:Body>
</s:Envelope>
```

## Updated Implementation Approach

We now use `async-upnp-client` library instead of manual SOAP requests. This provides:
- Automatic UPnP device discovery and service parsing
- Built-in SOAP request handling
- Real-time volume change events via UPnP event subscriptions
- Home Assistant integration compatibility

### UPnP Endpoint Discovery

Use `async-upnp-client` to discover Samsung TV RenderingControl service:

```bash
# Search for Samsung TV RenderingControl service
pipx run async-upnp-client --pprint search --search_target "urn:schemas-upnp-org:service:RenderingControl:1"

# Expected output for Samsung TV:
{
    "LOCATION": "http://192.168.1.219:7676/smp_14_",
    "SERVER": "SHP, UPnP/1.0, Samsung UPnP SDK/1.0",
    "ST": "urn:schemas-upnp-org:service:RenderingControl:1",
    "USN": "uuid:08583b01-008c-1000-817d-bc148594dddb::urn:schemas-upnp-org:service:RenderingControl:1"
}
```

### Real-time Volume Change Events

Samsung TVs support UPnP event subscriptions for instant volume change notifications:

```bash
# Subscribe to volume change events
pipx run async-upnp-client --pprint subscribe "http://192.168.1.219:7676/smp_14_" RC

# Expected event output when volume changes:
{
    "timestamp": 1750646634.707767,
    "service_id": "urn:upnp-org:serviceId:RenderingControl",
    "service_type": "urn:schemas-upnp-org:service:RenderingControl:1",
    "state_variables": {
        "LastChange": "<Event xmlns=\"urn:schemas-upnp-org:metadata-1-0/RCS/\"><InstanceID val=\"0\"><Volume channel=\"Master\" val=\"17\"/></InstanceID></Event>",
        "Volume": 17
    }
}
```

### Integration Architecture

1. **SSDP Discovery**: Home Assistant automatically discovers Samsung TVs via manifest.json SSDP matcher
2. **Device Setup**: Use `async-upnp-client` to create UPnP device from discovered LOCATION URL
3. **Volume Control**: Use DmrDevice profile for get/set volume operations
4. **Event Subscriptions**: Subscribe to RenderingControl events for real-time volume updates
5. **MediaPlayer Entity**: Expose volume control through Home Assistant MediaPlayer interface

### Key Benefits

- ✅ No manual SOAP XML construction needed
- ✅ Real-time volume change events (no polling required)
- ✅ Robust error handling and device lifecycle management
- ✅ Home Assistant native integration patterns
- ✅ Proven working with Samsung TV hardware

## Home Assistant DataUpdateCoordinator Best Practices

Based on official Home Assistant documentation for coordinated data fetching and entity availability:

### DataUpdateCoordinator Usage Patterns

1. **Centralized Data Polling**: Use for efficient, coordinated API polling across multiple entities
2. **Error Handling**: Raise `UpdateFailed` for general API communication errors
3. **Initial Setup**: Use `async_config_entry_first_refresh()` for safe initial data loading
4. **Manual Updates**: Use `async_request_refresh()` to trigger updates outside normal interval

### Entity Availability Rules

**When to Mark Entities Unavailable:**
- "If we can't fetch data from a device or service, we should mark it as unavailable"
- Goal: Reflect current state accurately rather than showing stale data
- If some data is missing but connection exists, mark entity as "unknown" instead

**Implementation with Coordinator:**
```python
class MySensor(SensorEntity, CoordinatorEntity[MyCoordinator]):
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.identifier in self.coordinator.data
```

### Error Handling Best Practices

```python
try:
    data = await self.my_api.fetch_data()
except ApiAuthError as err:
    raise ConfigEntryAuthFailed from err
except ApiError as err:
    raise UpdateFailed(f"Error communicating with API: {err}")
```

**Key Principle**: UpdateFailed exceptions are caught by DataUpdateCoordinator framework and handled internally - they should NOT bubble up to callers. The coordinator sets `last_update_success = False` and entities become unavailable automatically.
