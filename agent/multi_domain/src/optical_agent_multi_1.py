###
#
#   Title: Optical Agent
#   Author: Alan A. Diaz Montiel
#   Affiliation : CONNECT Centre, Trinity College Dublin
#   Email: adiazmon@tcd.ie
#   Description: The Optical Agent acts as a Bridge between the NOS
#    and the virtual switches via TCP/IP connections with a 1:M 
#    relation in both interfaces (North and South).
#
#   Note: For emulation purposes we're extending the use of Ryu
#       as the optical agent framework.
#
#   Functions:
#       - Connection establishment with NOS.
#       - Connection establishment with virtual switches.
#       - Network abstraction for the NOS.
#       - TED management of the virtual-PHY systems.
#       - Translator of OpenFlow messages from the NOS into
#           optical OpenFlow - optical Instructions.
#
###
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3

# For Control Plane management
import socket
import sys
import logging
import thread
import struct
import json
from time import sleep
import virtual_port_mapping
import link
import amplifier_attenuation
from macros import *
from decimal import *
import numpy as np
getcontext().prec = 16

############### Attention! Added by Yao, 2017-10-13. ###################### 
import Queue
import copy
############### Attention! Added by Yao, 2017-10-13. End ###################### 

log_file='/var/opt/sdn-optical/agent/multi_domain/logs/agent.log'
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')
# log_level = 'DEBUG' #Set log level
# if log_level == 'INFO':
#     logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')
# if log_level == 'DEBUG':
#     logging.basicConfig(level=logging.DEBUG)
# else:
#     logging.basicConfig(filename=log_file,level=logging.CRITICAL,format='%(asctime)s %(message)s',datefmt='%d/%m/%Y %H:%M:%S')

HELLO = bytearray('\x04\x00\x00\x10\x00\x00\x00\x2c\x00\x02\x00\x08\x00\x00\x00\x10')
FEATURE_REPLY = '\x04\x06\x00\x20\x15\xa7\xe7\x34\x01\x01\x01\x00\x00\x00\x00\x01\x02\x00\x02\x02\xff\x01\x00\x00\xff\x00\x00\xff\x00\x00\x00\x00'
WSS_SETUP_REPLY_HEADER = '\x04\x75\x00\x18\x00\x00\x00\x00'
WSS_TEARDOWN_REPLY_HEADER = '\x04\x77\x00\x18\x00\x00\x00\x00'
GET_OSNR_REPLY_HEADER = '\x04\x79\x00\x20\x00\x00\x00\x00'

WSS_SETUP_REQUEST_STR = '!QIIIIIIIII'
WSS_SETUP_REPLY_STR = '!QII'
WSS_TEARDOWN_REQUEST_STR = '!QIIIIIIIII'
WSS_TEARDOWN_REPLY_STR = '!QII'
GET_OSNR_REQUEST_STR = '!QIIIIIIII'
GET_OSNR_REPLY_STR = '!QIIII'

node_to_ports='/var/opt/sdn-optical/public/network/node_to_ports'#inversed_

############### Attention! Added by Yao, 2017-10-13. ###################### 
PROP_TH = 0.01
############### Attention! Added by Yao, 2017-10-13. End ###################### 

 #################################
#                                 #
# (Optical) Data plane management #
#                                 # 
 #################################

