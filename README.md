[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs) 
![GitHub release](https://img.shields.io/github/release/mudape/iphonedetect.svg)
![GitHub issues](https://img.shields.io/github/issues/mudape/iphonedetect.svg)
![GitHub pull requests](https://img.shields.io/github/issues-pr/mudape/iphonedetect.svg)  
# iPhone Detect
This component sends a message to the defined hosts on udp port 5353.  
iPhone's responds, even when in deep sleep, and an entry in the arp cache is made .  

Uses Home Assistant's [Ping](https://www.home-assistant.io/components/ping/#presence-detection) [device_tracker](https://www.home-assistant.io/components/device_tracker/) and idea/script from [return01](https://community.home-assistant.io/t/iphone-device-tracker-on-linux/13698)

Only **ip adresses** will work, _no hostnames_!  
You have to assign a **static** ip adress(es) to your iPhone's, probably in your router. 

_The interval_seconds time must be shorter then the arp cache is cleared (usally 15-45sec), or the phone will be marked not_home._
_So, leave it at the default value (12sec) or make it shorter._

## Example configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    consider_home: 60
    hosts:
      hostname1: 192.168.0.17
      hostname2: 192.168.0.24
```


<a href="https://www.buymeacoffee.com/MudApe" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
