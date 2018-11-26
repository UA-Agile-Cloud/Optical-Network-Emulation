from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
import mysql.connector
import db_config
import event_config
import database_procedures as dbp
import time
import datetime
from thread import *
import threading
exec_lock = threading.Lock()
link_to_channel_lock = threading.Lock()

class DatabaseManagement(app_manager.RyuApp):
    
    _EVENTS = [event_config.LightpathActivateEvent, 
                        event_config.RemoteMininetClientEvent,
                        event_config.LightpathCancelEvent]
    
    def __init__(self, *args, **kwargs):
        super(DatabaseManagement, self).__init__(*args, **kwargs)
        self.node_manager = self.NodeManagement()
        self.link_manager = self.LinkManagement()
        self.traffic_manager = self.TrafficManagement()
        
    # input: none
    # output: node count (int)
    def n_handle_count_nodes(self):
        node_no = self.node_manager.count_node_all()
        return node_no
        
    # input: none
    # output: nodes (list)
    def n_handle_get_all_nodes(self):
        nodes = self.node_manager.select_node_all()
        return nodes
        
    # input: none
    # output: port_id
    def n_handle_get_rx_port(self, node_id):
        port_id = self.node_manager.select_rx_port_id((node_id, ))
        return port_id
        
    # input: rx_node_rx_node (int, int)
    # output: link_id (int) that connects these nodes
    def l_handle_get_link_id(self,  tx_node,  rx_node):
        link_id = self.link_manager.select_link_id_with_nodes((tx_node,  rx_node))
        return link_id
        
    # input: link_id (int)
    # output: link (tuple)
    def l_handle_get_link_with_id(self, link_id):
        link = self.link_manager.select_link_with_id((link_id, ))
        return link
        
    # input: none
    # output: links (list)
    def l_handle_get_all_links(self):
        links = self.link_manager.select_link_all()
        return links
        
    # input: link_id (int)
    # output: available_channels (list)
    def l_handle_get_available_channels(self, link_id):
        available_channels = self.link_manager.select_available_channels((link_id, ))
        return available_channels
        
    def lp_get_nodes(self, lightpath_id):
        nodes = self.traffic_manager.get_nodes_with_id((lightpath_id, ))
        return nodes
        
    # Event-based traffic-manager method/function
    # In the common flow, raised by a NorthBoundInterface instance:
    #       @handle_create_lightpath(self, req, cmd, **_kwargs)
    # Attempts to create the instance of a lightpath in the database
    # with its default values. Then, it forwards the event to the 
    # PathComputationElement module
    @set_ev_cls(event_config.LightpathCreateEvent)
    def tm_handle_create_lightpath(self, ev):
        lightpath_tuple = [ev.lightpath_id, ev.tx_node,  ev.rx_node]
        if self.traffic_manager.create_lightpath(lightpath_tuple):
            self.send_event('PathComputationElement',  ev)
            
    # Event-based traffic-manager method/function
    # In the common flow, raised by a DatabaseManagement instance:
    #       @tm_handle_add_route(self, ev)
    # Attempts to activate a lightpath in the database (update status)
    @set_ev_cls(event_config.LightpathActivateEvent)
    def tm_handle_activate_lightpath(self, ev):
        ts = time.time()
        start_timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        lightpath_tuple = [ev.status, start_timestamp, ev.lightpath_id]
        if self.traffic_manager.activate_lightpath(lightpath_tuple):
            print("DatabaseManagement: Lightpath %s ACTIVATED" %ev.lightpath_id)
            remote_mininet_client_event = event_config.RemoteMininetClientEvent()
            remote_mininet_client_event.lightpath_id = ev.lightpath_id
            remote_mininet_client_event.channel = ev.channel
            self.send_event("SouthBoundInterface", remote_mininet_client_event)
        
    def th_tm_handle_add_route(self, ev):
        lightpath_id = ev.lightpath_id
        try:
            route_tuple = [ev.lightpath_id, ev.sequence, ev.link_id]
            self.traffic_manager.add_route(route_tuple)
            # Link channel to links and lightpath
            link_to_channel_tuple = (ev.lightpath_id, ev.link_id,  ev.channel)
            self.traffic_manager.update_link_to_channel(link_to_channel_tuple)
            if ev.last_node_in_sequence:
                lightpath_activate_event = event_config.LightpathActivateEvent()
                lightpath_activate_event.lightpath_id = ev.lightpath_id
                lightpath_activate_event.status = 1 # Active Status
                lightpath_activate_event.channel = ev.channel
                self.send_event('DatabaseManagement',  lightpath_activate_event)
                exec_lock.release()
        except:
            lightpath_cancel_event = event_config.LightpathCancelEvent()
            lightpath_cancel_event.lightpath_id = lightpath_id
            self.send_event("DatabaseManagement", lightpath_cancel_event)
            
    # Event-based traffic-manager method/function
    # In the common flow, raised by a RoutingWavelengthAssignment instance:
    #       @route_evaluation(self,  route)
    # Attempts to insert a route into the database, then create an event of
    # the type LightpathActivateEvent and raise it.
    @set_ev_cls(event_config.RouteAddEvent)
    def tm_handle_add_route(self, ev):
        exec_lock.acquire()
        start_new_thread(self.th_tm_handle_add_route, (ev, ))

    @set_ev_cls(event_config.LightpathCancelEvent)
    def tm_handle_cancel_lightpath(self, ev):
        self.traffic_manager.cancel_lightpath((ev.lightpath_id, ))

    class NodeManagement():
        def __init__(self,*args,**kwargs):
            self.db_connection = ''
            self.cursor = ''
        
        def db_connect(self):
            self.db_connection = mysql.connector.connect(**db_config.DB_CONFIG)
            self.cursor = self.db_connection.cursor(buffered=True)
            
        def db_close_connection(self):
            self.cursor.close()
            self.db_connection.close()
            
        # input: node_data (tuple): (node_id, dpid, ports_no, status) - (int, string, int, int)
        # output: successful message of inserted node.
        def add_node(self,  node_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_node, node_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.n_insert_success_message)
            except:
                print(dbp.n_insert_error_message)
                
        def select_node_all(self):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_node_all)
                nodes = self.cursor.fetchall()
                self.db_close_connection()
                #print(dbp.n_select_all_success_message)
                return nodes
            except:
                print(dbp.n_select_all_error_message)
                
        # input node_id (int)
        # output: return data of node with given ID
        def select_node_with_id(self,  node_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_node_with_id,  (node_id, ))
                #print(dbp.n_select_node_with_id_success_message)
                self.db_close_connection()
                return self.cursor
            except:
                print(dbp.n_select_node_with_id_error_message)
                
        # input dpid (int)
        # output: return data of node with given DPID
        def select_node_with_dpid(self,  dpid):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_node_with_dpid,  (dpid, ))
                #print(dbp.n_select_success_message_with_dpid)
                self.db_close_connection()
                return self.cursor
            except:
                print(dbp.n_select_error_message_with_dpid)
                
        # input: node_id (int), new_status (int)
        # output: successful message of updated status in given node.
        def update_node_status(self,  node_id,  new_status):
            try:
                self.db_connect()
                self.cursor.execute(dbp.update_node_status_with_ID,  (new_status,  node_id))
                self.db_connection.commit()
                #print(dbp.n_update_node_status_success_message)
                self.db_close_connection()
            except:
                print(dbp.n_update_node_status_error_message)
                
        # input: none
        # output: number of nodes in database (int)
        def count_node_all(self):
            try:
                self.db_connect()
                self.cursor.execute(dbp.count_node_all)
                node_no = self.cursor.fetchall()[0][0] #cursor returns list of tuples
                self.db_close_connection()
                #print(dbp.n_count_all_success_message)
                return node_no
            except:
                print(dbp.n_count_all_error_message)
                
        # input: node_to_port_data (tuple): (node_id, port_id) - (int, int)
        # output: successful message of inserted node_to_port relation.
        def add_node_to_port(self,  node_to_port_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_node_to_port, node_to_port_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.ntp_insert_success_message)
            except:
                print(dbp.ntp_insert_error_message)
                
        def select_rx_port_id(self, node_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_rx_port_id, node_id)
                self.db_connection.commit()
                port_id = self.cursor.fetchall()[0][0]
                self.db_close_connection()
                #print(dbp.ntp_select_rx_port_id_success_message)
                return port_id
            except:
                print(dbp.ntp_select_rx_port_id_error_message)

    class PortManagement():
        def __init__(self,*args,**kwargs):
            self.db_connection = ''
            self.cursor = ''
        
        def db_connect(self):
            self.db_connection = mysql.connector.connect(**db_config.DB_CONFIG)
            self.cursor = self.db_connection.cursor(buffered=True)
            
        def db_close_connection(self):
            self.cursor.close()
            self.db_connection.close()
            
        # input: port_data (tuple): (port_id, type, description) - (int, int, string)
        # output: successful message of inserted port.
        def add_port(self,  port_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_port, port_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.p_insert_success_message)
            except:
                print(dbp.p_insert_error_message)
                
    class LinkManagement():
        def __init__(self,*args,**kwargs):
            self.db_connection = ''
            self.cursor = ''
        
        def db_connect(self):
            self.db_connection = mysql.connector.connect(**db_config.DB_CONFIG)
            self.cursor = self.db_connection.cursor(buffered=True)
            
        def db_close_connection(self):
            self.cursor.close()
            self.db_connection.close()
            
        # input: link_data (tuple): (link_id, tx_node, tx_node_port, rx_node, rx_node_port, amplifier_no, length)
        # (int, int, int, int, int, int, int)
        # output: successful message of inserted link
        def add_link(self,  link_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_link, link_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.l_insert_success_message)
            except:
                print(dbp.l_insert_error_message)
                
        # input: link_to_channel_data (tuple): (link_id, channel) (int, int)
        # output: insert into link_to_channel table
        def add_link_to_channel(self,  link_to_channel_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_link_to_channel, link_to_channel_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.ltc_insert_success_message)
            except:
                print(dbp.ltc_insert_error_message)
                
        # input: nodes_data (tuple): (tx_node, rx_node) (int, int)
        # output: link_id (int)
        def select_link_id_with_nodes(self,  nodes_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_link_id_with_nodes,  nodes_data)
                #print(dbp.l_select_link_id_with_nodes_success_message)
                link_id = self.cursor.fetchall()[0][0]
                self.db_close_connection()
                return link_id
            except:
                print(dbp.l_select_link_id_with_nodes_error_message)
                
        # input: nodes_data (tuple): (tx_node, rx_node) (int, int)
        # output: link_id (int)
        def select_link_with_id(self, link_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_link_with_id, link_id)
                #print(dbp.l_select_link_with_id_success_message)
                link = self.cursor.fetchall()[0]
                self.db_close_connection()
                return link
            except:
                print(dbp.l_select_link_with_id_error_message)
                
        # input: none
        # output: links (list)
        def select_link_all(self):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_link_all)
                #print(dbp.l_select_all_success_message)
                links = self.cursor.fetchall()
                self.db_close_connection()
                return links
            except:
                print(dbp.l_select_all_error_message)
                
        # input: link_id (tuple): (link_id,) (int)
        # output: available_channels (list)
        def select_available_channels(self, link_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.select_available_channels,  link_id)
                #print(dbp.l_select_available_channels_success_message)
                available_channels = self.cursor.fetchall()
                self.db_close_connection()
                return available_channels
            except:
                print(dbp.l_select_available_channels_error_message)
                
    class TrafficManagement():
                
        def __init__(self,*args,**kwargs):
            self.db_connection = ''
            self.cursor = ''
        
        def db_connect(self):
            self.db_connection = mysql.connector.connect(**db_config.DB_CONFIG)
            self.cursor = self.db_connection.cursor(buffered=True)
            
        def db_close_connection(self):
            self.cursor.close()
            self.db_connection.close()
        
        # input: lightpath_data (tuple): (lightpath_id, tx_node, rx_node, status) - (int, int, int, int)
        # output: successful message of inserted lightpath.
        def create_lightpath(self,  lightpath_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_lightpath, lightpath_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.t_insert_success_message)
                return 1
            except:
                print(dbp.t_insert_error_message)
                return 0
         
        # input: lightpath_data (tuple): (status, lightpath_id) (int, int)
        # output: successfully updated/activated the lightpath in database
        def activate_lightpath(self,  lightpath_data):
            try:
                self.db_connect()
                self.cursor.execute(dbp.update_lightpath, lightpath_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.t_update_success_message)
                return 1
            except:
                print(dbp.t_update_error_message)
                return 0
                
        def get_nodes_with_id(self, lightpath_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.t_get_nodes_with_id, lightpath_id)
                self.db_connection.commit()
                nodes = self.cursor.fetchall()[0]
                self.db_close_connection()
                return nodes
            except:
                print(dbp.t_get_nodes_error_message)
                return 0
                
        # input: route_data (tuple): (r_lightpath_id, sequence, r_link_id) - (int, int, int)
        # output: successful message of inserted route.
        def add_route(self,  route_data):
            #print("DatabaseManagement.TrafficManagement: add_link_to_channel: ENTERING: %s" %route_data)
            try:
                self.db_connect()
                self.cursor.execute(dbp.insert_route, route_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.r_insert_success_message)
            except:
                print(dbp.r_insert_error_message)
                
        # functional method of threaded function:
        # call_remote_mininet_server(self, ev) below.
