# South Bound Interface
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
import event_config
import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-TCD-d2')
from database import database_management as dbm
from mymininet import remote_mininet_client as rmc
from thread import *
import threading
exec_lock = threading.Lock()

class SouthBoundInterface(app_manager.RyuApp):
    
    _EVENTS = [event_config.LightpathCancelEvent]
    
    def __init__(self, *args, **kwargs):
        super(SouthBoundInterface, self).__init__(*args, **kwargs)
        self.node_to_datapath = {}
        self.dbm = dbm.DatabaseManagement()
        
    # input: datapath, tx_node, in_port, out_port, channel, lightpath_id
    #            (openflow_format, int, int, int, int, int)
    # output: send OpenFlow instruction to device/switch.
    def add_flow(self, datapath, tx_node, in_port, out_port, channel, lightpath_id):
        mod = datapath.ofproto_parser.OFPTSetupConfigWSSRequest(
                    datapath,
                    datapath_id=tx_node,
                    message_id= 0,
                    ITU_standards= 0, 
                    node_id= tx_node,
                    input_port_id = in_port,
                    output_port_id = out_port,
                    start_channel=channel,
                    end_channel= 0,
                    experiment1= lightpath_id,
                    experiment2=0)
        datapath.send_msg(mod)
        
    # input: EventOFPSwitchFeatures
    # output: hash-table for devices/switches and their
    # connection stream to the controller.
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures)
    def handle_device_connection(self, ev):
        device_features = ev.msg
        datapath = device_features.datapath
        datapath.id = device_features.datapath_id
        self.node_to_datapath[int(datapath.id)] = datapath
        #print("SouthBoundInterface: device_features: %s" %device_features)
        
    # input: tx_node, sequence, out_port (int, int, int)
    # output: input port for each devices/switches
    # except the last one in a path.
    def get_in_port(self, tx_node, sequence, out_port):
        if sequence == 1:
            in_port = 1 # TX
        else:
            in_port = out_port - 1
        return in_port
        
    # input: RouteAddEvent
    # output: build an OpenFlow instruction to set
    # the lightpaths in the devices/switches.
    @set_ev_cls(event_config.RouteAddEvent)
    def build_ofp_lightpath_setup(self, ev):
        lightpath_id = ev.lightpath_id
        sequence = ev.sequence
        link_id = ev.link_id
        channel = ev.channel
        last_node_in_sequence = ev.last_node_in_sequence
        
        try:
            link = self.dbm.l_handle_get_link_with_id(link_id) # Retrieve from database
            
            tx_node = link[1]
            out_port = link[2]
            in_port = self.get_in_port(tx_node, sequence, out_port)
            datapath = self.node_to_datapath[tx_node]
                        
            self.add_flow(datapath, tx_node, in_port, out_port, channel, lightpath_id)
                        
            if last_node_in_sequence:
                tx_node = link[3]
                out_port = self.dbm.n_handle_get_rx_port(tx_node)
                in_port = link[4]
                datapath = self.node_to_datapath[tx_node]
                self.add_flow(datapath, tx_node, in_port, out_port, channel, lightpath_id)
        except:
            lightpath_cancel_event = event_config.LightpathCancelEvent()
            lightpath_cancel_event.lightpath_id = lightpath_id
            self.send_event("DatabaseManagement", lightpath_cancel_event)
            
    # functional method of threaded function:
    # call_remote_mininet_server(self, ev) below.
    def threaded(self,  ev):
        lightpath_id, channel = ev.lightpath_id, ev.channel
        try:
            nodes = self.dbm.lp_get_nodes(lightpath_id)
            tx_node, rx_node = nodes[0], nodes[1]
            rmc.main(lightpath_id, tx_node, rx_node, hex(channel))
            exec_lock.release()
        except:
            lightpath_cancel_event = event_config.LightpathCancelEvent()
            lightpath_cancel_event.lightpath_id = lightpath_id
            self.send_event("DatabaseManagement", lightpath_cancel_event)
        
    # input: RemoteMininetClientEvent
    # output: call to the remote mininet server, in order to
    # run the network emulation on the virtual hosts.
    @set_ev_cls(event_config.RemoteMininetClientEvent)
    def call_remote_mininet_server(self, ev):
        exec_lock.acquire()
        start_new_thread(self.threaded, (ev,))
