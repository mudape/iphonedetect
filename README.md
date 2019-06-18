# iphonedetect
This component sends a message to the defined hosts on udp port 5353.  
iPhone's responds, even when in deep sleep, and an entry in the arp cache is made .  

Uses Home Assistant's Ping device_tracker and idea/script from [return01](https://community.home-assistant.io/t/iphone-device-tracker-on-linux/13698)

Only **ip adresses** will work, _no hostnames_!  
You have to assign a **static** ip adress to your iPhone, probably with an entry in your router. 

Scan interval time must be shorter then the arp cache is cleared, or the phone will be marked not_home.  
Leave the scan interval at the default value or make it shorter. 

## Example configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    hosts:
      iphone_user1: 192.168.0.17
      iphone_user2: 192.168.0.24
```
