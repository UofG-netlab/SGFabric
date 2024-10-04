# Written by Xicheng Li

from tabnanny import verbose
from scapy.all import sniff, Ether, sendp
from pprint import pprint

iface = "veth2"
iface_out = "veth4"

GOOSE_TYPE = 0x88b8
GOOSE_STATS = {}

def per_packet_callback(packet):
    # only GOOSE packets
    # no need to check
    
    packet_len = len(packet)
    print(f"{packet[Ether].src} -> {packet[Ether].dst} : {packet_len} bytes")
    
    global GOOSE_COUNT
    global GOOSE_DATA_LEN
    
    src_mac = packet[Ether].src
    if src_mac not in GOOSE_STATS:
        GOOSE_STATS[src_mac] = {"count": 0, "data_len": 0}
    
    GOOSE_STATS[src_mac]["count"] += 1
    GOOSE_STATS[src_mac]["data_len"] += int(packet_len)

    sendp(packet, iface=iface_out, verbose=False)

sniff(iface=iface, filter=f"ether proto {str(GOOSE_TYPE)}", prn=per_packet_callback, count=160)

# print stats
pprint(GOOSE_STATS)