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
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

# For Control Plane management
import socket
import sys
import logging
import thread
import struct
from struct import calcsize
import scipy.constants as sc

from cProfile import Profile 
from pstats import Stats 

log_level = 'DEBUG' #Set log level
if log_level == 'INFO':
    logging.basicConfig(level=logging.INFO)
if log_level == 'DEBUG':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

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

node_to_ports='/home/alan/bk_sep_29_2017/ArizonaEx/single_domain/topology_discovery/node_to_ports'
ripple_function_file='/home/alan/bk_sep_29_2017/ArizonaEx/single_domain/ryu_optical_agent/ripple_function_dB.txt'


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
                                         # purposes.
        self.ripple_function = self.init_ripple_function()

        self.osnr_list = [] # for debugging purposes

        # Converting 0.2dB loss, and multiplying
        # for 60km.
        self.abs_fiber_loss = 10**((0.2*60)/10)  # constant
        # Converting 6dB loss
        self.abs_WSS_loss = 10**(6/float(10)) # constant


        self.packet_in_counter = 0
        self.packet_in_trigger = 3
        self.pr = Profile()
        self.pr.enable()

    def init_ripple_function(self):
        # Read file
        data = open(ripple_function_file)
        data_dB = [x.strip() for x in data.readlines()]
        data_abs = [10**(float(value)/10) for value in data_dB]
        return data_abs

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
        logging.debug('switch_features_handler: datapath.id: %s', str(datapath.id))
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
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
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

    # Function used for emulation purposes. Removes the OpenFlow (original)
    # instructions into the real switches.
    def delete_flow(self, datapath, outport, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath,
                                command=ofproto.OFPFC_DELETE,
                                out_port=outport,
                                out_group=ofproto.OFPG_ANY,
                                match=match)
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
        in_port = msg.match['in_port']

        try:
            ipv6_flabel = msg.match['ipv6_flabel']
            flow_id = msg.match['vlan_vid']

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
                _slambda = "0x" + "0" + _lambda
                previous_out_port = hex_ipv6_flabel[3:4]
                previous_hop = hex_ipv6_flabel[4:6]
            else:
                _lambda = hex_ipv6_flabel[2:4]
                _slambda = "0x" + _lambda
                previous_out_port = hex_ipv6_flabel[4:5]
                previous_hop = hex_ipv6_flabel[5:7]

            power, noise = self.get_switch_to_ports_power_noise(datapath.id, previous_hop, previous_out_port, _lambda, flow_id)

            # Assuming usage of VLAN tag to identify
            # the different flows.
            out_port = self.get_out_port(flow_id, datapath.id)

            # Estimate input power excursion
            input_power, input_noise = self.estimate_input_power_noise(power, noise)
            self.update_switch_to_ports_power_noise(datapath.id, in_port, _lambda, input_power, input_noise)

            # Estimate output power excursion
            output_power, output_noise = self.estimate_output_power_noise(input_power, input_noise, _lambda)
            self.update_switch_to_ports_power_noise(datapath.id, out_port, _lambda, output_power, output_noise)

            # Onlyh for debugging purposes.
            #if (out_port%2 == 0): USEFUL IN LINEAR TESTS
            logging.debug('_packet_in_handler: OSNR at port: %s in datapath: %s', str(out_port), str(datapath.id))
            osnr = output_power / output_noise
            print(osnr)
            self.osnr_list.append(osnr)
            print(self.osnr_list)

            # Packet processing for sending OpenFlow Message.

            ipv6_flabel_mod = self.build_ipv6_flabel(_lambda, datapath.id, out_port)

            actions = [parser.OFPActionSetField(ipv6_flabel=ipv6_flabel_mod),
                       parser.OFPActionOutput(out_port)]

            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions)

            # Install rule to avoid this processing next time
            match = parser.OFPMatch(in_port=in_port, eth_type=0x86dd, vlan_vid=flow_id, ipv6_flabel=ipv6_flabel)
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
            else:
                self.add_flow(datapath, 1, match, actions)


            datapath.send_msg(out)

            # Update flow_to_datapath_match structure for further deleiton purposes.
            self.update_flow_to_datapath_match(flow_id, datapath.id, match, out_port)

            #self.print_switch_to_ports()
            logging.debug('_packet_in_handler: Flow rule installed successfully.')
            logging.debug('_packet_in_handler: Packet routed successfully.')
            self.packet_in_counter += 1
            if(self.packet_in_counter >= self.packet_in_trigger):
                logging.debug('_packet_in_handler: Profiling...')
                self.pr.disable()
                self.pr.dump_stats('oagent_profile.stats')
                with open('oagent_profile.txt', 'wt') as output:
                    stats = Stats('oagent_profile.stats', stream=output)
                    stats.sort_stats('cumulative', 'time')
                    stats.print_stats()
            logging.info('----------------------------------------------------------------------')
            
        except:
            return
            #logging.debug("_packet_in_handler: Unable to route packet.")

    def get_switch_to_ports_power_noise(self, datapath_id, previous_hop, previous_out_port, _lambda, flow_id):
        n_previous_hop = int(previous_hop, 16)
        n_previous_out_port = int(previous_out_port, 16)
        n_lambda = int(_lambda, 16)
        if (n_previous_out_port == 0) and (n_previous_hop == 0):
            # Starting power in 0dB and 
            # noise as low as -100dB.
            # Absolute values representation.
            power = 1
            noise = 1e-10
            # Converting 0.2dB loss, and multiplying
            # for 0km.
            self.abs_fiber_loss = 10**((0.2*0)/10)  # constant
            # Converting 12dB loss (Two WSS)
            self.abs_WSS_loss = 10**(12/float(10)) # constant
            return power, noise
        elif(self.is_last_node_in_path(datapath_id, flow_id)):
            logging.debug('get_switch_to_ports_power_noise: datapath: %s is last node in path.', str(datapath_id))
            try:
                power = self.switch_to_ports[n_previous_hop][n_previous_out_port][0][n_lambda-1]
                noise = self.switch_to_ports[n_previous_hop][n_previous_out_port][1][n_lambda-1]
                # Converting 0.2dB loss, and multiplying
                # for 60km.
                self.abs_fiber_loss = 10**((0.2*60)/10)  # constant
                # Converting 12dB loss (Two WSS)
                self.abs_WSS_loss = 10**(6/float(10)) # constant
                return power, noise
            except:
                logging.debug('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                return 0, 0
        else:
            try:
                power = self.switch_to_ports[n_previous_hop][n_previous_out_port][0][n_lambda-1]
                noise = self.switch_to_ports[n_previous_hop][n_previous_out_port][1][n_lambda-1]
                # Converting 0.2dB loss, and multiplying
                # for 60km.
                self.abs_fiber_loss = 10**((0.2*60)/10)  # constant
                # Converting 12dB loss (Two WSS)
                self.abs_WSS_loss = 10**(12/float(10)) # constant
                return power, noise
            except:
                logging.debug('get_switch_to_ports_power_noise: unable to retrieve power/noise.')
                return 0, 0

    # Twin function of inter_domain_is_edge_node
    def is_last_node_in_path(self, datapath_id, flow_id):
        logging.debug('is_last_node_in_path: verifying...')
        i = len(self.paths[flow_id])
        last_node = self.paths[flow_id][i-1][0]
        print(self.paths[flow_id])
        logging.debug('is_last_node_in_path: last_node:')
        print(last_node)
        logging.debug('is_last_node_in_path: datapath_id:')
        print(datapath_id)
        if(datapath_id == last_node):
            return True
        return False

    def update_flow_to_datapath_match(self, flow_id, datapath_id, match, out_port):
        try:
            if flow_id not in self.flow_to_datapath_match:
                self.flow_to_datapath_match[flow_id] = {}
            self.flow_to_datapath_match[flow_id][datapath_id] = (match, out_port)
        except:
            logging.debug("update_flow_to_datapath_match: Unable to update flow_to_datapath_match structure.")

    # Note: to be modified.
    def not_valid_flow(self, flow_id, datapath_id, ipv6_flabel):
        f_ipv6_flabel_datapath = self.flow_to_ipv6_flabel[flow_id][0]
        if (datapath_id != f_ipv6_flabel_datapath):
            logging.debug('not_valid_flow: Not primary datapath')
            return -1
        else:
            f_ipv6_flabel = self.flow_to_ipv6_flabel[flow_id][1]
            if(f_ipv6_flabel != ipv6_flabel):
                return 0
            return -1

    def build_str_out_port_power(self, out_port_power):
        if(len(out_port_power) < 5):
                sout_port_power = "0" + out_port_power[2:4]
        else:
            sout_port_power = out_port_power[2:5]
        return sout_port_power

    def build_ipv6_flabel(self, _lambda, datapath, out_port):
        s_datapath = str(datapath)
        if(len(_lambda) < 2):
            _lambda = "0" + _lambda
        if(len(s_datapath) < 2):
            s_datapath = "0" + s_datapath
        elif(len(s_datapath) == 2):
            s_datapath = self.get_hex_number(datapath)

        sipv6_flabel = "0x" + _lambda + str(out_port) + s_datapath
        hex_ipv6_flabel = int(sipv6_flabel, 16)
        return hex_ipv6_flabel

    def get_hex_number(self, datapath):
        hex_no = hex(datapath)
        str_no = str(hex_no)
        letter = str_no[2:]
        return "00" + letter

    def get_out_port(self, flow_id, datapath_id):
        if flow_id in self.paths:
            flow = self.paths[flow_id]
            for _tuple in flow:
                if _tuple[0] == datapath_id:
                    return _tuple[2]
            return -1
        return -1

    def estimate_input_power_noise(self, in_signal_power, noise):
        # Converting 0.2dB loss, and multiplying
        # for 60km.
        abs_fiber_loss = 10**((0.2*60)/10)  # constant
        # Converting 6dB loss
        abs_WSS_loss = 10**(6/float(10)) # constant

        in_power = (in_signal_power / abs_fiber_loss / abs_WSS_loss)
        in_noise = (noise / abs_fiber_loss / abs_WSS_loss)
        return in_power, in_noise

    def estimate_output_power_noise(self, input_power, input_noise, _lambda):
        # Beware the hex format of the parameters
        n_lambda = int(_lambda, 16)
        sys_gain = self._ripple_function(n_lambda)

        out_power = input_power * sys_gain
        out_noise = self.calculate_out_noise(input_noise, n_lambda, sys_gain)

        return out_power, out_noise

    def _ripple_function(self, _lambda):
        # Converting 0.2dB loss, and multiplying
        # for 80km.
        _abs_fiber_loss = (10**(0.2*60/10))  # constant
        # Converting 6dB loss
        _abs_WSS_loss = 10**(6/float(10)) # constant
        try:
            ripple_lambda = self.ripple_function[_lambda - 1]

            target_gain = _abs_fiber_loss * _abs_WSS_loss

            sys_gain = ripple_lambda * target_gain

            return sys_gain
        except:
            return 1

    def calculate_out_noise(self, input_noise, n_lambda, sys_gain):
        planck_const = sc.h # 6.62607004e-34

        speed_of_light = sc.speed_of_light # 299792458.0

        c_band_lambda = (1549+n_lambda)*(10**-9) # m

        noise_figure = 10**(6/float(10))

        bandwidth = 12.5*(10**9) # Considering 50GHz bandwidth

        watt_to_mwatt = 1000

        out_noise = ((input_noise * sys_gain) + ((planck_const*(speed_of_light/c_band_lambda)) * watt_to_mwatt * sys_gain * noise_figure * bandwidth))
        return out_noise

    def update_switch_to_ports_power_noise(self, switch, port, _lambda, power, noise):
        _nlambda = int(_lambda, 16)
        _lambda_index = _nlambda - 1
        try:
            self.switch_to_ports[switch][port][0][_lambda_index] = power
            self.switch_to_ports[switch][port][1][_lambda_index] = noise
            logging.debug('update_switch_to_ports_power_noise: UPDATE successful.')
        except:
            logging.debug('update_switch_to_ports_power_noise: UPDATE failed.')
        

    def update_switch_to_ports_noise(self, switch, port, _lambda, noise):
        _nlambda = int(_lambda, 16)
        _lambda_index = _nlambda - 1
        try:
            self.switch_to_ports[switch][port][1][_lambda_index] = noise
            logging.debug('update_switch_to_ports_noise: UPDATE successfull.')
        except:
            logging.debug('update_switch_to_ports_noise: UPDATE failed.')


    def str_output_power(self, output_power):
        hex_output_power = hex(output_power)
        if(len(hex_output_power) < 5):
            soutput_power = "0" + hex_output_power[2:4]
        else:
            soutput_power = hex_output_power[2:5]
        return soutput_power

    # The lambda-availability can be retrievid from the in_port(s) of
    # each switch. Hence, this function checks for ANY unused lambda.
    # Returns a list with the available lambdas (position-based).
    # Note: for simplicity, the checks could be done ONLY for the
    # first switch in the communication path.
    def check_lambdas_avail(self, switch):
        avail_lambdas = []
        switch_to_port = self.switch_to_ports[switch]
        port = switch_to_port[1] # Should always be Port 1 for
                                 # this Increment (7).
        _lambdas = port[0]
        lambda_pos = 0
        for _lambda in _lambdas:
            if _lambda == 0:
                avail_lambdas.append(lambda_pos)
            lambda_pos += 1

        if avail_lambdas == []:
            return -1
        else:
            return avail_lambdas


    # Check for lambda availability in switch, and return
    # first available found.
    def get_avail_lambda(self, switch):
        avail_lambdas = self.check_lambdas_avail(switch)
        if avail_lambdas != -1:
            return avail_lambdas[0]
        return -1


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
        for port in range(1,ports_number):
            # First position: Power values
            # Second position: noise values
            _struct_a = [0.0] * 24
            _struct_b = [0.0] * 24
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


    # For debugging Optical Structures
    def print_switch_to_ports(self):
        for switch in self.switch_to_ports:
            print(self.switch_to_ports[switch])

    def print_port_to_lambda(self, switch):
        ports = self.switch_to_ports[switch]
        for port in ports:
            lambda_OSNR = ports[port]
            print(lambda_OSNR[0])


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
        
        controller_address = ("localhost", 6666)
        
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
                original_data = data
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
                elif self.ofp_belong_to(data) == 'FLOW_MOD':
                    logging.info('Received FLOW_MOD')
                    try:
                        self._ofp_flow_mod_handler(data, sock)
                    except:
                        logging.info('Failed to handle FLOW_MOD request.')
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
                    logging.info('O T H E R')
                    #self.print_bytearray(data)
                    logging.info('---------------------------------------')

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
        # Add hop-information to the flows (paths) structure.
        flow_data = (datapath_id, input_port_id, output_port_id)
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

        datapath = self.switches[datapath_id]
        parser = datapath.ofproto_parser

        # Retrieve flow ID (experiment 1)
        flow_id = experiment1
        if flow_id not in self.paths:
            logging.debug('ofp_teardown_config_wss_request_handler: Non-existent flow.')
            raise
        try:
            match = self.flow_to_datapath_match[flow_id][datapath_id][0]
            self.delete_flow(datapath, output_port_id, match)
            if(datapath_id == end_channel):
                self.remove_flow(flow_id)
            logging.debug('ofp_teardown_config_wss_request_handler: Successfully removed the flow.')
            return 0
        except:
            logging.debug('ofp_teardown_config_wss_request_handler: Failed to remove the flow.')
            return 1

    def remove_flow(self, flow_id):
        try:
            self.paths.pop(flow_id, None)
            self.flow_to_ipv6_flabel.pop(flow_id, None)
            self.flow_to_datapath_match.pop(flow_id, None)
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
        (datapath_id,
        message_id,
        ITU_standards,
        node_id,
        port_id,
        start_channel,
        end_channel)=struct.unpack(WSS_TEARDOWN_REQUEST_STR,data[8:])

        power_values = self.switch_to_ports[datapath_id][port_id][0]
        noise_values = self.switch_to_ports[datapath_id][port_id][1]
        osnr = {}
        i = 0


        try:
            result = 0
            while (i<len(power_values)):
                if(power_values[i] == 0 or noise_values[i] == 0):
                    osnr[i] = 0
                else:
                    osnr[i] = power_values[i]/noise_values[i]
                i = i + 1

            result = 0
            min_osnr = min(osnr.values())
            return min_osnr, result
        except:
            result = result | 1
            return -1, 1

    def ofp_get_osnr_reply_handler(self, sock, data, result, osnr):

        (datapath_id,
        message_id)=struct.unpack('!QI',data[8:20])

        GET_OSNR_REPLY_BODY = struct.pack(GET_OSNR_REPLY_STR,datapath_id,message_id,datapath_id,result,osnr)
        GET_OSNR_REPLY = ''.join([GET_OSNR_REPLY_HEADER,GET_OSNR_REPLY_BODY])

        try:
            assert len(GET_OSNR_REPLY) == 32
        except AssertionError as e:
            logging.critical(e)
            logging.critical('GET_OSNR_REPLY is not in a correct format')
            for device in NODETOCONNECTION.values():
                device.close()
            sys.exit()
        self.sock.sendall(GET_OSNR_REPLY)
        logging.info('GET_OSNR_REPLY Sent to RYU')

    # An OpenFlow FlowMod message is given (data). From this byte structre
    # the OFPMatch(in_port) and OFPActionOutput(out_port) structures are
    # retrieved for subsequent virtual mapping to the (Optical) Flow Tables.
    # Note: Although the conversion and management of OF-electronic packets
    # is done well, this is not completely relevant, and to forward messages
    # we're gonna be using the WSS_SETUP_REQUEST OF-extension messages.
    # Note 2: This method is to be used for creating the ActionOutput including
    # the power and wavelength-assignment parameters in the tags supported
    # by the OpenFlow virtual Switch (i.e. IPv6 Flow Label)
    def _ofp_flow_mod_handler(self, data, sock):
        switch = self.socket_to_phy_conn[sock]
        datapath = self.switches[switch]
        
        #ofp_header_format = 'BBHI'
        #ofp_flow_mod_format = 'QQBBHHHIIIH2x'
        ofp_action_output = '!HHIH6x'
        #ofp_match_format = 'HHBBBB'

        # Retrieve the Match OF Object.
        # Match: in_port
        # Note: The current acquisition is hard-coded, and requires
        # optimization.
        ofp_match_byte_struct = data[-32:]
        ofp_match_byte_struct_in_port = ofp_match_byte_struct[0:4]
        [in_port, ] = struct.unpack('!I', ofp_match_byte_struct_in_port)

        # Retrieve the ActionOutput OF object.
        # Action: out_port
        ofp_action_output_byte_struct = data[-16:]
        [_type, _len, out_port, max_len] = struct.unpack(
                                ofp_action_output, ofp_action_output_byte_struct)

        # Fill in Virtual (Optical) Mapping
        self.add_optical_flow(switch, in_port, out_port)

        # For the real emulation
        parser = datapath.ofproto_parser

        # Routing action: forwarding to designated out_port
        actions = [parser.OFPActionOutput(out_port)]
        # match = parser.OFPMatch(in_port=in_port) # original
        # ipv6_flable = 2 Bytes lambda, 2 Bytes power
        # i.e. A0 - 32 = lambda 160, at -30 dBm

        ipv6_src_h1=('fe80::200:ff:fe00:100')
        ipv6_src_h3=('fe80::200:ff:fe00:300')
                       #'ffff:ffff:ffff:ffff::')
        match = parser.OFPMatch(    in_port=in_port,
                                    eth_type=0x86dd,
                                    ipv6_src=ipv6_src_h1,
                                    ipv6_flabel=0x00002)
        self.add_flow(datapath, 1, match, actions)

        actions = [parser.OFPActionOutput(in_port)]
        match = parser.OFPMatch(    in_port=out_port,
                                    eth_type=0x86dd,
                                    ipv6_src=ipv6_src_h3,
                                    ipv6_flabel=0x00002)
        self.add_flow(datapath, 1, match, actions)

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
        pad = 0
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
        elif data[1] == 14: # Flow Mod
            return "FLOW_MOD"
        elif data[1] == 116:
            return "WSS_SETUP_REQUEST"
        elif data[1] == 118:
            return "WSS_TEARDOWN_REQUEST"
        elif data[1] == 120:
            return "GET_OSNR_REQUEST"

    # For debugging purposes
    def print_bytearray(self, data):
        x = len(data)
        for i in range(0,x):
            print(data[i])
