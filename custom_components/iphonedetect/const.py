"""Constants for the iPhone Device Tracker integration."""

DOMAIN = "iphonedetect"

NAME = "iPhone Device Tracker"

DEFAULT_CONSIDER_HOME: int = 28
MAX_CONSIDER_HOME: int = 90
MIN_CONSIDER_HOME: int = 15

CONF_PROBE_ARP = "arp"
CONF_PROBE_IP_NEIGH = "ip_neigh"
CONF_PROBE_IPROUTE = "ip_route"
