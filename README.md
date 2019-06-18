# iphonedetect
The idea behind this is to send a message to the iPhone on udp port 5353. 
The iPhone responds in some way so that an entry in the arp cache is made even when it is in deep sleep. 
This entry is detectet by the component.

Only ip adresses will work, no hostnames! 
So you have to assign a static ip adress to your iPhone, probably with an entry in your router. 

Scan interval time must be shorter then the arp cache is cleared, or the phone will be marked away.
Leave the default scan interval at the default value or make it shorter. 

Uses Home-Assistant's Ping device_tracker and idea/script from https://community.home-assistant.io/t/iphone-device-tracker-on-linux/13698

## Example configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    hosts:
      iphone_user1: 192.168.0.17
      iphone_user2: 192.168.0.24
```
