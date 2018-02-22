"""
EastWest message receiving

Author:   Yao Li (yaoli@optics.arizona.edu)
Created:  2017/01/19
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

class EastWest_message_receive(app_manager.RyuApp):
    
    _EVENTS =  [Custom_event.EastWest_ReceivePathCompRequestEvent,  
                Custom_event.EastWest_ReceivePathCompReplyEvent,   
                Custom_event.EastWest_ReceiveTrafSetupRequestEvent, 
                Custom_event.EastWest_ReceiveTrafSetupReplyEvent,  
                Custom_event.EastWest_ReceiveTrafTeardownRequest,  
                Custom_event.EastWest_ReceiveTrafTeardownReply, 
                Custom_event.EastWest_ReceiveTearDownPath,  
                Custom_event.EastWest_ReceiveOSNRMonitoringRequestEvent,   
                Custom_event.EastWest_ReceiveOSNRMonitoringReplyEvent]
                
    def __init__(self,*args,**kwargs):
        super(EastWest_message_receive,self).__init__(*args,**kwargs)
        self.listening_data_thread = []
        self.listening_thread = hub.spawn(self._listening)
        
    def _listening(self):
        #pass
        #while True:
            #receive a message
            #if this message does not have a timer in Database.Data.eastwest_timer
            #   discard this message
            #   print error information
            #else: 
            #   send events to other modules based on message type
            #   delete this timer 
            #if there are items in Database.Data.eastwest_timer to be timeout
            #   send timeout reply
            #   delete these timers
            #hub.sleep(1)
            
        #host = Database.Data.controller_list.this_controller.controller_ip
        host = 'localhost'
        port = 4998
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   
        s.bind((host, port))
        s.listen(1)
        client_list = []
        while True:
            #Database.Data.socket_server,addr=s.accept() 
            connection,addr=s.accept()
            if addr not in client_list:
            	self.logger.info("Connection from: {0}".format(addr))
                client_list.append(addr)         
                self.listening_data_thread.append(hub.spawn(self._listening_data, connection))
                self.logger.debug('Server done!\n')
            hub.sleep(0.1)
        #while True:
            
        #hub.sleep(0.1)
            
    def _listening_data(self, connection):
    #super(EastWest_message_receive,self).start()
        while True:
            #data = Database.Data.socket_server.recv(4096)             # receive some data from connection, with buffer=1024 bytes
            data = connection.recv(4096) 
            #data = pickle.loads(data)
            head = data[0:4]
            head = struct.unpack('!i', head)
            #self.logger.debug(data)
                
            flag = True
            #if data[0] == EW_PATH_COMP_REQ: #EastWest_ReceivePathCompRequestEvent
            if head[0] == EW_PATH_COMP_REQ:
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_PATH_COMP_REQ')
                cross_domain_pc_ev = Custom_event.EastWest_ReceivePathCompRequestEvent()
                cross_domain_pc_ev.traf_id = data[0]
                cross_domain_pc_ev.route_type = data[1]
                cross_domain_pc_ev.entry_of_next_domain = data[2]
                self.send_event('Path_computation', cross_domain_pc_ev) 
            elif head[0] == EW_PATH_COMP_REPLY: #EastWest_ReceivePathCompReplyEvent
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_PATH_COMP_REPLY')
                this_traf = Database.Data.traf_list.find_traf_by_id(data[0])
                if this_traf == None:
                    self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % data[0])
                    return
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    if Database.Data.msg_in_eastwest_timer(data[0], TIMER_PATH_COMPUTATION) != True:
                        self.logger.info('Cannot find timer information. (EastWest_message_receive: _listening)')
                        flag = False
                    else:
                        for this_timer in Database.Data.eastwest_timer:
                            if (this_timer.traf_id == data[0]) and (this_timer.timer_type == TIMER_PATH_COMPUTATION):
                                Database.Data.eastwest_timer.remove(this_timer)
                                #for recording excusion time
                                with open('record_time.txt', 'a') as f:
                                    f.write('eastwest path computation time: (route_type = %s) \n' % str(data[1]))
                                    f.write(str(time.time() - Database.Data.ew_ps_time)+'\n')
                                Database.Data.ew_ps_time = 0
                                #for recording excusion time end
                                break
                if flag == True:
                    pc_reply_ev = Custom_event.EastWest_ReceivePathCompReplyEvent()
                    pc_reply_ev.traf_id = data[0]
                    pc_reply_ev.route_type = data[1]
                    pc_reply_ev.result = data[2]
                    #pc_reply_ev.resource_allocation = data[3]
                    pc_reply_ev.exit_of_this_domain = data[3]
                    self.send_event('Path_computation', pc_reply_ev)
            elif head[0] == EW_TRAF_SETUP_REQ:  #EastWest_ReceiveTrafSetupRequestEvent
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_TRAF_SETUP_REQ')
                traf_setup_req_ev = Custom_event.EastWest_ReceiveTrafSetupRequestEvent()
                traf_setup_req_ev.traf_id = data[0]
                traf_setup_req_ev.traf_stage = data[1]
                self.send_event('Cross_domain_connection_ctrl', traf_setup_req_ev)
            elif head[0] == EW_TRAF_SETUP_REPLY:    #EastWest_ReceiveTrafSetupReplyEvent
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_TRAF_SETUP_REPLY')
                this_traf = Database.Data.traf_list.find_traf_by_id(data[0])
                if this_traf == None:
                    self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % data[0])
                    return
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    if Database.Data.msg_in_eastwest_timer(data[0], TIMER_TRAFFIC_SETUP) != True:
                        self.logger.info('Cannot find timer information. (EastWest_message_receive: _listening)')
                        flag = False
                    else:
                        for this_timer in Database.Data.eastwest_timer:
                            if (this_timer.traf_id == data[0]) and (this_timer.timer_type == TIMER_TRAFFIC_SETUP):
                                Database.Data.eastwest_timer.remove(this_timer)
                                #for recording excusion time
                                with open('record_time.txt', 'a') as f:
                                    f.write('eastwest setup time: (route_type = ')
                                if data[1] == TRAFFIC_WORKING:
                                    f.write(str(ROUTE_WORKING)+')\n')
                                else:
                                    f.write(str(ROUTE_REROUTE)+')\n')
                                    f.write(str(time.time() - Database.Data.ew_setup_time)+'\n')
                                Database.Data.ew_setup_time = 0
                                #for recording excusion time end
                                break
                if flag == True:
                    traf_setup_reply_ev = Custom_event.EastWest_ReceiveTrafSetupReplyEvent()
                    traf_setup_reply_ev.traf_id = data[0]
                    traf_setup_reply_ev.traf_stage = data[1]
                    traf_setup_reply_ev.traf_state = data[2]
                    traf_setup_reply_ev.result = data[3]
                    self.send_event('Cross_domain_connection_ctrl', traf_setup_reply_ev)
            elif head[0] == EW_TRAF_TEAR_REQ:   #EastWest_ReceiveTrafTeardownRequest
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_TRAF_TEAR_REQ')
                traf_tear_req_ev = Custom_event.EastWest_ReceiveTrafTeardownRequest()
                traf_tear_req_ev.traf_id =data[0]
                traf_tear_req_ev.traf_stage = data[1]
                traf_tear_req_ev.traf_state = data[2]
                self.send_event('Cross_domain_connection_ctrl', traf_tear_req_ev)
            elif head[0] == EW_TRAF_TEAR_REPLY: #EastWest_ReceiveTrafTeardownReply
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_TRAF_TEAR_REPLY')
                this_traf = Database.Data.traf_list.find_traf_by_id(data[0])
                if this_traf == None:
                    self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % data[0])
                    return
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    if Database.Data.msg_in_eastwest_timer(data[0], TIMER_TRAFFIC_TEARDOWN) != True:
                        self.logger.info('Cannot find timer information. (EastWest_message_receive: _listening)')
                        flag = False
                    else:
                        for this_timer in Database.Data.eastwest_timer:
                            if (this_timer.traf_id == data[0]) and (this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN):
                                Database.Data.eastwest_timer.remove(this_timer)
                                #for recording excusion time
                                with open('record_time.txt', 'a') as f:
                                    f.write('eastwest teardown time: \n')
                                    f.write(str(time.time() - Database.Data.ew_teardown_time)+'\n')
                                Database.Data.ew_teardown_time = 0
                                #for recording excusion time end
                                break
                if flag == True:
                    traf_tear_reply_ev = Custom_event.EastWest_ReceiveTrafTeardownReply()
                    traf_tear_reply_ev.traf_id = data[0]
                    traf_tear_reply_ev.result = data[1]
                    self.send_event('Cross_domain_connection_ctrl', traf_tear_reply_ev)
            elif head[0] == EW_TRAF_TEAR_PATH_REQ:  #EastWest_ReceiveTearDownPath
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_TRAF_TEAR_PATH_REQ')
                traf_tear_path_ev = Custom_event.EastWest_ReceiveTearDownPath()
                traf_tear_path_ev.traf_id = data[0]
                traf_tear_path_ev.route_type = data[1]
                self.send_event('Cross_domain_connection_ctrl', traf_tear_path_ev)
            elif head[0] == EW_OSNR_MONITOR_REQ:    #EastWest_ReceiveOSNRMonitoringRequestEvent
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_OSNR_MONITOR_REQ')
                osnr_req_ev = Custom_event.EastWest_ReceiveOSNRMonitoringRequestEvent()
                osnr_req_ev.traf_id = data[0]
                osnr_req_ev.route_type = data[1]
                #osnr_req_ev.result = data[3]
                self.send_event('Cross_domain_connection_ctrl', osnr_req_ev)
            elif head[0] == EW_OSNR_MONITOR_REPLY:  #EastWest_ReceiveOSNRMonitoringReplyEvent
                data = pickle.loads(data[4:])
                self.logger.debug('EW interface receives a message, type = EW_OSNR_MONITOR_REPLY')
                this_traf = Database.Data.traf_list.find_traf_by_id(data[0])
                if this_traf == None:
                    self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % data[0])
                    return
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    if Database.Data.msg_in_eastwest_timer(data[0], TIMER_OSNR_MONITORING) != True:
                        self.logger.info('Cannot find timer information. (EastWest_message_receive: _listening)')
                        flag = False
                    else:
                        for this_timer in Database.Data.eastwest_timer:
                            if (this_timer.traf_id == data[0]) and (this_timer.timer_type == TIMER_OSNR_MONITORING):
                                Database.Data.eastwest_timer.remove(this_timer)
                                #for recording excusion time
                                with open('record_time.txt', 'a') as f:
                                    f.write('eastwest osnr monitor time: (route_type = ')
                                if data[1] == TRAFFIC_WORKING:
                                    f.write(str(ROUTE_WORKING)+')\n')
                                else:
                                    f.write(str(ROUTE_REROUTE)+')\n')
                                    f.write(str(time.time() - Database.Data.ew_osnr_monitor_time)+'\n')
                                Database.Data.ew_osnr_monitor_time = 0
                                #for recording excusion time end
                                break
                if flag == True:
                    osnr_reply_ev = Custom_event.EastWest_ReceiveOSNRMonitoringReplyEvent()
                    osnr_reply_ev.traf_id = data[0]
                    osnr_reply_ev.route_type = data[1]
                    osnr_reply_ev.result = data[2]
                    osnr_reply_ev.is_inter_domain_impairment = data[3]
                    osnr_reply_ev.traf_stage = data[4]
                    osnr_reply_ev.traf_state = data[5]
                    self.send_event('Cross_domain_connection_ctrl', osnr_reply_ev)
            else:
                self.logger.info('Invalid eastwest bound message type! (EastWest_message_receive: _listening)')
                
            # handle timeout
            ready_remove = list()
            for this_timer in Database.Data.eastwest_timer:
                if this_timer.end_time < time.time():
                    if this_timer.timer_type == TIMER_TRAFFIC_SETUP:
                        this_traf = Database.Data.traf_list.find_traf_by_id(this_timer.traf_id)
                        if this_traf == None:
                            self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            return 
                        traf_setup_reply_ev = Custom_event.EastWest_ReceiveTrafSetupReplyEvent()
                        traf_setup_reply_ev.traf_id = this_timer.traf_id
                        traf_setup_reply_ev.traf_stage = this_traf.traf_stage
                        traf_setup_reply_ev.traf_state = TRAFFIC_SETUP_FAIL
                        if this_traf.traf_stage == TRAFFIC_WORKING:
                            traf_setup_reply_ev.result = TIMEOUT_TRAF_SETUP
                        elif this_traf.traf_stage == TRAFFIC_REROUTING:
                            traf_setup_reply_ev.result = TIMEOUT_REROUTING
                        else:
                            self.logger.info('Traffic %d is inactive. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            continue
                        self.send_event('Cross_domain_connection_ctrl', traf_setup_reply_ev)
                        ready_remove.append(this_timer) #delete this timer
                        self.logger.debug('traffic %d setup timeout (EW).' % this_timer.traf_id)
                    elif this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        traf_tear_reply_ev = Custom_event.EastWest_ReceiveTrafTeardownReply()
                        traf_tear_reply_ev.traf_id = this_timer.traf_id
                        traf_tear_reply_ev.result = TIMEOUT_TRAF_TEARDOWN
                        self.send_event('Cross_domain_connection_ctrl', traf_tear_reply_ev)
                        ready_remove.append(this_timer) #delete this timer
                        self.logger.debug('traffic %d teardown timeout (EW).' % this_timer.traf_id)
                    elif this_timer.timer_type == TIMER_PATH_COMPUTATION:
                        this_traf = Database.Data.traf_list.find_traf_by_id(this_timer.traf_id)
                        if this_traf == None:
                            self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            return 
                        pc_reply_ev = Custom_event.EastWest_ReceivePathCompReplyEvent()
                        pc_reply_ev.traf_id = this_timer.traf_id
                        if this_traf.traf_stage == TRAFFIC_WORKING:
                            pc_reply_ev.route_type = ROUTE_WORKING
                        elif this_traf.traf_stage == TRAFFIC_REROUTING:
                            pc_reply_ev.route_type = ROUTE_REROUTE
                        else:
                            self.logger.info('Traffic %d is inactive. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            continue
                        pc_reply_ev.result = TIMEOUT_PATH_COMPUTATION
                        #pc_reply_ev.resource_allocation = []
                        pc_reply_ev.exit_of_this_domain = None
                        self.send_event('Path_computation', pc_reply_ev)
                        ready_remove.append(this_timer) #delete this timer
                        self.logger.debug('traffic %d path computation timeout (EW).' % this_timer.traf_id)
                    elif this_timer.timer_type == TIMER_OSNR_MONITORING:
                        this_traf = Database.Data.traf_list.find_traf_by_id(this_timer.traf_id)
                        if this_traf == None:
                            self.logger.critical('Cannot find traffic %d. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            return 
                        osnr_reply_ev = Custom_event.EastWest_ReceiveOSNRMonitoringReplyEvent()
                        osnr_reply_ev.traf_id = timer.traf_id
                        if this_traf.traf_stage == TRAFFIC_WORKING:
                            if this_traf.traf_state != TRAFFIC_ON_BACKUP_PATH:
                                osnr_reply_ev.route_type = ROUTE_WORKING
                            else:
                                osnr_reply_ev.route_type = ROUTE_BACKUP
                        elif this_traf.traf_stage == TRAFFIC_REROUTING:
                            osnr_reply_ev.route_type = ROUTE_REROUTE
                        else:
                            self.logger.info('Traffic %d is inactive. (EastWest_message_receive: _listening)' % this_timer.traf_id)
                            continue
                        osnr_reply_ev.result = TIMEOUT_OSNR_MONITORING
                        osnr_reply_ev.is_inter_domain_impairment = None
                        osnr_reply_ev.traf_stage = this_traf.traf_stage
                        osnr_reply_ev.traf_state = this_traf.traf_state
                        self.send_event('Cross_domain_connection_ctrl', osnr_reply_ev)
                        ready_remove.append(this_timer) #delete this timer
                        self.logger.debug('traffic %d OSNR monitoring timeout (EW).' % this_timer.traf_id)
                    else:
                        self.logger.info('Invalid eastwest timer type! (EastWest_message_receive: _listening)')
            for timer in ready_remove:
                Database.Data.south_timer.remove(timer)
            
            hub.sleep(0.1)
           
            
        
           
