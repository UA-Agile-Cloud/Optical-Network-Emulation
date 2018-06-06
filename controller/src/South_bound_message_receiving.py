"""
listening to openflow events

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
Created:  2017/01/18
Version:  1.0

Last modifiedby Yao: 2017/02/07
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER,DEAD_DISPATCHER,HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
import time
from Common import *
import Database
import Custom_event
import logging
from Common import log_level

logging.basicConfig(level = log_level)

class South_bound_message_receive(app_manager.RyuApp):
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    _EVENTS =  [Custom_event.South_LSPSetupReplyEvent,
                Custom_event.South_LSPTeardownReplyEvent,
                Custom_event.South_OSNRMonitoringReplyEvent]
                
    def __init__(self,*args,**kwargs):
        super(South_bound_message_receive,self).__init__(*args,**kwargs)
        self.listening_thread = hub.spawn(self._listening)
    
    def _listening(self):
        pass
        #while True:
            #if there are items in south_timer to be timeout
            #   send timeout reply
            #   delete these timers
            #if there are items in south_timer_no_response to be timeout
            #   delete these timers
            #hub.sleep(1)
        while True:
            ready_remove = list()
            for this_timer in Database.Data.south_timer:
                if this_timer.end_time < time.time():
                    if this_timer.timer_type == TIMER_TRAFFIC_SETUP:
                        ev_lsp_setup_reply = Custom_event.South_LSPSetupReplyEvent()
                        ev_lsp_setup_reply.traf_id = this_timer.traf_id
                        #ev_lsp_setup_reply.result = TIMEOUT_TRAF_SETUP
                        tmp_traf = Database.Data.traf_list.find_traf_by_id(this_timer.traf_id)
                        if tmp_traf.traf_stage == TRAFFIC_WORKING:
                            ev_lsp_setup_reply.result = TIMEOUT_TRAF_SETUP
                        elif tmp_traf.traf_stage == TRAFFIC_REROUTING:
                            ev_lsp_setup_reply.result = TIMEOUT_REROUTING
                        else:
                            self.logger.info('Traffic stage is INACTIVE! (South_bound_message_receive: _listening)')
                        if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                            self.send_event('Intra_domain_connection_ctrl',ev_lsp_setup_reply)
                        elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                            self.send_event('Cross_domain_connection_ctrl',ev_lsp_setup_reply)
                        else:
                            self.logger.info('Invalid traffic type! (South_bound_message_receive: _listening)')
                        #Database.Data.south_timer.remove(this_timer)
                        ready_remove.append(this_timer)
                        self.logger.debug('traffic %d setup timeout (south).' % this_timer.traf_id)
                    elif this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        ev_lsp_teardown_reply = Custom_event.South_LSPTeardownReplyEvent()
                        ev_lsp_teardown_reply.traf_id = this_timer.traf_id
                        ev_lsp_teardown_reply.result = TIMEOUT_TRAF_TEARDOWN
                        tmp_traf = Database.Data.traf_list.find_traf_by_id(int(this_timer.traf_id))
                        if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                            self.send_event('Intra_domain_connection_ctrl',ev_lsp_teardown_reply)
                        elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                            self.send_event('Cross_domain_connection_ctrl',ev_lsp_teardown_reply)
                        else:
                            self.logger.info('Invalid traffic type! (South_bound_message_receive: _listening)')
                        #Database.Data.south_timer.remove(this_timer)
                        ready_remove.append(this_timer)
                        #self.logger.debug('traffic %d teardown timeout (south).' % this_timer.traf_id)
                    elif this_timer.timer_type == TIMER_OSNR_MONITORING:
                        ev_lsp_osnr_monitor_reply = Custom_event.South_OSNRMonitoringReplyEvent()
                        ev_lsp_osnr_monitor_reply.traf_id = this_timer.traf_id
                        ev_lsp_osnr_monitor_reply.result = TIMEOUT_OSNR_MONITORING
                        tmp_traf = Database.Data.traf_list.find_traf_by_id(this_timer.traf_id)
                        if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                            self.send_event('Intra_domain_connection_ctrl',ev_lsp_osnr_monitor_reply)
                        elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                            self.send_event('Cross_domain_connection_ctrl',ev_lsp_osnr_monitor_reply)
                        else:
                            self.logger.info('Invalid traffic type! (South_bound_message_receive: _listening)')
                        #Database.Data.south_timer.remove(this_timer)
                        ready_remove.append(this_timer)
                        self.logger.debug('traffic %d OSNRR monitoring timeout (south).' % this_timer.traf_id)
                    else:
                        self.logger.info('Invalid south timer type! (South_bound_message_receive: _listening)')
            for timer in ready_remove:
                Database.Data.south_timer.remove(timer)
                
            ready_remove = []
            for this_timer in Database.Data.south_timer_no_response:
                if this_timer.end_time < time.time():
                    if this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        for this_lsp in this_timer.lsp_msg_list:
                            Database.Data.lsp_list.update_lsp_state(this_timer.traf_id, this_lsp.lsp_id, LSP_TEARDOWN_FAIL)    
                        #Database.Data.south_timer.remove(this_timer)
                        ready_remove.append(this_timer)
                        self.logger.debug('traffic %d teardown timeout (south_no_response).' % this_timer.traf_id)
                    else:
                        self.logger.info('Invalid south-no-reponse timer type! (South_bound_message_receive: _listening)')
            for timer in ready_remove:
                Database.Data.south_timer_no_response.remove(timer)
            
            hub.sleep(0.1)
            
                        
    @set_ev_cls(ofp_event.EventOFPTSetupConfigWSSReply,[CONFIG_DISPATCHER,MAIN_DISPATCHER,DEAD_DISPATCHER])
    def _handle_setup_reply(self,ev):
        #return
        #if this message does not have a timer in south_timer and south_timer_no_response
        #   discard this message
        #   print error information
        #else: 
        #   update timer
        #   if all the reply msgs are received in this timer
        #       if this timer in south_timer
        #           send events to other modules based on message type
        #       else:
        #           update lsp information
        #   delete this time 
        msg = ev.msg
        (datapath_id,message_id,result) = (msg.datapath_id,msg.message_id,msg.result)
        try:
            datapath=Database.Data.dpid2datapath[datapath_id]
        except:
            self.logger.critical('South_bound_message_receiving: _handle_setup_reply: Datapath not found!')
            for element in Database.Data.dpid2datapath:
                self.logger.info("dpid2datapath: %s " %element)
        self.logger.info('South_bound_message_receiving: _handle_setup_reply: RYU get a WSS_SETUP_CONFIG_REPLY from agent %s' % datapath.id)
        if (Database.Data.msg_in_south_timer(message_id) == False) and (Database.Data.msg_in_south_timer_no_response(message_id) == False):
            self.logger.warning('Cannot find this reply message in timer! (South_bound_message_receive: _handle_setup_reply)')
            return
        if Database.Data.msg_in_south_timer(message_id) == True:
            if result == SUCCESS:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_SETUP:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            for key,msg_id in tmp_lsp_msg_list.msgs.items():
                                if msg_id == message_id:
#                               	    self.logger.info('South_bound_message_receive module receives a success setup reply. msg_id = %d' % message_id)
                                    flag_find_msg = True
                                    del tmp_lsp_msg_list.msgs[key]
                                    #tmp_lsp_msg_list.msgs = filter(lambda msg: msg != message_id, tmp_lsp_msg_list.msgs)
                                    if not tmp_lsp_msg_list.msgs:
                                        #Database.Data.lsp_list.update_lsp_state(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, LSP_SETUP_SUCCESS)
                                        tmp_timer.lsp_msg_list.remove(tmp_lsp_msg_list)
                                        break
                        if tmp_timer.lsp_msg_list == []:
                            ev_lsp_setup_reply = Custom_event.South_LSPSetupReplyEvent()
                            ev_lsp_setup_reply.traf_id = tmp_timer.traf_id
                            ev_lsp_setup_reply.result = SUCCESS
                            tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                            if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                self.send_event('Intra_domain_connection_ctrl',ev_lsp_setup_reply)
                            elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                self.send_event('Cross_domain_connection_ctrl',ev_lsp_setup_reply)
                            else:
                                self.logger.info('Invalid traffic type! (South_bound_message_receive: _handle_setup_reply)')
                            Database.Data.south_timer.remove(tmp_timer)

            elif result == FAIL:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_SETUP:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            if message_id in tmp_lsp_msg_list.msgs:
#                                self.logger.debug('South_bound_message_receive module receives a fail setup reply. msg_id = %d' % message_id)
                                flag_find_msg = True
                                Database.Data.lsp_list.update_lsp_state(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, LSP_SETUP_FAIL)
                                ev_lsp_setup_reply = Custom_event.South_LSPSetupReplyEvent()
                                ev_lsp_setup_reply.traf_id = tmp_timer.traf_id
                                ev_lsp_setup_reply.result = FAIL
                                tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                                if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                    self.send_event('Intra_domain_connection_ctrl',ev_lsp_setup_reply)
                                elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                    self.send_event('Cross_domain_connection_ctrl',ev_lsp_setup_reply)
                                else:
                                    self.logger.info('Invalid traffic type! (South_bound_message_receive: _handle_setup_reply)')
                                Database.Data.south_timer.remove(tmp_timer)
                                break
                        if flag_find_msg == True:
                            break
            else:
                self.logger.info('Invalid LSP setup result! (South_bound_message_receive: _handle_setup_reply)')
        else:   #Database.Data.msg_in_south_timer_no_response(message_id) == True:
            self.logger.info('Wrong timer type, setup reply should not in a no-response timer! (South_bound_message_receive: _handle_setup_reply)')
            
    
    @set_ev_cls(ofp_event.EventOFPTTeardownConfigWSSReply,[CONFIG_DISPATCHER,MAIN_DISPATCHER,DEAD_DISPATCHER])
    def handle_teardown_reply(self,ev):
        msg = ev.msg
        (datapath_id,message_id,result) = (msg.datapath_id,msg.message_id,msg.result)
        try:
            datapath=Database.Data.dpid2datapath[int(datapath_id)]
        except:
            print('Bad things occur......Datapath not found...')
        self.logger.info('South_bound_message_receiving: handle_teardown_reply: RYU get a WSS_TEARDOWN_CONFIG_REPLY from agent %s' % datapath.id)
        if (Database.Data.msg_in_south_timer(message_id) == False) and (Database.Data.msg_in_south_timer_no_response(message_id) == False):
            self.logger.info('Cannot find this reply message in timer! (South_bound_message_receive: handle_teardown_reply)')
            return
        if Database.Data.msg_in_south_timer(message_id) == True:
            if result == SUCCESS:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            for key,msg_id in tmp_lsp_msg_list.msgs.items():
                                if msg_id == message_id:
                                    #self.logger.info('South_bound_message_receive module receives a success teardown reply. msg_id = %d' % message_id)
                                    flag_find_msg = True
                                    del tmp_lsp_msg_list.msgs[key]
                                    if not tmp_lsp_msg_list.msgs:
                                        tmp_timer.lsp_msg_list.remove(tmp_lsp_msg_list)
                                        break
                        if tmp_timer.lsp_msg_list == []:
                            ev_lsp_teardown_reply = Custom_event.South_LSPTeardownReplyEvent()
                            ev_lsp_teardown_reply.traf_id = tmp_timer.traf_id
                            ev_lsp_teardown_reply.result = SUCCESS
                            tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                            if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                self.send_event('Intra_domain_connection_ctrl',ev_lsp_teardown_reply)
                            elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                self.send_event('Cross_domain_connection_ctrl',ev_lsp_teardown_reply)
                            else:
                                self.logger.info('Invalid traffic type! (South_bound_message_receive: handle_teardown_reply)')
                            Database.Data.south_timer.remove(tmp_timer)


            elif result == FAIL:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            if message_id in tmp_lsp_msg_list.msgs:
                                self.logger.debug('South_bound_message_receive module receives a fail teardown reply. msg_id = %d' % message_id)
                                flag_find_msg = True
                                Database.Data.lsp_list.update_lsp_state(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, LSP_TEARDOWN_FAIL)
                                ev_lsp_teardown_reply = Custom_event.South_LSPTeardownReplyEvent()
                                ev_lsp_teardown_reply.traf_id = tmp_timer.traf_id
                                ev_lsp_teardown_reply.result = FAIL
                                tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                                if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                    self.send_event('Intra_domain_connection_ctrl',ev_lsp_teardown_reply)
                                elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                    self.send_event('Cross_domain_connection_ctrl',ev_lsp_teardown_reply)
                                else:
                                    self.logger.info('Invalid traffic type! (South_bound_message_receive: handle_teardown_reply)')
                                Database.Data.south_timer.remove(tmp_timer)
                                break
                            if flag_find_msg == True:
                                break
                            else:
                                self.logger.info('Invalid LSP teardown result! (South_bound_message_receive: handle_teardown_reply)')
        else:   #Database.Data.msg_in_south_timer_no_response(message_id) == True:
            if result == SUCCESS:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer_no_response:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            if message_id in tmp_lsp_msg_list.msgs:
                                self.logger.debug('South_bound_message_receive module receives a success teardown reply (no response). msg_id = %d' % message_id)
                                flag_find_msg = True
                                tmp_lsp_msg_list.msgs = filter(lambda msg: msg != message_id, tmp_lsp_msg_list.msgs)
                                if tmp_lsp_msg_list.msgs == []:
                                    Database.Data.lsp_list.update_lsp_state(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, LSP_TEARDOWN_SUCCESS)
                                    if Database.Data.update_phytopo(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, ACTION_TEARDOWN) == False:
                                        self.logger.info('Recover phytopo fail! (South_bound_message_receive: handle_teardown_reply)')
                                    tmp_timer.lsp_msg_list.remove(tmp_lsp_msg_list)
                                    break
                                if tmp_timer.lsp_msg_list == []:
                                    Database.Data.south_timer.remove(tmp_timer)
			    #for recording excusion time
                this_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                if this_traf == None:
                    self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
                    return
#			    with open('record_time.txt', 'a') as f:
#			        f.write('South teardown path time: (route_type = ')
#			        if this_traf.traf_state == TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS:
#				    f.write(str(ROUTE_WORKING)+')\n')
#			        else :
#				    f.write(str(ROUTE_REROUTE)+')\n')
#			        f.write(str(time.time() - Database.Data.south_teardown_path_time)+'\n')
                Database.Data.south_teardown_path_time = 0
            elif result == FAIL:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            if message_id in tmp_lsp_msg_list.msgs:
                                self.logger.debug('South_bound_message_receive module receives a fail teardown reply (no response). msg_id = %d' % message_id)
                                flag_find_msg = True
                                Database.Data.lsp_list.update_lsp_state(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, LSP_TEARDOWN_FAIL)
                                tmp_timer.lsp_msg_list.remove(tmp_lsp_msg_list)
                                break
                        if tmp_timer.lsp_msg_list == []:
                            Database.Data.south_timer.remove(tmp_timer)
                            break
                        if flag_find_msg == True:
                            break
 
