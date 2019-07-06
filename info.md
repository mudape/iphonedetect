  
Tracks iPhone's connected to local wifi, even when they are in deep sleep.  

### Requirements
You have to assign <b>static</b> ip address(es) to your iPhone('s), probably in your router.  

### Configuration
Add to configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    consider_home: 60
    new_device_defaults:
      track_new_devices: true
      hide_if_away: false
    hosts:
      hostname1: 192.168.0.17
      hostname2: 192.168.0.24
```
