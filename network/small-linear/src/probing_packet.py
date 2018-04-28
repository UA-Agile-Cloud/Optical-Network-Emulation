#! /usr/bin/env python

# This script was programmatically generated
# by Ostinato version 0.7.1 revision da551b378f72@
# The script should work out of the box mostly,
# but occassionally might need minor tweaking
# Please report any bugs at http://ostinato.org

# standard modules
import logging
import os
import sys
import time

# import ostinato modules
from ostinato.core import DroneProxy, ost_pb
from ostinato.protocols.udp_pb2 import Udp, udp
from ostinato.protocols.vlan_pb2 import Vlan, vlan
from ostinato.protocols.eth2_pb2 import Eth2, eth2
from ostinato.protocols.ip6_pb2 import Ip6, ip6
from ostinato.protocols.payload_pb2 import Payload, payload
from ostinato.protocols.mac_pb2 import Mac, mac

log_file='/var/opt/Optical-Network-Emulation/network/logs/probing_packet.log'
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')

logging.info('probing_packet: Entering...')
# Receive as parameters: flow_id, src_node, dst_node, wavelength
if len(sys.argv) < 4:
    print("Err: Invalid number of arguments.")
    print("Run: python <file> flow_id src_node dst_node wavelength")
    sys.exit(0)

flow_id = sys.argv[1]
src_node = sys.argv[2]
dst_node = sys.argv[3]
wavelength = sys.argv[4]

def get_flow_label(_lambda):
    if(len(_lambda) < 2):
            _lambda = "0" + str(_lambda)
    flow_label = str(_lambda) + "000"
    print('GET_FLOW_LABEL')
    print(flow_label)
    return int(flow_label, 16)

def get_flow_id(flow_id):
    print('GET_FLOW_ID')
    print(flow_id)
    if(len(flow_id) == 1):
            flow_id = "00" + flow_id
    elif(len(flow_id) == 2):
            flow_id = "0" + flow_id
    return int(flow_id)

def get_node_addr(node_id):
    if(len(node_id) < 1):
            node_id = "0" + node_id
    node_addr = node_id + "00"
    return int(node_addr, 16)

# initialize the below variables appropriately to avoid manual input
host_name = '127.0.0.1'
tx_port_number = 0

# setup logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

drone = DroneProxy(host_name)

try:
    # connect to drone
    log.info('connecting to drone(%s:%d)' 
            % (drone.hostName(), drone.portNumber()))
    drone.connect()

    # setup tx port list
    tx_port = ost_pb.PortIdList()
    tx_port.port_id.add().id = tx_port_number;

    # ------------#
    # add streams #
    # ------------#
    stream_id = ost_pb.StreamIdList()
    stream_id.port_id.id = tx_port_number
    stream_id.stream_id.add().id = 0
    drone.addStream(stream_id)

    # ------------------#
    # configure streams #
    # ------------------#
    stream_cfg = ost_pb.StreamConfigList()
    stream_cfg.port_id.id = tx_port_number

    # stream 0 
    s = stream_cfg.stream.add()
    s.stream_id.id = 0
    s.core.is_enabled = True
    s.core.frame_len = 70

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kMacFieldNumber
    p.Extensions[mac].dst_mac = get_node_addr(src_node)
    p.Extensions[mac].src_mac = get_node_addr(dst_node)

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kVlanFieldNumber
    p.Extensions[vlan].vlan_tag = get_flow_id(flow_id)
    print('VLAN TAG IN PROBING PACKET')
    print(p.Extensions[vlan].vlan_tag)

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kEth2FieldNumber
    p.Extensions[eth2].type = 0x86dd
    p.Extensions[eth2].is_override_type = True

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kIp6FieldNumber
    p.Extensions[ip6].flow_label = get_flow_label(wavelength)

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kUdpFieldNumber

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kPayloadFieldNumber

    drone.modifyStream(stream_cfg)
    # clear tx/rx stats
    log.info('clearing tx stats')
    drone.clearStats(tx_port)

    log.info('starting transmit')
    drone.startTransmit(tx_port)

    # wait for transmit to finish
    log.info('waiting for transmit to finish ...')
    while True:
        try:
            time.sleep(2)
            tx_stats = drone.getStats(tx_port)
            if tx_stats.port_stats[0].state.is_transmit_on == False:
                break
        except KeyboardInterrupt:
            log.info('transmit interrupted by user')
            break

    # stop transmit and capture
    log.info('stopping transmit')
    drone.stopTransmit(tx_port)

    # get tx stats
    log.info('retreiving stats')
    tx_stats = drone.getStats(tx_port)

    log.info('tx pkts = %d' % (tx_stats.port_stats[0].tx_pkts))

    # delete streams
    log.info('deleting tx_streams')
    drone.deleteStream(stream_id)

    # bye for now
    drone.disconnect()

except Exception as ex:
    log.exception(ex)
    sys.exit(1)