class OpticalAgent(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(OpticalAgent, self).__init__(*args, **kwargs)
        self.switches = {}
        self.switch_feature_reply_msg = {}
        self.socket_to_phy_conn = {}
        # STRUCTURES
        self.switch_to_flow_tables = {}
        self.switch_to_ports = {} # OSNR monitoring
        self.paths = {0: []} # Enabled paths
        self.flow_to_ipv6_flabel = {} # Validation of flows
        self.flow_to_datapath_match = {} # Per-datapath registers of
                                         # match fields for deleiton 
                                         # purpoErrses.
        self.flow_to_wavelength = {}

        self.osnr_list = [] # for debugging purposes
        self.power_list = [] # for debugging purposes
        self.noise_list = [] # for debugging purposes

        # Converting 0.2dB loss, and multiplying
        # for 80km.
        self.abs_fiber_loss = self.dB_to_abs(0)  # constant
        # Converting 6dB loss
        self.abs_WSS_loss = self.dB_to_abs(9) # constant

        self.virtual_port_mapping = virtual_port_mapping.main()
        self.links = link.Link()
        self.amplifier_attenuation = amplifier_attenuation.AmplifierAttenuation()

        try:
            thread.start_new_thread(self.inter_domain_listener,) # the comma (,) is needed
                                                                 # to represent a Tuple.
        except:
            logging.critical('__init__: Unable to create Thread for Inter-domain Agents.')

    # switch_features_handler handles the events occurring at the PHY
    # layer (the switches). The information about its connections is
    # stored in the Datapath object. This relation is being stored in
    # the dictionary self.switches {}
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        ev_msg = self.ofp_build_features_reply_msg(ev.msg)

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        self.switches[datapath.id] = datapath
#        logging.debug('switch_features_handler: datapath.id: %s', str(datapath.id))
        self._switch_to_ports(datapath.id)
        self.switch_feature_reply_msg[datapath.id] = ev_msg

        # Enable multi-threading functionality for handling
        # the different connections.
        try:
            thread.start_new_thread(self.controller_connections, (datapath.id,)) # the comma (,) is needed
                                                                                 # to represent a Tuple.
        except:
            logging.critical('switch_features_handler: Unable to create Thread for switch: ' + str(datapath.id))

    # Init the switch to ports structure.
    def _switch_to_ports(self, switch_id):
        self.switch_to_ports[switch_id] = self.init_ports(switch_id)

    # Function used for emulation purposes. Forwards the OpenFlow (original)
    # instructions into the real switches.
    def add_flow(self, datapath, priority, match, actions, buffer_id=None, flow_id=None, datapath_id=None, out_port=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

        if flow_id is not None:
            # Update flow_to_datapath_match structure for further deleiton purposes.
            self.update_flow_to_datapath_match(flow_id, datapath_id, match, out_port, inst)

    # Function used for emulation purposes. Removes the OpenFlow (original)
    # instructions into the real switches.
    def delete_flow(self, datapath, outport, match, inst):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath,
                                command=ofproto.OFPFC_DELETE_STRICT,
                                priority=1,
                                out_port=outport,
                                match=match,
                                instructions=inst)
        datapath.send_msg(mod)

    # In the emulation we're gonna be probing UDP packets carrying
    # information about wavelength and power tuning. We're checking
    # the IPv6 Flow Label for this.
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        vin_port = msg.match['in_port']

        try:
            ipv6_flabel = msg.match['ipv6_flabel']
            flow_id = msg.match['vlan_vid']

            in_port = self._inverse_virtual_port_mapping(datapath.id, vin_port)

            hex_ipv6_flabel = hex(ipv6_flabel)

            # Note: Might need to change due to multi-domain
            # constraints - edge nodes/agents, and the
            # respective packets.
            if flow_id not in self.flow_to_ipv6_flabel:
                self.flow_to_ipv6_flabel[flow_id] = (datapath.id, ipv6_flabel)

            # Separate lambda, datapath, and previous_out_port
            # from IPv6 Flow Label
            if(len(hex_ipv6_flabel) < 7):
                _lambda = hex_ipv6_flabel[2]
                previous_out_port = hex_ipv6_flabel[3:4]
                previous_hop = hex_ipv6_flabel[4:6]
            else:
                _lambda = hex_ipv6_flabel[2:4]
                previous_out_port = hex_ipv6_flabel[4:5]
                previous_hop = hex_ipv6_flabel[5:7]

            # Retrieve input power at current node
            power, noise = self.get_switch_to_ports_power_noise(datapath.id, previous_hop, previous_out_port, _lambda, flow_id)

            # Assuming usage of VLAN tag to identify
            # the different flows.
            out_port = self.get_out_port(flow_id, datapath.id)

            ############### Attention! Modified by Yao, 2017-10-13. ######################
            # Estimate input power excursion
            input_power, input_noise = self.estimate_input_power_noise(power, noise)
            sleep(0.01)
            #self.update_switch_to_ports_power_noise(datapath.id, in_port, _lambda, input_power, input_noise)
            #sleep(0.01)

            # Estimate output power excursion
            #output_power, output_noise = self.estimate_output_power_noise(input_power, input_noise, _lambda, flow_id)
            #self.update_switch_to_ports_power_noise(datapath.id, out_port, _lambda, output_power, output_noise)
            
            print(flow_id)
            print(datapath.id)
            print(in_port)
            print(out_port)
            print(_lambda)
            # Instead of power_cal, for the calculation of output_P,N
            # it is just necessary to invoke the function:
            # self.estimate_output_power_noise(input_power, input_noise, _lambda, flow_id)
            # This modifies the flow of the simulation to a hop-by-hop approach.
            _nlambda = int(_lambda, 16)
            wavelength = _nlambda - 1
            output_power, output_noise = self.estimate_output_power_noise(datapath.id, input_power, input_noise, wavelength, flow_id, out_port)
            # Update structure switch_to_ports
            self.switch_to_ports[datapath.id][out_port][0][wavelength] = output_power
            self.switch_to_ports[datapath.id][out_port][1][wavelength] = output_noise
            
            #output_power, output_noise = self.power_cal(flow_id, datapath.id, in_port, out_port, _lambda, input_power, input_noise)
            sleep(0.01)
            ############### Attention! Modified by Yao, 2017-10-13. End ######################


            if self.is_last_node_in_path(datapath.id, flow_id):
                osnr_list = []

                for path_id in self.paths:
                    if path_id is not 0:
                        path = self.paths[path_id]
                        t_lambda = self.flow_to_wavelength[path_id] - 1
                        t_osnr_list = []
                        for _tuple in path:
                            # _tuple -> (node_ID, in_port, out_port)
                            t_node_id = _tuple[0]
                            t_out_port = _tuple[2]
                            t_out_power = self.switch_to_ports[t_node_id][t_out_port][0][t_lambda]
                            t_out_noise = self.switch_to_ports[t_node_id][t_out_port][1][t_lambda]

                            t_osnr = t_out_power / t_out_noise

                            t_osnr_list.append(t_osnr)

                        osnr_list.append(t_osnr_list)

                print(osnr_list)
                print("####################################################")

            # Packet processing for sending OpenFlow Message.
            # Virtual port mapping

            virtual_out_port = self._virtual_port_mapping(datapath.id, out_port)

            ipv6_flabel_mod = self.build_ipv6_flabel(_lambda, datapath.id, out_port, flow_id)

            actions = [parser.OFPActionSetField(ipv6_flabel=ipv6_flabel_mod),
                       parser.OFPActionOutput(virtual_out_port)]

            virtual_in_port = self._virtual_port_mapping(datapath.id, in_port)
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=virtual_in_port, actions=actions)

            # Install rule to avoid this processing next time
            match = parser.OFPMatch(in_port=virtual_in_port, eth_type=0x86dd, vlan_vid=flow_id, ipv6_flabel=ipv6_flabel)
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, flow_id, datapath.id, out_port)
            else:
                self.add_flow(datapath, 1, match, actions, None, flow_id, datapath.id, out_port)

            datapath.send_msg(out)

            logging.debug('_packet_in_handler: Flow rule installed successfully.')
            logging.debug('_packet_in_handler: Packet routed successfully.')
            
        except:
            return
            #logging.debug("_packet_in_handler: Unable to route packet.")

    def _virtual_port_mapping(self, datapath_id, port):
        node = self.virtual_port_mapping[datapath_id]
        for _map in node:
            if(_map[0] == port):
                return _map[1]
        return 0

    def _inverse_virtual_port_mapping(self, datapath_id, port):
        node = self.virtual_port_mapping[datapath_id]
        for _map in node:
            if(_map[1] == port):
                if(_map[0]%2 is not 0):
                    return _map[0]
        return 0

    # Retrieve power and noise at input interface, and update fibre loss
    # and WSS impairments for this interface.
    def get_switch_to_ports_power_noise(self, datapath_id, previous_hop, previous_out_port, _lambda, flow_id):
        n_previous_hop = int(previous_hop, 16)
        n_previous_out_port = int(previous_out_port, 16)
        n_lambda = int(_lambda, 16)
        if (n_previous_out_port == 0) and (n_previous_hop == 0):
            # Starting power in 0dB and 
            # noise as low as -100dB.
            # Absolute values representation.
            power = TARGET_POWER
            noise = IN_NOISE
            self.abs_fiber_loss = self.dB_to_abs(1e-10)
            # # Converting 18dB loss (Two WSS)
            self.abs_WSS_loss = self.dB_to_abs(20)
            sleep(0.01)
            return power, noise
        elif (n_previous_out_port == 15) and (n_previous_hop == 255):
            # Inter-domain node
            # Establish connection to neighbour agent.
            power, noise = self.inter_domain_client_connection(flow_id, n_lambda)
            # Converting 0.2dB loss, and multiplying
            # for 0km.
            self.abs_fiber_loss = self.dB_to_abs(1e-10)  # constant
            # Converting 18dB loss (Two WSS)
            self.abs_WSS_loss = self.dB_to_abs(20) # constant
            sleep(0.01)
            return power, noise
        elif(self.is_last_node_in_path(datapath_id, flow_id)):
            logging.debug('get_switch_to_ports_power_noise: datapath: %s is last node in path.', str(datapath_id))
            try:
                power = self.switch_to_ports[n_previous_hop][n_previous_out_port][0][n_lambda-1]
                noise = self.switch_to_ports[n_previous_hop][n_previous_out_port][1][n_lambda-1]
                # Should be converted to last link span
                #self.update_in_fiber_loss(flow_id, datapath_id)
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                # Converting 18dB loss (Two WSS)
                self.abs_WSS_loss = self.dB_to_abs(9)
                #sleep(0.01)
                return power, noise
            except:
                logging.debug('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                print('Err: get_switch_to_ports_power_noise: unable to retrieve power/noise. Last node.')
                return 0, 0
        else:
            try:
                power = self.switch_to_ports[n_previous_hop][n_previous_out_port][0][n_lambda-1]
                noise = self.switch_to_ports[n_previous_hop][n_previous_out_port][1][n_lambda-1]
                # The updated fibre loss is not for the LONG-LINK, but the last span
                #self.update_in_fiber_loss(flow_id, datapath_id)
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                # Converting 18dB loss (Two WSS)
                self.abs_WSS_loss = self.dB_to_abs(20) # constant
                sleep(0.01)
                return power, noise
            except:
                logging.debug('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                print('Err: get_switch_to_ports_power_noise: unable to retrieve power/noise. Intermediate node.')
                return 0, 0

    def dB_to_abs(self, value):
        absolute_value = 10**(value/float(10))
        return absolute_value

    # Twin function of inter_domain_is_edge_node
    def is_last_node_in_path(self, datapath_id, flow_id):
        i = len(self.paths[flow_id])
        last_node = self.paths[flow_id][i-1][0]
        if(datapath_id == last_node):
            return True
        return False

    def is_first_node_in_path(self, datapath_id, flow_id):
        first_node = self.paths[flow_id][0][0]
        if(datapath_id == first_node):
            return True
        return False

    def is_last_node_in_path_remove(self, datapath_id, flow_id):
        i = len(self.paths[flow_id])
        # In line 278 (Commented) we add the wavelength to the
        # path. Although we're not using that in the current
        # power_cal implementation.
        #last_node = self.paths[flow_id][i-2][0]
        last_node = self.paths[flow_id][i-1][0]
        if(datapath_id == last_node):
            return True
        return False

    def update_flow_to_datapath_match(self, flow_id, datapath_id, match, out_port, inst):
        try:
            if flow_id not in self.flow_to_datapath_match:
                self.flow_to_datapath_match[flow_id] = {}
            self.flow_to_datapath_match[flow_id][datapath_id] = (match, out_port, inst)
        except:
            logging.debug("update_flow_to_datapath_match: Unable to update flow_to_datapath_match structure.")
            print('Err: update_flow_to_datapath_match: Unable to update flow_to_datapath_match structure.')

    # Note: to be modified.
    def not_valid_flow(self, flow_id, datapath_id, ipv6_flabel):
        f_ipv6_flabel_datapath = self.flow_to_ipv6_flabel[flow_id][0]
        if (datapath_id is not f_ipv6_flabel_datapath):
            logging.debug('not_valid_flow: Not primary datapath')
            return -1
        else:
            f_ipv6_flabel = self.flow_to_ipv6_flabel[flow_id][1]
            if(f_ipv6_flabel is not ipv6_flabel):
                return 0
            return -1

    def build_str_out_port_power(self, out_port_power):
        if(len(out_port_power) < 5):
                sout_port_power = "0" + out_port_power[2:4]
        else:
            sout_port_power = out_port_power[2:5]
        return sout_port_power

    def build_ipv6_flabel(self, _lambda, datapath, out_port, flow_id):
        try:
            datapath = hex(datapath)
            if(len(datapath) < 4):
                datapath = datapath[2]
            else:
                datapath = datapath[2:4]
            if self.inter_domain_is_edge_node(datapath, flow_id):
                if(len(_lambda) < 2):
                    _lambda = "0" + _lambda
                s_out_port = "f"
                s_datapath = "ff"
                sipv6_flabel = "0x" + _lambda + s_out_port + s_datapath
            else:
                s_datapath = str(datapath)
                if(len(_lambda) < 2):
                    _lambda = "0" + _lambda
                if(len(s_datapath) < 2):
                    s_datapath = "0" + s_datapath
                elif(len(s_datapath) == 2):
                    #s_datapath = self.get_hex_number(datapath)
                    s_datapath = datapath
                sipv6_flabel = "0x" + _lambda + str(out_port) + s_datapath
            hex_ipv6_flabel = int(sipv6_flabel, 16)
            return hex_ipv6_flabel
        except:
            print('Err: build_ipv6_flabel. Unable to compute ipv6_flabel')
            return "00000"

    def get_hex_number(self, datapath):
        try:
            hex_no = hex(datapath)
            str_no = str(hex_no)
            letter = str_no[2:]
            return "00" + letter
        except:
            print('Err: get_hex_number. Unable to compute hex number.')
            return "000"

    def get_out_port(self, flow_id, datapath_id):
        try:
            if flow_id in self.paths:
                flow = self.paths[flow_id]
                for _tuple in flow:
                    if _tuple[0] == datapath_id:
                        return _tuple[2]
                return -1
        except:
            print('Err: get_out_port. Unable to retrieve output port.')
            return -1

    def estimate_input_power_noise(self, in_signal_power, noise, intermediate=False):
        in_power = (in_signal_power / self.abs_fiber_loss / self.abs_WSS_loss)
        in_noise = (noise / self.abs_fiber_loss / self.abs_WSS_loss)
        return in_power, in_noise

    def estimate_output_power_noise(self, node_id, input_power, input_noise, wavelength, flow_id, out_port):
        
        print("estimate_output_power_noise: Entering with out_port: ", out_port)
        print("estimate_output_power_noise: Entering with _lambda: ", wavelength)

        if(self.is_last_node_in_path(node_id, flow_id)):
            print("estimate output power: LAST NODE")
            self.abs_WSS_loss = self.dB_to_abs(9)
            output_power = input_power / self.abs_WSS_loss
            output_noise = input_noise / self.abs_WSS_loss
            return output_power, output_noise

        dst_node = self.get_next_node(flow_id, node_id)
        # Based on the destination node, retrieve the link ID from self.links
        # and match it to the amplifier_attenuation object.
        # Then, iterate through the number of amplifiers, retrieving the corresponding
        # ripple function.
        link_ID = self.links.get_link_ID(node_id, dst_node)
        amplifiers = self.amplifier_attenuation.get_amplifier_attenuation(link_ID)

        EDFA_NO = self.links.get_EDFA_NO(node_id, dst_node)
        print("EDFA_NO: ", EDFA_NO)
        link_distance = self.links.get_link_distance(node_id, dst_node)

        amp_no = 0 # counter for amplifiers in link, applies for span_id too
        self.update_fiber_loss(STANDARD_SPAN) # set standard span length
        fibre_span = STANDARD_SPAN
        sleep(0.01)

        for function_ID in amplifiers:
            print("Entering for function_ID: %s" %function_ID)
            ripple_function = self.amplifier_attenuation.get_function(function_ID)
            amplifier_attenuation = ripple_function[wavelength]
            
            print("Fine")

            if amp_no == EDFA_NO-1:
                target_gain = self.compute_gain_last_span(input_power)
            else:
                target_gain = self.dB_to_abs(TARGET_GAIN)

            if amp_no == EDFA_NO-2:
                fibre_span = self.get_last_span_length(EDFA_NO, link_distance)
                self.abs_fiber_loss = self.dB_to_abs(0.2*fibre_span)
                sleep(0.01)

            # input_power should be the newly computed one (with SRS).
            # The replacement of this parameter could lead the way to
            # implement here the power excursion as well.
            output_power = target_gain * input_power * amplifier_attenuation
            output_noise = self.calculate_out_noise(input_noise, wavelength, target_gain*amplifier_attenuation)

            print("estimate_output_power_noise: Power and noise computed.")

            # insert "new" channel-power_level relation to active_channels.
            #if amp_no < EDFA_NO-1:
            print("insert new channel-power_level relation to active_channels, amp_no: ", amp_no)
            self.links.set_active_channel(link_ID, amp_no, wavelength, output_power, output_noise, amplifier_attenuation)

            # This is done at this point, because the input_power to be used
            # for the computation of the output_power is already sharing
            # the fibre with other channels (if any).
            active_channels_per_span = self.links.get_active_channels(link_ID, amp_no)
            print("estimate_output_power_noise: get active channel")
            # Check if active channels is  not single channel, or
            # if the loop is not at the last EDFA.
            if (len(active_channels_per_span) > 1) and (amp_no < EDFA_NO-1):
                print("Class OpticalAgent: estimate_output: Entered SRS-NORMALIZATION-EXCURSION")
                # compute SRS impairment
                new_active_channels_per_span = self.links.calculate_SRS(active_channels_per_span, fibre_span)
                print("estimate_output_power_noise: set new active channel")
                self.links.update_active_channels(link_ID, span_id, new_active_channels_per_span)
                
                # Store not normalized power and noise levels
                # to be considered in the power excursion calculation
                not_normalized_power,  not_normalized_noise = self.links.get_active_channels_power_noise(link_ID, span_id)
                
                # Consider channel-normalization per-span
                self.links.normalize_channel_levels(link_ID,  span_id)
                
                # Consider power excursion and propagation per-span
                EXCURSION_OK = self.links.power_excursion_propagation(link_ID,  span_id,  not_normalized_power,  not_normalized_noise)
                
                if EXCURSION_OK:
                    continue
                else:
                    print("estimate_output_power_noise: EXCURSION_OK error")
                    
                output_power = self.links.get_power_level(link_ID, amp_no, wavelength)
                output_noise = self.links.get_noise_level(link_ID, amp_no, wavelength)
            # compute power and noise without considering SRS

            # This is ignored in last computation.
            print("Class OpticalAgent: estimate_output: computing input_power:")
            input_power = output_power / self.abs_fiber_loss
            print("Class OpticalAgent: estimate_output: computing input_noise:")
            input_noise = output_noise / self.abs_fiber_loss

            amp_no = amp_no + 1
        print("Class OpticalAgent: estimate_output: returning power: and noise: %s" %output_noise)
        return output_power, output_noise

    def calculate_out_noise(self, input_noise, n_lambda, sys_gain):
        try:
            c_band_lambda = (1530+n_lambda*0.4)*10e-9 # Starting in 1530 nm (C-band)
            watt_to_mwatt = 1000
            out_noise = ((input_noise * sys_gain) + ((PLANCK_CONST*(SPEED_OF_LIGHT/c_band_lambda)) * sys_gain * watt_to_mwatt * NOISE_FIGURE * BANDWIDTH))
            return out_noise
        except:
            print('Err: calculate_out_noise. Unable to compute output noise.')
            return -1

    def compute_gain_last_span(self, input_power):
        try:
            target_gain = TARGET_POWER / input_power
            return target_gain
        except:
            print('Err: compute_gain_last_span. Unable to compute gain at last amplifier.')
            return -1

    def update_switch_to_ports_power_noise(self, switch, port, _lambda, power, noise):
        try:
            self.switch_to_ports[switch][port][0][_lambda_index] = power
            self.switch_to_ports[switch][port][1][_lambda_index] = noise
            logging.debug('update_switch_to_ports_power_noise: UPDATE successful.')
            print('update_switch_to_ports_power_noise: UPDATE successful.')
        except:
            logging.debug('update_switch_to_ports_power_noise: UPDATE failed.')


    def str_output_power(self, output_power):
        hex_output_power = hex(output_power)
        if(len(hex_output_power) < 5):
            soutput_power = "0" + hex_output_power[2:4]
        else:
            soutput_power = hex_output_power[2:5]
        return soutput_power

    # Note: This function requires further updates beyond this set of experiments.
    # Updates needed:
    #   - Scale the number of lambdas-per-port.
    def init_ports(self, datapath_id):
        # Declare the number of Lambdas available per port.
        # Init with a value of 0 (unused).
        #port_to_lambdas_noise = [[0, 0, 0, 0], 0]  # Not usable at this point
                                                    # due to mutable/immutable
                                                    # properties of Python.
        ports_to_lambdas_noise = {}
        ports_number = self.get_ports_number(datapath_id)
        # Assign the port_to_lambdas relation to each port
        # of the switch. Number of ports retrieved via the file
        # ~/topology-discovery/node_to_ports.
        for port in range(1,2*ports_number+1):
            # First position: Power values
            # Second position: noise values
            _struct_a = [0.0] * CHANNEL_NUMBER
            _struct_b = [0.0] * CHANNEL_NUMBER
            port_to_lambda_noise = [_struct_a, _struct_b]
            ports_to_lambdas_noise[port] = port_to_lambda_noise

        return ports_to_lambdas_noise

    # Read node_to_ports file, and retrieve number of ports
    # based on datapath ID.
    def get_ports_number(self, datapath_id):
        # Read file
        ports = open(node_to_ports)
        ports_no = [x.strip() for x in ports.readlines()]
        # Access index datapath_id - 1
        return (int(ports_no[datapath_id-1]) + 1)

 ##############################################
#                                              #
# Inter-domain Optical Agent management        #
#                                              # 
 ##############################################

    # Put up a TCP socket for inter-domain
    # agent requests. At the moment only
    # regarding power and noise values at
    # edge_node interfaces.
    def inter_domain_listener(self):
        inter_domain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 10001)
        inter_domain_sock.bind(server_address)

        inter_domain_sock.listen(1)

        try:
            while True:
                connection, client_address = inter_domain_sock.accept()
                data = connection.recv(100)
                jdata = json.loads(data)
                flow_id = int(jdata['flow_id'])
                n_lambda = int(jdata['_lambda'])
                n_previous_hop, n_previous_out_port = self.inter_domain_get_edge_node(flow_id)
                power = self.switch_to_ports[n_previous_hop][n_previous_out_port][0][n_lambda-1]
                noise = self.switch_to_ports[n_previous_hop][n_previous_out_port][1][n_lambda-1]
                connection.send(json.dumps({'power':power, 'noise':noise}))
        except:
            logging.info('inter_domain_listener: error with inter_domain_socket.')
        finally:
            # Clean up the connection
            connection.close()
            return

    # Establish a single-time connection to
    # the inter-domain agent listener. At the
    # moment only regarding power and noise
    # values at edge_node interfaces.
    def inter_domain_client_connection(self, flow_id, _lambda):
        logging.debug('inter_domain_client_connection: entering...')
        # Create a TCP/IP socket
        inter_domain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('localhost', 10002)
        inter_domain_sock.connect(server_address)

        logging.debug('inter_domain_client_connection: Initialization OK...')

        try:
    
            # Send data
            inter_domain_sock.send(json.dumps({'flow_id':flow_id, '_lambda':_lambda}))
            # Look for the response
            data = inter_domain_sock.recv(100)
            jdata = json.loads(data)
            power = float(jdata['power'])
            noise = float(jdata['noise'])

            print >>sys.stderr, 'closing client socket'
            inter_domain_sock.close()
        except:
            return 0, 0

        return power, noise

    def inter_domain_get_edge_node(self, flow_id):
        i = len(self.paths[flow_id])
        n_previous_hop = self.paths[flow_id][i-1][0]
        n_previous_out_port = self.paths[flow_id][i-1][2]
        return n_previous_hop, n_previous_out_port

    def inter_domain_is_edge_node(self, datapath, flow_id):
        datapath = int(datapath, 16)
        i = len(self.paths[flow_id])
        n_previous_hop = self.paths[flow_id][i-1][0]
        if(datapath == n_previous_hop):
            return True
        return False


 #################################
#                                 #
# Control plane management        #
#                                 # 
 #################################

# TO DO: Generate Python class ControlPlane for pure Control Plane functions (?).

    # controller_connections establishes as many connections to the
    # upper-level controller as switches exist in the data plane.
    # Could be understood as independent TCP channels, which passes data
    # from/to the controller, and from/to the switches.
    # Calls functions init_openflow(sock) & _socket_to_phy_conn(switch, sock).
    def controller_connections(self, switch):
        
        # Changing accordingly to Domain X
        controller_address = ("localhost", 6666)
        #controller_address = ("10.129.36.254", 6666)
        
        try:
            sock = socket.create_connection(controller_address)
            self._socket_to_phy_conn(switch, sock)
            self.openflow_mgmt(switch, sock) # This will loop forever to handle the
                                             # upper-level OpenFlow messages.
        except Exception as e:
            logging.critical('Unable to create socket connection to Controller')
            sys.exit()
            
    # _socket_to_phy_conn records the relations between the connections
    # (socket-based) to the upper-level controller, and the switches 
    # structure key (datapath.id-based).
    def _socket_to_phy_conn(self, switch, sock):
        self.socket_to_phy_conn[sock] = switch

    # For debugging purposes
    def end_connection(self, sock):
        sock.close()

 #################################
#                                 #
# OpenFlow management             #
#                                 # 
 #################################

    # openflow_mgmt performs the formalities of the OpenFlow Protocol
    # regarding the connections between Controller - Switch. These
    # operations are performed to 'mock' the behaviour of the PHY-
    # switches, hence providing network-abstraction to the upper-level
    # controller.
    # It also manages the upper-level instructions, and converts/
    # translates into the proper PHY-layer commands.
    def openflow_mgmt(self, switch, sock):
        # Extracted from Arizona code - Original Author: Weiyang Mo

        try:
            while(1):
                data = sock.recv(4096)
                data = [ord(c) for c in data]
                data = bytearray(data)
                if self.ofp_belong_to(data) == 'HELLO':
                    logging.info('Received Hello Request')
                    sock.sendall(HELLO)
                    logging.info('Hello Reply Sent to RYU')
                    logging.info('---------------------------------------')
                elif self.ofp_belong_to(data) == 'FEATURE_REQUEST':
                    logging.info('Received FEATURE_REQUEST')
                    FEATURE_REPLY = self.ofp_get_reply_msg(switch)
                    sock.sendall(FEATURE_REPLY)
                    logging.info('FEATURE_REPLY SENT')
                    logging.info('---------------------------------------')
                elif self.ofp_belong_to(data) == 'WSS_SETUP_REQUEST':
                    logging.info('Received WSS_SETUP_REQUEST')
                    try:
                        assert struct.calcsize(WSS_SETUP_REQUEST_STR) == len(data[8:])
                    except AssertionError as e:
                        logging.critical(e)
                        logging.critical('WSS_SETUP_REQUEST from RYU is not in a correct format')
                    result = self.ofp_setup_config_wss_request_handler(data)
                    self.ofp_setup_config_wss_reply_handler(sock, data, result)
                    logging.info('---------------------------------------')
                elif self.ofp_belong_to(data) == 'WSS_TEARDOWN_REQUEST':
                    logging.info('Received WSS_TEARDOWN_REQUEST')
                    try:
                        WSS_TEARDOWN_REQUEST_STR = '!QIIIIIIIII'
                        assert struct.calcsize(WSS_TEARDOWN_REQUEST_STR) == len(data[8:])
                    except AssertionError as e:
                        logging.critical(e)
                        logging.critical('WSS_TEARDOWN_REQUEST from RYU is not in a correct format')
                    result = self.ofp_teardown_config_wss_request_handler(data)
                    self.ofp_teardown_config_wss_reply_handler(sock, data, result)
                    logging.info('---------------------------------------')
                elif self.ofp_belong_to(data) == 'GET_OSNR_REQUEST':
                    logging.info('Received GET_OSNR_REQUEST')
                    try:
                        GET_OSNR_REQUEST_STR = '!QIIIIIIII'
                        assert struct.calcsize(GET_OSNR_REQUEST_STR) == len(data[8:])
                    except AssertionError as e:
                        logging.critical(e)
                        logging.critical('GET_OSNR_REQUEST_STR from RYU is not in a correct format')
                    osnr, result = self.ofp_get_osnr_request_handler(data)
                    self.ofp_get_osnr_reply_handler(sock, data, result, osnr)
                    logging.info('---------------------------------------')
                else:
                    pass
                    #logging.info('O T H E R')
                    #logging.info('---------------------------------------')

        except Exception as e:
            logging.critical('OOPS, something wrong when capturing received data, that might be due to the connection disruption')
            logging.critical('Can not be recovered, agent shall be manually rebooted...')
            sys.exit()
        finally:
           self.end_connection(sock)

    # Retrieve the proper values from the entry, and
    # add_flow(), once formed the
    # Matching -- OutputActions relation.
    def ofp_setup_config_wss_request_handler(self, data):

        (datapath_id,
        message_id,
        ITU_standards,
        node_id,
        input_port_id,
        output_port_id,
        start_channel,
        end_channel,
        experiment1,
        experiment2)=struct.unpack(WSS_SETUP_REQUEST_STR,data[8:])
        
        logging.info('Recieved WSS_SETUP_REQUEST from RYU')
        logging.debug(  'datapath_id=%s,message_id=%s, ' \
                        'ITU_standards=%s,node_id=%s,input_port_id=%s,output_port_id=%s,' \
                        'start_channel=%s,end_channel=%s' %(
                                                            datapath_id,
                                                            message_id,
                                                            ITU_standards,
                                                            node_id,
                                                            input_port_id,
                                                            output_port_id,
                                                            start_channel,
                                                            end_channel))

        # Instead of directly allocating each rule, this function would
        # register the (light)-path, and process the request in this
        # per-flow manner.

        # Retrieve flow ID (experiment 1)
        flow_id = experiment1
        if flow_id not in self.paths:
            self.paths[flow_id] = []
            self.flow_to_wavelength[flow_id] = start_channel
        # Add hop-information to the flows (paths) structure.
        flow_data = (node_id, input_port_id, output_port_id)
        if flow_data not in self.paths[flow_id]:
            self.paths[flow_id].append(flow_data)

        return 0

    def ofp_setup_config_wss_reply_handler(self, sock, data, result):

        (datapath_id,
        message_id)=struct.unpack('!QI',data[8:20])

        WSS_SETUP_REPLY_BODY=struct.pack(   WSS_SETUP_REPLY_STR,
                                            datapath_id,
                                            message_id,
                                            result)
        WSS_SETUP_REPLY = ''.join([WSS_SETUP_REPLY_HEADER,WSS_SETUP_REPLY_BODY])

        try:
            assert len(WSS_SETUP_REPLY) == 24
        except AssertionError as e:
            logging.critical(e)
            logging.critical('WSS_SETUP_REPLY is not in a correct format')
        sock.sendall(WSS_SETUP_REPLY)
        logging.info('WSS_SETUP_REPLY Sent to RYU')

    def ofp_teardown_config_wss_request_handler(self, data):

        (datapath_id,
        message_id,
        ITU_standards,
        node_id,
        input_port_id,
        output_port_id,
        start_channel,
        end_channel,
        experiment1,
        experiment2)=struct.unpack(WSS_TEARDOWN_REQUEST_STR,data[8:])
        
        logging.info('Recieved WSS_TEARDOWN_REQUEST from RYU')
        logging.debug(  'datapath_id=%s,message_id=%s, ' \
                        'ITU_standards=%s,node_id=%s,input_port_id=%s,output_port_id=%s,' \
                        'start_channel=%s,end_channel=%s' %(
                                                            datapath_id,
                                                            message_id,
                                                            ITU_standards,
                                                            node_id,
                                                            input_port_id,
                                                            output_port_id,
                                                            start_channel,
                                                            end_channel))

        #datapath = self.switches[datapath_id]
        #datapath = self.switches[node_id]
        #parser = datapath.ofproto_parser

        # Retrieve flow ID (experiment 1)
        flow_id = experiment1
        
        try:
            if flow_id not in self.paths:
                logging.debug('ofp_teardown_config_wss_request_handler: Non-existent flow.')
                print('ofp_teardown_config_wss_request_handler: Non-existent flow.')
                raise
            print('ofp_teardown_config_wss_request_handler: Attempting to remove flow:')
            print('node_id')
            print(node_id)
            print('flow_id')
            print(flow_id)
            print('flows')
            print(self.paths)
            if(self.is_last_node_in_path_remove(node_id, flow_id)):
                self.remove_flow(flow_id)
            logging.debug('ofp_teardown_config_wss_request_handler: Successfully removed the flow.')
            print('ofp_teardown_config_wss_request_handler: Successfully removed the flow.')
            return 0
        except:
            logging.debug('ofp_teardown_config_wss_request_handler: Failed to remove the flow.')
            print('ofp_teardown_config_wss_request_handler: Failed to remove the flow.')
            return 1

    def remove_flow(self, flow_id):
        try:
            self.clear_switch_to_ports(flow_id)
            self.flow_to_ipv6_flabel.pop(flow_id, None)
            self.flow_to_datapath_match.pop(flow_id, None)         
        except:
            logging.debug('remove_flow: Unable to remove flow: %s', flow_id)
            print('remove_flow: Unable to remove flow: %s', flow_id)

    def clear_switch_to_ports(self, flow_id):
        print('clear_switch_to_ports')
        try:
            wavelength = int(self.flow_to_wavelength[flow_id]) - 1
            for flow_data in self.paths[flow_id]:
                node_id = flow_data[0]
                input_port = flow_data[1]
                output_port = flow_data[2]
                self.switch_to_ports[node_id][input_port][0][wavelength] = 0.0
                self.switch_to_ports[node_id][input_port][1][wavelength] = 0.0
                self.switch_to_ports[node_id][output_port][0][wavelength] = 0.0
                self.switch_to_ports[node_id][output_port][1][wavelength] = 0.0
            self.paths.pop(flow_id, None)
            print(self.paths)
            self.flow_to_wavelength.pop(flow_id, None)
        except:
            logging.debug('remove_flow: Unable to remove flow: %s', flow_id)


    def ofp_teardown_config_wss_reply_handler(self, sock, data, result):

        (datapath_id,
        message_id)=struct.unpack('!QI',data[8:20])

        WSS_TEARDOWN_REPLY_BODY = struct.pack(  WSS_TEARDOWN_REPLY_STR,
                                                datapath_id,
                                                message_id,
                                                result)
        WSS_TEARDOWN_REPLY = ''.join([WSS_TEARDOWN_REPLY_HEADER, WSS_TEARDOWN_REPLY_BODY])

        try:
            assert len(WSS_TEARDOWN_REPLY) == 24
        except AssertionError as e:
            logging.critical(e)
            logging.critical('WSS_TEARDOWN_REPLY is not in a correct format')
        sock.sendall(WSS_TEARDOWN_REPLY)
        logging.info('WSS_TEARDOWN_REPLY Sent to RYU')


    def ofp_get_osnr_request_handler(self, data):
        print('ofp_get_osnr_request_handler: Entering')
        (datapath_id,
        message_id,
        ITU_standards,
        node_id,
        port_id,
        start_channel,
        end_channel,
        experiment1,
        experiment2)=struct.unpack(GET_OSNR_REQUEST_STR,data[8:])

        logging.info('Recieved GET_OSNR_REQUEST_STR from RYU')

        power = self.switch_to_ports[int(node_id)][int(port_id)][0][int(start_channel)-1]
        noise = self.switch_to_ports[int(node_id)][int(port_id)][1][int(start_channel)-1]
        print(node_id)
        print(port_id)
        print(start_channel)
        print("power: ")
        print(power)
        print("noise: ")
        print(noise)

        try:
            if(noise is 0):
                return 100, 0
            else:
                osnr = power/noise
                osnr = Decimal(10*np.log10(osnr))
                return osnr, 0
        except:
            print('Something went wrong in ofp_get_osnr_request_handler')
            return -1, 1

    def ofp_get_osnr_reply_handler(self, sock, data, result, osnr):
        (datapath_id,
        message_id,
        ITU_standards,
        node_id,
        port_id,
        start_channel,
        end_channel,
        experiment1,
        experiment2)=struct.unpack(GET_OSNR_REQUEST_STR,data[8:])

        GET_OSNR_REPLY_BODY = struct.pack(GET_OSNR_REPLY_STR,datapath_id,message_id,node_id,result,osnr)
        GET_OSNR_REPLY = ''.join([GET_OSNR_REPLY_HEADER,GET_OSNR_REPLY_BODY])
        try:
            assert len(GET_OSNR_REPLY) == 32
        except AssertionError as e:
            logging.critical(e)
            logging.critical('GET_OSNR_REPLY is not in a correct format')
            for device in NODETOCONNECTION.values():
                device.close()
            sys.exit()  
        sock.sendall(GET_OSNR_REPLY)
        logging.info('GET_OSNR_REPLY Sent to RYU')

    def ofp_get_reply_msg(self, switch):
        return self.switch_feature_reply_msg[switch]

    # Generation of the OpenFlow FEATURES_REPLY message.
    # This conversion into bytes is necessary due to
    # TCP sockets declaration.
    def ofp_build_features_reply_msg(self, ev_msg):
        version = ev_msg.version
        msg_type = ev_msg.msg_type
        msg_len= ev_msg.msg_len
        xid= ev_msg.xid
        datapath_id = ev_msg.datapath_id
        n_buffers = ev_msg.n_buffers
        n_tables = ev_msg.n_tables
        auxiliary_id = ev_msg.auxiliary_id
        capabilities = ev_msg.capabilities
        reserved = 0
        # The format required is: '!BBHIQIBBHII'
        byte_reply = struct.pack(   '!BBHIQIBB2xII',
                                    version,
                                    msg_type,
                                    msg_len,
                                    xid,
                                    datapath_id,
                                    n_buffers,
                                    n_tables,
                                    auxiliary_id,
                                    capabilities,
                                    reserved
                                )

        return byte_reply

    def ofp_belong_to(self, data):
        if data[1] == 0:
            return "HELLO"
        elif data[1] == 5: #Feature_Request
            return "FEATURE_REQUEST"
        elif data[1] == 116:
            return "WSS_SETUP_REQUEST"
        elif data[1] == 118:
            return "WSS_TEARDOWN_REQUEST"
        elif data[1] == 120:
            return "GET_OSNR_REQUEST"
            
    ############### Attention! Added by Yao, 2017-10-13. ######################     
    def power_cal(self, flow_no, node_no, input_port, output_port, _lambda, signal_power, noise_power):
        _nlambda = int(_lambda, 16)
        wavelength = _nlambda - 1
        switch_to_port_old = copy.deepcopy(self.switch_to_ports)

        # Set input power and noise at this node        
        self.switch_to_ports[node_no][input_port][0][wavelength] = signal_power
        self.switch_to_ports[node_no][input_port][1][wavelength] = noise_power

        # Give time for structures to update
        sleep(0.01)

        # print(wavelength)
        # print(self.switch_to_ports[node_no][input_port][0][wavelength])
        # print(switch_to_port_old[node_no][input_port][0][wavelength])
            
        next_node_queue = Queue.Queue()
        next_node_queue.put(node_no)
        
        while not next_node_queue.empty():
            print("Entered power_cal for node: %s", str(node_no))
            current_node = next_node_queue.get()
            flow_id = 0
            # recalculate output powers according to input power changes
            flag_need_recalculation = False
            # For each port in the current node
            for key_port in self.switch_to_ports[current_node].keys():
                # For each input_port (odd number) AND
                # if the values of the new and old structure (switch_to_ports) is different
                if(key_port % 2 is not 0) and ((self.switch_to_ports[current_node][key_port][0] == switch_to_port_old[current_node][key_port][0]) is not True):
                    flag_need_recalculation = True
                    wavelength_no = len(self.switch_to_ports[current_node][key_port][0])
                    # For each channel in the port (loaded and unloaded)
                    for key_wave in range(0,wavelength_no):
                        value_wave = self.switch_to_ports[current_node][key_port][0][key_wave]
                        # If the power values of the new and old structure are different
                        if value_wave is not switch_to_port_old[current_node][key_port][0][key_wave]: # ???? this should ONLY enter for the new /NOT considered channel
                            # for each flow in the registered paths
                            for flow in self.paths: # This would enter for EVERY flow - this is an ERROR
                                # Entering for each flow, except 0
                                if flow is not 0:
                                    flow_struct = self.paths[flow]
                                    # for each hop (node)
                                    for flow_node in flow_struct:
                                        # If flow-node is current node AND
                                        # output_port is the current port
                                        if (flow_node[0] == current_node) and (flow_node[1] == key_port): # In a linear topology, this will always enter
                                            input_power = value_wave
                                            input_noise = self.switch_to_ports[current_node][key_port][1][key_wave]
                                            # if this is not an empty channel
                                            if((input_power == 0 and input_noise == 0) is not True):
                                                out_port = flow_node[2]
                                                out_signal, out_noise = self.estimate_output_power_noise(current_node, input_power, input_noise, key_wave, flow, out_port)
                                                print("power_cal, out_signal: ", out_signal)
                                                # Update structure switch_to_ports
                                                self.switch_to_ports[current_node][out_port][0][key_wave] = out_signal
                                                self.switch_to_ports[current_node][out_port][1][key_wave] = out_noise
                                                switch_to_port_old[current_node][key_port][0][key_wave] = input_power
                                                switch_to_port_old[current_node][key_port][1][key_wave] = input_noise
                                                flow_id = flow
                                                break
            if flag_need_recalculation == False:
                continue            
                
            # nomarlize output powers
            # For each port in the current node
            for key_port in self.switch_to_ports[current_node].keys():
                # if the values of the new and old structure (switch_to_ports) is different
                if (key_port % 2 == 0) and ((self.switch_to_ports[current_node][key_port][0] == switch_to_port_old[current_node][key_port][0]) is not True):
                    current_gain = 0
                    count_wave = 0
                    wavelength_no = len(self.switch_to_ports[current_node][key_port][0])
                    # For each channel in the port (loaded and unloaded)
                    for key_wave in range(0,wavelength_no):
                        value_wave = self.switch_to_ports[current_node][key_port][0][key_wave]
                        if abs(value_wave - 0) > 0:
                            # Should ripple function value consider the number of EDFAs? yes
                            ripple_function_value = self.get_ripple_function_mean(current_node, key_wave, flow_id) # the ripple mean is WRONG - this is an ERROR
                            current_gain = current_gain + ripple_function_value
                            count_wave = count_wave + 1
                    if current_gain is not 0:
                        current_gain = current_gain/float(count_wave)
                    else:
                        current_gain = 1
                    # Update structure switch_to_ports
                    self.switch_to_ports[current_node][key_port][0] = [x/float(current_gain) for x in self.switch_to_ports[current_node][key_port][0]]
                    self.switch_to_ports[current_node][key_port][1] = [x/float(current_gain) for x in self.switch_to_ports[current_node][key_port][1]]

            # calculate excursion and propogate power changes
            # For each port in the current node
            for key_port in self.switch_to_ports[current_node].keys():
                # if the values of the new and old structure (switch_to_ports) is different
                if (key_port % 2 == 0) and ((self.switch_to_ports[current_node][key_port][0] == switch_to_port_old[current_node][key_port][0]) is not True):
                    # Note: To modify to handle absolute values
                    # Update structure switch_to_ports
                    total_power = list(map(lambda x: x[0]*x[1]+x[0], zip(self.switch_to_ports[current_node][key_port][0], self.switch_to_ports[current_node][key_port][1])))
                    total_power_old = list(map(lambda x: x[0]*x[1]+x[0], zip(switch_to_port_old[current_node][key_port][0], switch_to_port_old[current_node][key_port][1])))
                    excursion = max(list(map(lambda x: abs(x[0]-x[1]), zip(total_power, total_power_old))))
                    switch_to_port_old[current_node][key_port][0] = copy.deepcopy(self.switch_to_ports[current_node][key_port][0])
                    switch_to_port_old[current_node][key_port][1] = copy.deepcopy(self.switch_to_ports[current_node][key_port][1])
                    if excursion < PROP_TH:
                        pass
                    else:
                        flag_prop = False
                        flow_id = 0 # For get_switch_to_ports_power_noise_excursion management
                        # for each flow in the registered paths
                        for flow in self.paths:
                            # for each flow in paths, except 0
                            if flow is not 0:
                                if not flag_prop:
                                    flow_struct = self.paths[flow]
                                    key_node = -1
                                    for flow_node in flow_struct:
                                        key_node = key_node + 1
                                        if (flow_node[0] == current_node) and (flow_node[2] == key_port) and (self.is_last_node_in_path(current_node, flow) is not True):
                                            next_node = flow_struct[key_node+1][0]
                                            next_input_port = flow_struct[key_node+1][1]
                                            flag_prop = True
                                            flow_id = flow
                                            break
                        if flag_prop:
                            wavelength_no = len(self.switch_to_ports[current_node][key_port][0])
                            for key in range(0,wavelength_no):
                                input_power, input_noise = self.get_switch_to_ports_power_noise_excursion(current_node, key_port, key, flow_id)
                                if((input_power == 0 and input_noise == 0) is not True):
                                    self.update_fiber_loss(1e-10)
                                    self.update_wss_loss(20) # Assumming next intermediate nodes
                                    sleep(0.01)
                                    in_signal, in_noise = self.estimate_input_power_noise(input_power, input_noise, True)
                                    self.switch_to_ports[next_node][next_input_port][0][key] = in_signal
                                    self.switch_to_ports[next_node][next_input_port][1][key] = in_noise
                            if (next_node_queue.empty()):
                            #if next_node not in next_node_queue: THIS LINE DOES NOT WORK
                                next_node_queue.put(next_node)
        
        return self.switch_to_ports[node_no][output_port][0][wavelength], self.switch_to_ports[node_no][output_port][1][wavelength]
    ############### Attention! Added by Yao, 2017-10-13. End ###################### 

    def get_ripple_function_mean(self, node_id, _lambda, flow_id):
        try:
            if self.is_last_node_in_path(node_id, flow_id) is not True:
                dst_node = self.get_next_node(flow_id, node_id)
                link_ID = self.links.get_link_ID(node_id, dst_node)
                mean_amplifier_attenuation = self.amplifier_attenuation.get_mean_amplifier_attenuation(link_ID, _lambda)
                return mean_amplifier_attenuation
            else:
                return 0
        except:
            print('Err: get_ripple_function_mean: unable to retrieve ripple function.')
            return 0

    def get_switch_to_ports_power_noise_excursion(self, node_id, port, _lambda, flow_id):
        if (port == 0) and (node_id == 0):
            # Starting power in 0dB and 
            # noise as low as -100dB.
            # Absolute values representation.
            power = TARGET_POWER
            noise = IN_NOISE
            self.abs_fiber_loss = self.dB_to_abs(1e-10)  # constant
            # Converting 18dB loss (Two WSS)
            self.abs_WSS_loss = self.dB_to_abs(20) # constant
            sleep(0.01)
            return power, noise
        elif (port == 15) and (node_id == 255):
            # Inter-domain node
            # Establish connection to neighbour agent.
            power, noise = self.inter_domain_client_connection(flow_id, _lambda)
            # Converting 0.2dB loss, and multiplying
            # for 0km.
            # Should be converted to last link span
            self.abs_fiber_loss = self.dB_to_abs(1e-10)
            # # Converting 18dB loss (Two WSS)
            self.abs_WSS_loss = self.dB_to_abs(20)
            return power, noise
        elif(self.is_last_node_in_path(node_id, flow_id)):
            logging.debug('get_switch_to_ports_power_noise: datapath: %s is last node in path.', str(node_id))
            try:
                power = self.switch_to_ports[node_id][port][0][_lambda]
                noise = self.switch_to_ports[node_id][port][1][_lambda]
                # Should be converted to last link span
                #self.update_in_fiber_loss(flow_id, node_id)
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                # Converting 18dB loss (Two WSS)
                self.abs_WSS_loss = self.dB_to_abs(9)
                #sleep(0.01)
                return power, noise
            except:
                logging.info('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                print('Err: get_switch_to_ports_power_noise: unable to retrieve power/noise. Last node.')
                return 0, 0
        else:
            try:
                power = self.switch_to_ports[node_id][port][0][_lambda]
                noise = self.switch_to_ports[node_id][port][1][_lambda]
                # Should be converted to last link span
                #self.update_in_fiber_loss(flow_id, node_id)
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                self.abs_WSS_loss = self.dB_to_abs(20) # constant
                sleep(0.01)
                return power, noise
            except:
                logging.info('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                print('Err: get_switch_to_ports_power_noise: unable to retrieve power/noise. Intermediate node.')
                return 0, 0

    # Note: To be removed
    def update_in_fiber_loss(self, flow_id, src_node):
        try:
            if self.is_first_node_in_path(src_node, flow_id):
                self.abs_fiber_loss = self.dB_to_abs(0)
            else:
                prev_node = self.get_prev_node(flow_id, src_node)
                last_span = self.get_last_span_length(src_node, prev_node)
                self.abs_fiber_loss = self.dB_to_abs(0.2*last_span)
            sleep(0.01)
        except:
            print('Err: update_in_fiber_loss. Unable to update in_fiber_loss')

    def update_wss_loss(self, loss):
        try:
            self.abs_WSS_loss = self.dB_to_abs(loss)
        except:
            print('Err: update_wss_loss. Unable to update wss_loss.')

    def update_fiber_loss(self, span):
        try:
            self.abs_fiber_loss = self.dB_to_abs(0.2*span)
        except:
            print('Err: update_fiber_loss. Unable to update out_fiber_loss')

    def get_last_span_length(self, EDFA_NO, link_distance):
        try:
            last_span = link_distance - (100*(EDFA_NO-2))
            return last_span
        except:
            print('Err: get_last_span_length. Unable to compute last span length.')
            return 1

    def get_next_node(self, flow_id, datapath_id):
        try:
            if flow_id in self.paths:
                flow = self.paths[flow_id]
                NEXT_NODE_FLAG = False
                for _tuple in flow:
                    if NEXT_NODE_FLAG == True:
                        return _tuple[0]
                    if _tuple[0] == datapath_id:
                        NEXT_NODE_FLAG = True
        except:
            print('Err: get_next_node. Unable to compute next node in path.')
            return -1

    def get_prev_node(self, flow_id, src_node):
        try:
            if flow_id in self.paths:
                flow = self.paths[flow_id]
                for _tuple in flow:
                    if _tuple[0] == src_node:
                        return prev_node                
        except:
            print('Err: get_prev_node. Unable to compute prev node in path.')
            return -1
