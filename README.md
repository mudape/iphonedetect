[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs) 
![GitHub release](https://img.shields.io/github/release/mudape/iphonedetect.svg)
![GitHub issues](https://img.shields.io/github/issues/mudape/iphonedetect.svg)
![GitHub pull requests](https://img.shields.io/github/issues-pr/mudape/iphonedetect.svg)  
# iPhone Detect
This integration sends a message to the defined hosts on udp port 5353.  
iPhone's responds, _even when in deep sleep_, and an entry in the arp cache is made .  

Uses Home Assistant's [device_tracker](https://www.home-assistant.io/components/device_tracker/) and idea/script from [return01](https://community.home-assistant.io/u/return01)

Only **ip addresses** will work, _no hostnames_!  
You have to assign a **static** ip address(es) to your iPhone's, probably in your router. 

_The interval_seconds time must be shorter then the arp cache is cleared (usally 15-45sec), or the phone will be marked not_home._
_So, leave it at the default value (12sec) or make it shorter._

## Example configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    consider_home: 60
    scan_interval: 12
    new_device_defaults:
      track_new_devices: true
    hosts:
      hostname1: 192.168.0.17
      hostname2: 192.168.0.24
```
This will create `device_tracker.hostname1` and `device_tracker.hostname2` once the devices has been detected on your wifi.  
Cycle wifi on your device to trigger their creation on first run.  

When you set up automations or scripts in the Home Assistant front end, the two states for this device are either `home` or `not_home`.

__Note__  
If you have `track_new_devices: false` (in this or any integrations specified before this) for the device_tracker component you need to manually change `track:` to true for each device in `known_devices.yaml`  
(see component settings for [device_tracker](https://www.home-assistant.io/components/device_tracker/#configuring-a-device_tracker-platform))  
```yaml
hostname1:
  icon:
  mac:
  name: hostname1
  picture:
  track: true
```

<a href="https://www.buymeacoffee.com/MudApe" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
