#!/usr/bin/env python
#
# Send/receive UDP multicast packets.
# Requires that your OS kernel supports IP multicast.
#
# Usage:
#   mcast -s (sender, IPv4)
#   mcast -s -6 (sender, IPv6)
#   mcast    (receivers, IPv4)
#   mcast  -6  (receivers, IPv6)
#
# Modify to add interface
# Usage: -i <interface name>
#   mcast -s -i eth0 (sender, IPv4, eth0)
#   mcast -i eth0 (receivers, IPv4, eth0)

import time
import struct
import socket
import sys
import fcntl
from optparse import OptionParser

def main(opts):
    if not opts.interface:
      p.error("to specify interface is minimum ")

    if opts.interface:
       interface = opts.interface
    if opts.ipv6:
       group = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
    else:
       group = '225.0.0.250'
    if not opts.sender:
        # multicast receiver
        receiver(group, interface)
    else:
        # multicast sender
        sender(group, interface)

def sender(group, interface):
    addrinfo = socket.getaddrinfo(group, None)[0]

    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    # Set Time-to-live (optional)
    ttl_bin = struct.pack('@i', opts.ttl)
    if addrinfo[0] == socket.AF_INET: # IPv4
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    else:
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    if interface != None:
        s.bind(('', opts.port))

    while True:
        data = repr(time.time())
        s.sendto(data + '\0', (addrinfo[4][0], opts.port))
        time.sleep(1)

def receiver(group, interface):
    # Look up multicast group address in name server and find out IP version
    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create a socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind it to the port
    s.bind(('', opts.port))

    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    # Join group
    mreq = group_bin;
    if addrinfo[0] == socket.AF_INET: # IPv4
        if interface == None:
            mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        else:
            ip_addr = socket.gethostbyname(socket.gethostname())
            ip_addr_n = socket.inet_aton(ip_addr)
            mreq = group_bin + struct.pack("=4s", ip_addr_n)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        if interface == None:
            mreq = group_bin + struct.pack('@I', 0)
        else:
            #TODO: need fully test
            ip_addr = get_ip_address(interface)
            ip_addr_n = socket.inet_aton(ip_addr)
            mreq = group_bin + struct.pack("=4s", ip_addr_n)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    # Loop, printing any data we receive
    while True:
        data, sender = s.recvfrom(1500)
        while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
        print (str(sender) + '  ' + repr(data))

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

if __name__ == '__main__':
    p = OptionParser(usage="usage: %prog [ --interface <INTERFACE> ] --port <PORT_NUMBER> --send ",
                     version="%prog 0.7")
    p.add_option("-s", "--send", dest="sender", help="Send Mcast", action="store_true")
    p.add_option("-6", "--ipv6", dest="ipv6", help="Ipv6 Mcast", action="store_true")
    p.add_option("-i", "--interface", dest="interface", help="Network interface")
    p.add_option("-p", "--port", dest="port", help="Network Port", default="8123", type="int")
    p.add_option("-t", "--ttl", dest="ttl", help="Mcast ttl", default="1", type="int")
    (opts, args) = p.parse_args()
    main(opts)
