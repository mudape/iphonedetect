{% if prerelease %}
## NB!: This is a Beta version!
### Changes
- Re-add fallback to using 'arp'
{% endif %}
---
{% if installed %}
## Changes as compared to your installed version:

### Breaking Changes
{% if version_installed.replace("v", "").replace(".","") | int < 130  %}
- Support for using 'arp' removed, back soon
{% endif %}
### Changes
{% if version_installed.replace("v", "").replace(".","") | int < 140  %}
- Re-add fallback to using 'arp'
{% endif %}
{% if version_installed.replace("v", "").replace(".","") | int < 130  %}
- Ping all devices, then scan once per intervall
{% endif %}

### Features
{% if version_installed.replace("v", "").replace(".","") | int < 140  %}
- Add ip attribute
- GitHub Action add version to manifest.json
{% endif %}
---
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
