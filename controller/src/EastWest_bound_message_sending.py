"""
EastWest message sending

Author:   Yao Li (yaoli@optics.arizona.edu)
Created:  2017/01/10
Version:  1.0

Last modified by Yao: 2017/05/19

"""

from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import time
import socket
import pickle
import struct
from Common import *
import Database
import Custom_event
import logging
from Common import log_level

logging.basicConfig(level = log_level)

class EastWest_message_send(app_manager.RyuApp):
    
    _EVENTS =  [Custom_event.EastWest_SendPathCompRequestEvent,
                Custom_event.EastWest_SendPathCompReplyEvent,
                Custom_event.EastWest_SendTrafSetupRequestEvent,
                Custom_event.EastWest_SendTrafSetupReplyEvent,
                Custom_event.EastWest_SendTrafTeardownRequest,
                Custom_event.EastWest_SendTrafTeardownReply,
                Custom_event.EastWest_SendTearDownPath,
                Custom_event.EastWest_SendOSNRMonitoringRequestEvent,
                Custom_event.EastWest_SendOSNRMonitoringReplyEvent,
        Custom_event.North_CrossDomainTrafficRequestEvent]
                
    def __init__(self,*args,**kwargs):
        super(EastWest_message_send,self).__init__(*args,**kwargs)
        
    def start(self):
        super(EastWest_message_send,self).start()
        hub.sleep(3)
        for local_ctrl in Database.Data.controller_list.local_controllers:
           if (local_ctrl.controller_type == CONTROLLER_LOCAL) and (local_ctrl.controller_ip != Database.Data.controller_list.this_controller.controller_ip):
               host = 'localhost'#local_ctrl.controller_ip  
               port = 4999
               s = socket.socket()
               s.connect((host, port))
               s.setblocking(False)
               Database.Data.socket_client[local_ctrl.controller_ip] = s
        self.logger.debug('Client done!\n')
        #self.logger.debug(s)
        self.logger.debug(Database.Data.controller_list.this_controller.controller_ip)

        # for testing
        '''hub.sleep(8)
        new_north_traffic_request_ev = Custom_event.North_CrossDomainTrafficRequestEvent()
        new_north_traffic_request_ev.traf_id = 1
        new_north_traffic_request_ev.traf_stage = TRAFFIC_WORKING
        new_north_traffic_request_ev.traf_state = TRAFFIC_RECEIVE_REQUEST
        new_north_traffic_request_ev.src_node_ip = '192.168.1.1'
        new_north_traffic_request_ev.dst_node_ip = '192.168.2.3'
        new_north_traffic_request_ev.traf_type = TRAFFIC_CROSS_DOMAIN
        new_north_traffic_request_ev.prot_type = TRAFFIC_REROUTING_RESTORATION
        new_north_traffic_request_ev.bw_demand = 50
        new_north_traffic_request_ev.OSNR_req = 0
        new_north_traffic_request_ev.domain_num = 2
        new_north_traffic_request_ev.domain_sequence = [1,2]
        #hub.sleep(1)
        self.send_event('Cross_domain_connection_ctrl', new_north_traffic_request_ev)
        self.logger.debug("\nFirst north traffic request event")
        # for testing end'''
        
    @set_ev_cls(Custom_event.EastWest_SendPathCompRequestEvent)
    def _handle_send_cross_domain_pc_request(self,ev):
        #send cross-domain path computation request message to next domain
        #if this domain is the source domain:
        #   setup a timer in Database.Data.eastwest_timer
        #pass
        self.logger.debug('EastWest_message_send receives EastWest_SendPathCompRequestEvent')
        next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if next_domain_id == None:
            self.logger.critical('Cannot find next domain id. (EastWest_message_send: _handle_send_cross_domain_pc_request)')
            return
        #next_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(next_domain_id)
	next_controller_ip = '192.168.2.0'
        if next_controller_ip == None:
            self.logger.critical('Cannot find next controller ip. (EastWest_message_send: _handle_send_cross_domain_pc_request)')
            return
        this_socket = Database.Data.socket_client[next_controller_ip]
        #msg = [EW_PATH_COMP_REQ, ev.traf_id, ev.route_type, ev.entry_of_next_domain]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_PATH_COMP_REQ) + pickle.dumps([ev.traf_id, ev.route_type, ev.entry_of_next_domain])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_PATH_COMP_REQ message sent.')
        # set up a timer
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) == True: 
            new_timer = Database.Timer()
            new_timer.traf_id = ev.traf_id
            new_timer.timer_type = TIMER_PATH_COMPUTATION
            new_timer.end_time = time.time() + EASTWEST_WAITING_TIME
            Database.Data.eastwest_timer.append(new_timer)
        #for resording excution time
        if Database.Data.ew_ps_time == 0:       
            Database.Data.ew_ps_time = time.time()
        else:
            self.logger.critical('ew_ps_time error! \n')
        #for resording excution time end
               
    @set_ev_cls(Custom_event.EastWest_SendPathCompReplyEvent)
    def _handle_send_cross_domain_pc_reply(self,ev):
        #send cross-domain path computation reply message to previous domain
        #pass
        self.logger.debug('EastWest_message_send receives EastWest_SendPathCompReplyEvent')
        previous_domain_id = Database.Data.traf_list.find_previous_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if previous_domain_id == None:
            self.logger.info('Cannot find previous domain id. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        previous_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(previous_domain_id)
        if previous_controller_ip == None:
            self.logger.info('Cannot find previous controller ip. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        this_socket = Database.Data.socket_client[previous_controller_ip]
        #msg = [EW_PATH_COMP_REPLY, ev.traf_id, ev.route_type, ev.result, ev.resource_allocation]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i',EW_PATH_COMP_REPLY) + pickle.dumps([ev.traf_id, ev.route_type, ev.result, ev.exit_of_previous_domain])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_PATH_COMP_REPLY message sent.')
        
    @set_ev_cls(Custom_event.EastWest_SendTrafSetupRequestEvent)
    def _handle_send_cross_domain_setup_request(self,ev):
        #send cross-domain traffic setup request message to next domain
        #if this domain is the source domain:
        #   setup a timer in Database.Data.eastwest_timer
        #pass
        self.logger.debug('EastWest_message_send module receives EastWest_SendTrafSetupRequestEvent')
        next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if next_domain_id == None:
            self.logger.critical('Cannot find next domain id. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        #next_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(next_domain_id)
        next_controller_ip = '192.168.2.0'
        if next_controller_ip == None:
            self.logger.critical('Cannot find next controller ip. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        this_socket = Database.Data.socket_client[next_controller_ip]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_TRAF_SETUP_REQ) + pickle.dumps([ev.traf_id, ev.traf_stage])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_TRAF_SETUP_REQ message sent.')
        # set up a timer
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) == True: 
            new_timer = Database.Timer()
            new_timer.traf_id = ev.traf_id
            new_timer.timer_type = TIMER_TRAFFIC_SETUP
            new_timer.end_time = time.time() + EASTWEST_WAITING_TIME
            Database.Data.eastwest_timer.append(new_timer)
        #for resording excution time
        if Database.Data.ew_setup_time == 0:        
            Database.Data.ew_setup_time = time.time()
        else:
            self.logger.critical('ew_setup_time error! \n')
        #for resording excution time end
        
    @set_ev_cls(Custom_event.EastWest_SendTrafSetupReplyEvent)
    def _handle_send_cross_domain_setup_reply(self,ev):
        #send cross-domain traffic setup reply message to previous domain
        #pass
        self.logger.debug('EastWest_message_send module receives EastWest_SendTrafSetupReplyEvent')
        previous_domain_id = Database.Data.traf_list.find_previous_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if previous_domain_id == None:
            self.logger.critical('Cannot find previous domain id. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        previous_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(previous_domain_id)
        if previous_controller_ip == None:
            self.logger.critical('Cannot find previous controller ip. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        this_socket = Database.Data.socket_client[previous_controller_ip]
        #msg = [EW_TRAF_SETUP_REPLY, ev.traf_id, ev.traf_stage, ev.traf_state, ev.result]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_TRAF_SETUP_REPLY) + pickle.dumps([ev.traf_id, ev.traf_stage, ev.traf_state, ev.result])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_TRAF_SETUP_REPLY message sent.')
    
    @set_ev_cls(Custom_event.EastWest_SendTrafTeardownRequest)
    def _handle_send_traf_teardown_request(self,ev):
        #send teardown traffic request message to next domain
        #if this domain is the source domain:
        #   setup a timer in Database.Data.eastwest_timer
        #pass
        next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if next_domain_id == None:
            self.logger.info('Cannot find next domain id. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        #next_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(next_domain_id)
	next_controller_ip = '192.168.2.0'
        if next_controller_ip == None:
            self.logger.info('Cannot find next controller ip. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        this_socket = Database.Data.socket_client[next_controller_ip]
        #msg = [EW_TRAF_TEAR_REQ, ev.traf_id, ev.traf_stage, ev.traf_state]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_TRAF_TEAR_REQ) + pickle.dumps([ev.traf_id, ev.traf_stage, ev.traf_state])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_TRAF_TEAR_REQ message sent.')
        # set up a timer
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) == True: 
            new_timer = Database.Timer()
            new_timer.traf_id = ev.traf_id
            new_timer.timer_type = TIMER_TRAFFIC_TEARDOWN
            new_timer.end_time = time.time() + EASTWEST_WAITING_TIME
            Database.Data.eastwest_timer.append(new_timer)
        #for resording excution time
        if Database.Data.ew_teardown_time == 0:     
            Database.Data.ew_teardown_time = time.time()
        else:
            self.logger.critical('ew_teardown_time error! \n')
        #for resording excution time end
        
    @set_ev_cls(Custom_event.EastWest_SendTrafTeardownReply)
    def _handle_send_traf_teardown_reply(self,ev):
        #send teardown traffic reply message to previous domain    
        #pass
        previous_domain_id = Database.Data.traf_list.find_previous_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if previous_domain_id == None:
            self.logger.info('Cannot find previous domain id. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        previous_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(previous_domain_id)
        if previous_controller_ip == None:
            self.logger.info('Cannot find previous controller ip. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        this_socket = Database.Data.socket_client[previous_controller_ip]
        #msg = [EW_TRAF_SETUP_REPLY, ev.traf_id, ev.result]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_TRAF_DOWN_REPLY) + pickle.dumps([ev.traf_id, ev.result])      
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_TRAF_SETUP_REPLY message sent.')
    
    @set_ev_cls(Custom_event.EastWest_SendTearDownPath)
    def _handle_send_teardown_path_request(self,ev):
        #send teardown path message to next domain
        #pass
        next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if next_domain_id == None:
            self.logger.info('Cannot find next domain id. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        #next_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(next_domain_id)
	next_controller_ip = '192.168.2.0'
        if next_controller_ip == None:
            self.logger.info('Cannot find next controller ip. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        this_socket = Database.Data.socket_client[next_controller_ip]
        #msg = [EW_TRAF_TEAR_PATH_REQ, ev.traf_id, ev.route_type]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_TRAF_TEAR_PATH_REQ) + pickle.dumps([ev.traf_id, ev.route_type])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_TRAF_TEAR_PATH_REQ message sent.')
        
    @set_ev_cls(Custom_event.EastWest_SendOSNRMonitoringRequestEvent)
    def _handle_send_cross_domain_OSNR_monitoring_request(self,ev):
        #send OSNR monitoring request message to next domain
        #if this domain is the source domain:
        #   setup a timer in Database.Data.eastwest_timer
        #pass
        self.logger.debug('EastWest_message_send module receives EastWest_SendOSNRMonitoringRequestEvent')
        next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if next_domain_id == None:
            self.logger.info('Cannot find next domain id. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        #next_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(next_domain_id)
	next_controller_ip = '192.168.2.0'
        if next_controller_ip == None:
            self.logger.info('Cannot find next controller ip. (EastWest_message_send: _handle_send_cross_domain_setup_request)')
            return
        this_socket = Database.Data.socket_client[next_controller_ip]
        #msg = [EW_OSNR_MONITOR_REQ, ev.traf_id, ev.route_type]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_OSNR_MONITOR_REQ) + pickle.dumps([ev.traf_id, ev.route_type])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_OSNR_MONITOR_REQ message sent.')
        # set up a timer
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) == True: 
            new_timer = Database.Timer()
            new_timer.traf_id = ev.traf_id
            new_timer.timer_type = TIMER_OSNR_MONITORING
            new_timer.end_time = time.time() + EASTWEST_WAITING_TIME
            Database.Data.eastwest_timer.append(new_timer)
        #for resording excution time
        if Database.Data.ew_osnr_monitor_time == 0:     
            Database.Data.ew_osnr_monitor_time = time.time()
        else:
            self.logger.critical('ew_osnr_monitor_time error! \n')
        #for resording excution time end
        
    @set_ev_cls(Custom_event.EastWest_SendOSNRMonitoringReplyEvent)
    def _handle_send_cross_domain_OSNR_monitoring_reply(self,ev):
        #send OSNR monitoring repy message to previous domain
        #pass
        self.logger.debug('EastWest_message_send module receives EastWest_SendOSNRMonitoringReplyEvent')
        previous_domain_id = Database.Data.traf_list.find_previous_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
        if previous_domain_id == None:
            self.logger.info('Cannot find previous domain id. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        previous_controller_ip = Database.Data.controller_list.get_controller_ip_by_domain_id(previous_domain_id)
        if previous_controller_ip == None:
            self.logger.info('Cannot find previous controller ip. (EastWest_message_send: _handle_send_cross_domain_pc_reply)')
            return
        this_socket = Database.Data.socket_client[previous_controller_ip]
        #msg = [EW_OSNR_MONITOR_REPLY, ev.traf_id, ev.route_type, ev.result, ev.is_inter_domain_impairment, ev.traf_stage, ev.traf_state]
        #msg = pickle.dumps(msg)
        msg = struct.pack('!i', EW_OSNR_MONITOR_REPLY) + pickle.dumps([ev.traf_id, ev.route_type, ev.result, ev.is_inter_domain_impairment, ev.traf_stage, ev.traf_state])
        this_socket.send(msg)             # send message
        self.logger.debug('A EW_OSNR_MONITOR_REPLY message sent.')
