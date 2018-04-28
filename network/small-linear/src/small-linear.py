"""
	Title: Linear topology
	Author: Alan Diaz
	Affiliation: CONNECT Centre, Trinity College Dublin
	Date: April 20th, 2018

	Description: This Pyhton script represents a linear topology
    with only 5 nodes and 4 links.
    Built to train multi-channel control of the controller.
"""
#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import RemoteController, UserSwitch
import logging
import socket
import sys
import json

linear_topology_src='/var/opt/Optical-Network-Emulation/network/small-linear/src/'
probing_instruction='python ' + linear_topology_src + 'probing_packet.py'
log_file='/var/opt/Optical-Network-Emulation/network/logs/network.log'
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')

if '__main__' == __name__:

    "Assign a remote controller (Ryu-based) for net"
    net = Mininet(controller=RemoteController, switch=UserSwitch, autoStaticArp=True)

    "Create the controller net-specific"
    #ryuController = net.addController('ryuController', port=6653, ip='134.226.55.22')
    ryuController = net.addController('ryuController', port=6653, ip='127.0.0.1')

    "Create the 5 switches of the net"
    switches = []
    switches.append(net.addSwitch('s01', dpid='000000000001'))
    switches.append(net.addSwitch('s02', dpid='000000000002'))
    switches.append(net.addSwitch('s03', dpid='000000000003'))
    switches.append(net.addSwitch('s04', dpid='000000000004'))
    switches.append(net.addSwitch('s05', dpid='000000000005'))
    
    "Create the hosts that belong to the net"
    hosts = []
    hosts.append(net.addHost('h01', mac='00:00:00:00:01:00'))
    hosts.append(net.addHost('h02', mac='00:00:00:00:02:00'))
    hosts.append(net.addHost('h03', mac='00:00:00:00:03:00'))
    hosts.append(net.addHost('h04', mac='00:00:00:00:04:00'))
    hosts.append(net.addHost('h05', mac='00:00:00:00:05:00'))

    "Attach hosts to switches"
    for (host),(switch) in zip(hosts,switches):
        net.addLink(host, switch)

    "Generate links between switches == establish Telefonica Topology"
    net.addLink(switches[0], switches[1])
    net.addLink(switches[1], switches[2])
    net.addLink(switches[2], switches[3])
    net.addLink(switches[3], switches[4])

    "Build mininet"
    net.build()

    "Start the Ryu Controller"
    ryuController.start()

    "Start the switches controlled by Ryu SDN Controller"
    for switch in switches:
        switch.start([ryuController])
    
    "Start Drone server in each host"
    for host in hosts: 
        host.cmd('drone &')
    logging.info('Drone server running in all virtual hosts...')

    mininet_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server_address = ('134.226.55.100', 20001)
    server_address = ('127.0.0.1', 20001)
    mininet_sock.bind(server_address)

    mininet_sock.listen(1)
    logging.info('Remote Mininet Handler listening...')
    try:
        while True:
            connection, client_address = mininet_sock.accept()
            logging.info('Connection established with Remote Mininet Handler client.')
            data = connection.recv(1000)
            jdata = json.loads(data)
            flow_id = int(jdata['flow_id'])
            src_node = int(jdata['src_node'])
            dst_node = int(jdata['dst_node'])
            wavelength = jdata['wavelength']

            hosts[src_node-1].cmd(probing_instruction, flow_id, src_node, dst_node, wavelength)
            logging.info('Function probing_instruction called with flow_id: %s, src_node: %s, dst_node: %s, wavelength: %s.', str(flow_id), str(src_node), str(dst_node), str(wavelength))
            connection.close()
    except:
        logging.info('Err: Remote Mininet handler failed.')
        sys.exit(0)
    finally:
        connection.close()
        net.stop()
