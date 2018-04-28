"""
	Title: Telefonica National Network
	Author: Alan Diaz
	Affiliation: CTVR/CONNECT centre, Trinity College Dublin
	Date: September 28th, 2016

	Description: This Pyhton script emulates the topology of the Telefonica net in Spain,
	which is composed of 21 nodes interconnected through 34 links.
				G = [N,L]
	Where G is a graph that composes the topology, N is the number of nodes, and L the number of
	links.
"""
#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import RemoteController, UserSwitch
import logging
import socket
import sys
import json

telefonica_src='/var/opt/Optical-Network-Emulation/network/telefonica/src/'
probing_instruction='python ' + telefonica_src + 'probing_packet.py'
log_file='/var/opt/Optical-Network-Emulation/network/logs/network.log'
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')

if '__main__' == __name__:

    "Assign a remote controller (Ryu-based) for net"
    net = Mininet(controller=RemoteController, switch=UserSwitch, autoStaticArp=True)

    "Create the controller net-specific"
    ryuController = net.addController('ryuController', port=6653, ip='134.226.55.22')
    #ryuController = net.addController('ryuController', port=6653, ip='127.0.0.1')

    "Create the 21 switches of the net"
    switches = []
    switches.append(net.addSwitch('s01', dpid='000000000001'))
    switches.append(net.addSwitch('s02', dpid='000000000002'))
    switches.append(net.addSwitch('s03', dpid='000000000003'))
    switches.append(net.addSwitch('s04', dpid='000000000004'))
    switches.append(net.addSwitch('s05', dpid='000000000005'))
    switches.append(net.addSwitch('s06', dpid='000000000006'))
    switches.append(net.addSwitch('s07', dpid='000000000007'))
    switches.append(net.addSwitch('s08', dpid='000000000008'))
    switches.append(net.addSwitch('s09', dpid='000000000009'))
    switches.append(net.addSwitch('s10', dpid='00000000000a'))
    switches.append(net.addSwitch('s11', dpid='00000000000b'))
    switches.append(net.addSwitch('s12', dpid='00000000000c'))
    switches.append(net.addSwitch('s13', dpid='00000000000d'))
    switches.append(net.addSwitch('s14', dpid='00000000000e'))
    switches.append(net.addSwitch('s15', dpid='00000000000f'))
    switches.append(net.addSwitch('s16', dpid='000000000010'))
    switches.append(net.addSwitch('s17', dpid='000000000011'))
    switches.append(net.addSwitch('s18', dpid='000000000012'))
    switches.append(net.addSwitch('s19', dpid='000000000013'))
    switches.append(net.addSwitch('s20', dpid='000000000014'))
    switches.append(net.addSwitch('s21', dpid='000000000015'))

    "Create the hosts that belong to the net"
    hosts = []
    hosts.append(net.addHost('h01', mac='00:00:00:00:01:00'))
    hosts.append(net.addHost('h02', mac='00:00:00:00:02:00'))
    hosts.append(net.addHost('h03', mac='00:00:00:00:03:00'))
    hosts.append(net.addHost('h04', mac='00:00:00:00:04:00'))
    hosts.append(net.addHost('h05', mac='00:00:00:00:05:00'))
    hosts.append(net.addHost('h06', mac='00:00:00:00:06:00'))
    hosts.append(net.addHost('h07', mac='00:00:00:00:07:00'))
    hosts.append(net.addHost('h08', mac='00:00:00:00:08:00'))
    hosts.append(net.addHost('h09', mac='00:00:00:00:09:00'))
    hosts.append(net.addHost('h10', mac='00:00:00:00:0a:00'))
    hosts.append(net.addHost('h11', mac='00:00:00:00:0b:00'))
    hosts.append(net.addHost('h12', mac='00:00:00:00:0c:00'))
    hosts.append(net.addHost('h13', mac='00:00:00:00:0d:00'))
    hosts.append(net.addHost('h14', mac='00:00:00:00:0e:00'))
    hosts.append(net.addHost('h15', mac='00:00:00:00:0f:00'))
    hosts.append(net.addHost('h16', mac='00:00:00:00:10:00'))
    hosts.append(net.addHost('h17', mac='00:00:00:00:11:00'))
    hosts.append(net.addHost('h18', mac='00:00:00:00:12:00'))
    hosts.append(net.addHost('h19', mac='00:00:00:00:13:00'))
    hosts.append(net.addHost('h20', mac='00:00:00:00:14:00'))
    hosts.append(net.addHost('h21', mac='00:00:00:00:15:00'))

    "Attach hosts to switches"
    for (host),(switch) in zip(hosts,switches):
        net.addLink(host, switch)

    "Generate links between switches == establish Telefonica Topology"
    net.addLink(switches[0], switches[1])
    net.addLink(switches[0], switches[2])
    net.addLink(switches[1], switches[2])
    net.addLink(switches[1], switches[3])
    net.addLink(switches[2], switches[4])
    net.addLink(switches[2], switches[6])
    net.addLink(switches[3], switches[4])
    net.addLink(switches[3], switches[9])
    net.addLink(switches[4], switches[5])
    net.addLink(switches[4], switches[7])
    net.addLink(switches[5], switches[8])
    net.addLink(switches[6], switches[8])
    net.addLink(switches[6], switches[13])
    net.addLink(switches[6], switches[14])
    net.addLink(switches[7], switches[8])
    net.addLink(switches[7], switches[10])
    net.addLink(switches[7], switches[11])
    net.addLink(switches[8], switches[12])
    net.addLink(switches[9], switches[10])
    net.addLink(switches[9], switches[20])
    net.addLink(switches[10], switches[19])
    net.addLink(switches[10], switches[20])
    net.addLink(switches[11], switches[12])
    net.addLink(switches[11], switches[18])
    net.addLink(switches[11], switches[19])
    net.addLink(switches[12], switches[13])
    net.addLink(switches[12], switches[17])
    net.addLink(switches[13], switches[14])
    net.addLink(switches[13], switches[16])
    net.addLink(switches[14], switches[15])
    net.addLink(switches[15], switches[16])
    net.addLink(switches[16], switches[17])
    net.addLink(switches[17], switches[18])
    net.addLink(switches[18], switches[19])
    net.addLink(switches[19], switches[20])

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
    server_address = ('134.226.55.100', 20001)
    #server_address = ('127.0.0.1', 20001)
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
