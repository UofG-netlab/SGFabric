#! /usr/bin/env python
from scapy.all import *
from datetime import datetime
import atexit

GOOSE_PROTOCOL = 0x88B8
INTERFACE = "DPSHMI-eth0"

mac_packet_count = {}
mac_bytes_count = {}
timestamp_list = []

def packet_callback(packet): 
     global packet_count
     global bytes_count

     if Ether in packet and packet[Ether].type == GOOSE_PROTOCOL:
          src_mac = packet[Ether].src 
          if src_mac not in mac_packet_count: 
               mac_packet_count[src_mac] = 0 
          mac_packet_count[src_mac] += 1 

          if src_mac not in mac_bytes_count: 
               mac_bytes_count[src_mac] = 0 
          mac_bytes_count[src_mac] += len(packet) 

          timestamp_capture = packet.time
          timestamp_ns = time.time_ns()
          current_time = datetime.fromtimestamp(timestamp_ns / 1e9)
          current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S") + f'.{timestamp_ns % 1_000_000_000:09d}'
          print(f"New GOOSE received at {current_time_str}: {packet.summary()}")
          print(f"Total packets: " + str(mac_packet_count[src_mac]) + ", bytes: " + str(mac_bytes_count[src_mac]))
          timestamp_list.append(current_time_str)

def exit_handler():
     print(f"Saving data...")
     f = open("exp-scapy.csv", "w")
     for entry in timestamp_list:
          f.write(str(entry) + "\n")
     f.close()
     print(f"Data saved, exiting...")

atexit.register(exit_handler)

sniff(prn=packet_callback, iface=INTERFACE, filter="ether proto 0x88B8", store=0)
