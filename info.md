{% if installed %}
## Changes as compared to your installed version:

### Breaking Changes

### Changes
- Remove minimum Home-Assistant release from manifest.json

### Features
- Add [Hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/)  
{% endif %}  
Tracks iPhones connected to local wifi, even when they are in deep sleep.  

### Requirements
You have to assign <b>static</b> IP address(es) to your iPhone(s), probably in your router.  

### Configuration
Add to configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    consider_home: 60
    new_device_defaults:
      track_new_devices: true
    hosts:
      hostname1: 192.168.0.17
      hostname2: 192.168.0.24
```
