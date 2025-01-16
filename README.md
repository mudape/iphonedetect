# iPhone Detect for Home-Assistant

[![Validate with hassfest](https://github.com/mudape/iphonedetect/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mudape/iphonedetect/actions/workflows/hassfest.yaml)
[![HACS Validate](https://github.com/mudape/iphonedetect/actions/workflows/hacs_action.yml/badge.svg)](https://github.com/mudape/iphonedetect/actions/workflows/hacs_action.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/custom-components/hacs)

![downloads](https://img.shields.io/github/downloads/mudape/iphonedetect/total.svg)
![downloads](https://img.shields.io/github/downloads/mudape/iphonedetect/1.4.2/total.svg)
![downloads](https://img.shields.io/github/downloads/mudape/iphonedetect/latest/total.svg)

This integration sends a mDNS message to defined hosts.  
The device responds if it's connected to the network, even when in deep sleep, and an entry in the ARP cache is made and read.  
Usefull as a [device_tracker](https://www.home-assistant.io/integrations/device_tracker/) for your [person](https://www.home-assistant.io/integrations/person/) integration to see if users are at home.

## Installation

After installation you need to **restart** Home-Assistant before using the integration.

### Using HACS  

If you dont' have [HACS](https://hacs.xyz) installed yet, I highly recommend it.  
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mudape&repository=iphonedetect&category=integration) or search for `iPhone Device Tracker`.

### Manual  

Download the `iphonedetect` directory and place in your `<config>/custom_component`

## Configuration  

### Network

Assign a **static** IP address to the device you want to track, probably in your router.  
Alternative, set a manual IP in your device WiFi configuration.  
Avoid automatically connect to differtent SSID's (2.4 and 5 ghz bands)  

### Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=iphonedetect)

If you don't have [My Home Assistant](https://my.home-assistant.io/) redirects set up, go to Settings -> Devices & Services  
Click "Add integration" and search for `iPhone Device Tracker`

Give the entity a unique `name` and enter its IP address.  

![image](https://github.com/user-attachments/assets/c4583955-72d8-4c3a-81b4-062a134af11e)

This will create an entity `device_tracker.<name>`  

Repeat the steps for additional entities.

#### Options

You can change the consider home timeout per tracked device in the UI.  
Default is 24 seconds.  
![image](https://github.com/user-attachments/assets/caf31775-333d-448c-b8f2-660534d856d7)

#### Reconfigure

You can change the IP address of the tracked device in the UI.  
![image](https://github.com/user-attachments/assets/4fc98224-eee6-4451-aaf1-b16c858014d2)

## Troubleshooting | FAQ  

<details>
<summary>Private Wi-Fi address</summary>
The device private MAC address will remain the same for each network, as long as the network isn't recreated or rotating (iOS 18+) MAC is used.  

In other words, if a tracked device no longer can be found the user have propably recreated the connection to your Wi-Fi forcing a new random MAC address to be used.  
<br />
Note that if your WiFi has different SSID for the 2.4 and 5 ghz bands, and the phone has private network enabled, two different MAC will be presented to the DHCP.  
Most likely that will require the integration to track two IP's per user/Person.
<br />
So, for best result only have/connect to one SSID, turn off private network and assign static IP.
</details>
<details>
<summary>False or flaky not_home status</summary>
Especially when the network has multiple Access Points, tracked devices sometimes are marked as not_home when actually connected to the network.  
Increasing the consider home timeout might help this.  
Most likely it's a network issue though, try placing your AP's at different locations.  

Devices might auto-update during night, they of course then will be not_home for awhile.  
</details>

## Attribution

Original idea from [return01](https://community.home-assistant.io/u/return01)

## Disclaimer  

Author is in no way affiliated with Apple Inc.  
Author does not guarantee functionality of this integration and is not responsible for any damage.  
All product names, trademarks and registered trademarks in this repository, are property of their respective owners.  

<a href="https://www.buymeacoffee.com/MudApe" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
