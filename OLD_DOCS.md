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