#        def th_update_link_to_channel(self, link_to_channel_data):
#            print("DatabaseManagement.TrafficManagement: add_link_to_channel: ENTERING: " )
#            print(link_to_channel_data)
#            try:
#                self.db_connect()
#                self.cursor.execute(dbp.update_link_to_channel_link, link_to_channel_data)
#                self.db_connection.commit()
#                self.db_close_connection()
#                #print(dbp.ltc_update_link_success_message)
#            except:
#                print(dbp.ltc_update_link_error_message)
#            link_to_channel_lock.release()

        # input: link_to_channel_data (tuple): (lightpath_id, link_id, channel) (int, int, int)
        # output: successfully update values in link_to_channel table
        def update_link_to_channel(self,  link_to_channel_data):
#            link_to_channel_lock.acquire()
#            start_new_thread(self.th_update_link_to_channel, (link_to_channel_data, ))
            try:
                self.db_connect()
                self.cursor.execute(dbp.update_link_to_channel_link, link_to_channel_data)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.ltc_update_link_success_message)
            except:
                print(dbp.ltc_update_link_error_message)
                
        def cancel_lightpath(self, lightpath_id):
            try:
                self.db_connect()
                self.cursor.execute(dbp.cancel_lightpath, lightpath_id)
                self.db_connection.commit()
                self.db_close_connection()
                #print(dbp.lp_cancel_lightpath_error_message)
            except:
                print(dbp.lp_cancel_lightpath_error_message)
        
        
