#!/usr/bin/env python

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, UserSwitch

if '__main__' == __name__:

    "Assign a remote controller for the network"
    net = Mininet(controller=RemoteController, switch=UserSwitch, autoStaticArp=True)

    "Create the controller"
    net_controller = net.addController('net_controller', port=6653, ip='134.226.55.22')

    "Switch 1"
    s1 = net.addSwitch('s1', dpid='000000000001')
    
    "Switch 2"
    s2 = net.addSwitch('s2', dpid='000000000002')

    "Host 1"
    h1 = net.addHost('h1', mac='00:00:00:00:01:00')

    "Host 2" 
#    h2 = net.addHost('h2', mac='00:00:00:00:02:00')

    "Host 3"
    h3 = net.addHost('h3', mac='00:00:00:00:03:00')

    "Linear links"
    net.addLink(h1,s1)
    net.addLink(s1,s2)
#    net.addLink(h2,s1)
    net.addLink(h3,s2)

    "Build mininet"
    net.build()

    "Start the Controller"
    net_controller.start()

    "Assign controller to network devices"
    s1.start([net_controller])
    s2.start([net_controller])

    cmd = h1.cmd('echo hello world from h1')
    #print(cmd)

    CLI(net)

    net.stop()
