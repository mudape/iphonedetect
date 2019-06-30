  
This component sends a message to the defined hosts on udp port 5353.  
iPhone's responds, even when in deep sleep, and an entry in the arp cache is made . 

### Requirements
You have to assign <b>static</b> ip address(es) to your iPhone('s), probably in your router.  

### Configuration
Add to configuration.yaml

```yaml
device_tracker:
  - platform: iphonedetect
    consider_home: 60
    hosts:
      hostname1: 192.168.0.17
      hostname2: 192.168.0.24
```
