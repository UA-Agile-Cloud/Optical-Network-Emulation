"""
Inter-domain connection control

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/02/15

"""

from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from Common import *
import Database
import Custom_event
import logging
from Common import log_level

logging.basicConfig(level = log_level)

class Cross_domain_connection_ctrl(app_manager.RyuApp):
    
    _EVENTS =  [Custom_event.North_CrossDomainTrafficRequestEvent,
                Custom_event.North_CrossDomainTrafficTeardownRequestEvent,
                Custom_event.North_TrafficReplyEvent,
                Custom_event.North_TrafficTeardownReplyEvent,
                Custom_event.North_TrafficStateUpdateEvent,
                Custom_event.CrossDomainPathCompRequestEvent,
                Custom_event.CrossDomainPathCompReplyEvent,
                Custom_event.CrossDomainReroutingRequestEvent,
                Custom_event.CrossDomainReroutingReplyEvent,
                Custom_event.EastWest_SendTrafSetupRequestEvent,
                Custom_event.EastWest_ReceiveTrafSetupRequestEvent,
                Custom_event.EastWest_SendTrafSetupReplyEvent,
                Custom_event.EastWest_ReceiveTrafSetupReplyEvent,
                Custom_event.EastWest_SendTrafTeardownRequest,
                Custom_event.EastWest_ReceiveTrafTeardownRequest,
                Custom_event.EastWest_SendTrafTeardownReply,
                Custom_event.EastWest_ReceiveTrafTeardownReply,
                Custom_event.EastWest_SendTearDownPath,
                Custom_event.EastWest_ReceiveTearDownPath,
                Custom_event.EastWest_SendOSNRMonitoringRequestEvent,
                Custom_event.EastWest_ReceiveOSNRMonitoringRequestEvent,
                Custom_event.EastWest_SendOSNRMonitoringReplyEvent,
                Custom_event.EastWest_ReceiveOSNRMonitoringReplyEvent,
                Custom_event.South_LSPSetupRequestEvent,
                Custom_event.South_LSPSetupReplyEvent,
                Custom_event.South_OSNRMonitoringRequestEvent,
                Custom_event.South_OSNRMonitoringReplyEvent,
                Custom_event.IntraDomainReroutingRequest,
                Custom_event.IntraDomainReroutingReply]
                
    def __init__(self,*args,**kwargs):
        super(Cross_domain_connection_ctrl,self).__init__(*args,**kwargs)
        
    @set_ev_cls(Custom_event.North_CrossDomainTrafficRequestEvent)
    def _handle_cross_domain_traffic_request(self,ev):
        self.logger.debug('Cross_domain_connection_ctrl module receives North_CrossDomainTrafficRequestEvent')
        if (Database.Data.traf_list.insert_new_traf(ev) == False):   #insert new traffic information to database
            self.logger.critical('Insert traffic to database error! (Cross_domain_connection_ctrl: _handle_cross_domain_traffic_request)')
            return
	#self.logger.debug(Database.Data.controller_list.this_controller.controller_ip)
	#self.logger.debug(ev.domain_sequence[0])
        print ev.domain_sequence[0]
        if (Database.Data.controller_list.is_this_domain(ev.domain_sequence[0]) == False):      # this domain is not the source domian
            self.logger.debug('This domain is not the source domain of cross-domain traffic %d. Waiting...'%ev.traf_id)
            return
        else:     # this domain is the source domain
            cross_domain_traffic_pc_ev = Custom_event.CrossDomainPathCompRequestEvent()   # send custom event to trigger traffic setup
            cross_domain_traffic_pc_ev.traf_id = ev.traf_id
            self.send_event('Path_computation',cross_domain_traffic_pc_ev)
        
    @set_ev_cls(Custom_event.CrossDomainPathCompReplyEvent)
    def _handle_cross_domain_pc_reply(self,ev):
        #pass
        #if SUCCESS:
        #   update traffic state to TRAFFIC_SETUP
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        #elif FAIL:
        #   send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #   send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #else:
        #   error
        self.logger.debug('Cross_domain_connection_ctrl module receives CrossDomainPathCompReplyEvent')
	#for testing
	#self.logger.debug(Database.Data.lsp_list[0])
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP)
            lsp_setup_req_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_req_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', lsp_setup_req_ev)
        elif ev.result == FAIL:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
            traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.result = ev.result
            traf_reply_ev.traf_stage = traf.traf_stage
            traf_reply_ev.traf_state = traf.traf_state
            self.send_event('North_bound_message_send', traf_reply_ev)
            traf_tear_req_ev = Custom_event.EastWest_SendTrafTeardownRequest()
            traf_tear_req_ev.traf_id = ev.traf_id
            traf_tear_req_ev.traf_stage = traf.traf_stage
            traf_tear_req_ev.traf_state = traf.traf_state
            self.send_event('EastWest_message_send', traf_tear_req_ev)
        else:
            self.logger.info('Invalid cross-domain path computation result. (Cross_domain_connection_ctrl: _handle_cross_domain_pc_reply)')

    @set_ev_cls(Custom_event.South_LSPSetupReplyEvent)
    def _handle_lsp_setup_reply(self,ev):
        #pass need to be completed in the future
        #if SUCCESS: 
        #   update lsp state to LSP_SETUP_SUCCESS in database
        #   if this domain is the source domain:
        #       send Custom_event.EastWest_SendTrafSetupRequestEvent to 'EastWest_message_send'
        #       setup a timer
        #   elif this domain is the destination domain:
        #       update traffic state to TRAFFIC_SETUP_SUCCESS
        #       send Custom_event.EastWest_SendTrafSetupReplyEvent to 'EastWest_message_send'
        #   else:
        #       send Custom_event.EastWest_SendTrafSetupRequestEvent to 'EastWest_message_send'
        #elif FAIL:  
        #   update lsp state to LSP_SETUP_FAIL in database
        #   update traffic state to TRAFFIC_SETUP_FAIL
        #   if this domain is the source domain:     
        #       send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #       send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #       send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #   else:
        #       send Custom_event.EastWest_SendTrafSetupReplyEvent to 'EastWest_message_send'
        self.logger.debug('Cross_domain_connection_ctrl module receives South_LSPSetupReplyEvent')
	#self.logger.debug('ev.traf_id = %d' % ev.traf_id)
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        #unpro_lsp = Database.Data.lsp_list.get_unprovisioned_lsps(ev.traf_id)
        #if unpro_lsp == None:
         #   self.logger.critical('Cannot find traffic %d\'s unprovisioned lsps. (Cross_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
         #   return
        if ev.result == SUCCESS:
            #for lsp_id in unpro_lsp:
            #    Database.Data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_SUCCESS)
            if this_traf.traf_state == TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS:
                osnr_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
                osnr_req_ev.traf_id = ev.traf_id
                osnr_req_ev.route_type = ROUTE_INTRA_REROUTE
		hub.sleep(1)
                self.send_event('Monitoring', osnr_req_ev)
            else:
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    traf_setup_req_ev = Custom_event.EastWest_SendTrafSetupRequestEvent()
                    traf_setup_req_ev.traf_id = ev.traf_id
                    traf_setup_req_ev.traf_stage = this_traf.traf_stage
                    self.send_event('EastWest_message_send', traf_setup_req_ev)
                    # Moved to EastWest_message_send
                    #new_timer = Timer()    
                    #new_timer.traf_id = ev.traf_id
                    #new_timer.timer_type = TIMER_TRAFFIC_SETUP
                    #new_timer.end_time = time.time() + EASTWEST_WAITING_TIME
                    #eastwest_timer.append(new_timer)
                elif Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) == True:
                    Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP_SUCCESS)
                    traf_setup_reply_ev = Custom_event.EastWest_SendTrafSetupReplyEvent()
                    traf_setup_reply_ev.traf_id = ev.traf_id
                    traf_setup_reply_ev.traf_stage = this_traf.traf_stage
                    traf_setup_reply_ev.traf_state = this_traf.traf_state
                    traf_setup_reply_ev.result = ev.result
                    self.send_event('EastWest_message_send', traf_setup_reply_ev)
                else:
                    traf_setup_req_ev = Custom_event.EastWest_SendTrafSetupRequestEvent()
                    traf_setup_req_ev.traf_id = ev.traf_id
                    traf_setup_req_ev.traf_stage = this_traf.traf_stage
                    self.send('EastWest_message_send', traf_setup_req_ev)
        elif ev.result == FAIL: # need to be completed in the future
            self.logger.info('LSP setup fail. (Cross_domain_connection_ctrl: _handle_lsp_setup_reply)')
        else:   # ev.result == TIMEOUT_TRAF_SETUP or TIMEOUT_REROUTING 
            self.logger.info('LSP setup timeout. (Cross_domain_connection_ctrl: _handle_lsp_setup_reply)')
        
        
    @set_ev_cls(Custom_event.EastWest_ReceiveTrafSetupRequestEvent)
    def _handle_receive_traffic_setup_request(self,ev): 
        #pass
        #if ev.traf_stage is right
        #   update traffic state to TRAFFIC_SETUP
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        self.logger.debug('Cross_domain_connection_ctrl module receives EastWest_ReceiveTrafSetupRequestEvent')
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        if ev.traf_stage == this_traf.traf_stage:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP)
            lsp_setup_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', lsp_setup_ev)
        else:
            self.logger.info('Invalid traffic stage! (Intra_domain_connection_ctrl: _handle_receive_traffic_setup_request)')
    
    @set_ev_cls(Custom_event.EastWest_ReceiveTrafSetupReplyEvent)
    def _handle_receive_traffic_setup_reply(self,ev): 
        #pass
        #update traffic state to ev.traf_state
        #if this domain is not the source domain:
        #   send Custom_event.EastWest_SendTrafSetupReplyEvent to 'EastWest_message_send'
        #else:
        #   send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #   if ev.traf_state == TRAFFIC_SETUP_FAIL
        #       send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #       send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #   elif ev.traf_state == TRAFFIC_SETUP_SUCCESS:
        #       if ev.traf_stage is TRAFFIC_WORKING:
        #           send Custom_event.South_OSNRMonitoringRequest to 'Monitoring'
        #       elif ev.traf_stage is TRAFFIC_REROUTING:
        #           send Custom_event.EastWest_SendTearDownPath to 'EastWest_message_send' to teardown working(backup) path
        #           send Custom_event.South_OSNRMonitoringRequest to 'Monitoring'
        #       else:
        #           error
        #   else:
        #       error
        self.logger.debug('Cross_domain_connection_ctrl module receives EastWest_ReceiveTrafSetupReplyEvent')
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_receive_traffic_setup_reply)' % ev.traf_id)
            return
        if this_traf.traf_stage == ev.traf_stage:
            Database.Data.traf_list.update_traf_state(ev.traf_id, ev.traf_state)
        if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) != True:
            traf_setup_reply_ev = Custom_event.EastWest_SendTrafSetupReplyEvent()
            traf_setup_reply_ev.traf_id = ev.traf_id
            traf_setup_reply_ev.traf_stage = ev.traf_stage
            traf_setup_reply_ev.traf_state = ev.traf_state
            traf_setup_reply_ev.result = ev.result
            self.send_event('EastWest_message_send', traf_setup_reply_ev)
        else:
	    if ev.traf_stage == TRAFFIC_WORKING:
                traf_reply_ev = Custom_event.North_TrafficReplyEvent()
                traf_reply_ev.traf_id = ev.traf_id
                traf_reply_ev.traf_stage = ev.traf_stage
                traf_reply_ev.traf_state = ev.traf_state
                traf_reply_ev.result = ev.result
                self.send_event('North_bound_message_send', traf_reply_ev)
	    elif ev.traf_stage == TRAFFIC_REROUTING:
		traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
		traf_update_ev.traf_id = ev.traf_id
		traf_update_ev.traf_stage = ev.traf_stage
		traf_update_ev.traf_state = ev.traf_state
		self.send_event('North_bound_message_send', traf_update_ev)
	    else:
		pass	#complete later
            
            if ev.traf_state == TRAFFIC_SETUP_FAIL:
                traf_tear_req_ev = Custom_event.EastWest_SendTrafTeardownRequest()
                traf_tear_req_ev.traf_id = ev.traf_id
                traf_tear_req_ev.traf_stage = ev.traf_stage
                traf_tear_req_ev.traf_state = ev.traf_state
                self.send_event('EastWest_message_send', traf_tear_req_ev)
                lsp_tear_req_ev = Custom_event.South_LSPTeardownRequestEvent()
                lsp_tear_req_ev.traf_id = ev.traf_id
                self.send_event('Intra_domain_connection_ctrl', South_LSPTeardownRequestEvent)
            elif ev.traf_state == TRAFFIC_SETUP_SUCCESS:
                if ev.traf_stage == TRAFFIC_WORKING:
                    sonr_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
                    sonr_req_ev.traf_id = ev.traf_id
                    sonr_req_ev.route_type = ROUTE_WORKING
		    hub.sleep(1)
                    self.send_event('Monitoring', sonr_req_ev)
                elif ev.traf_stage == TRAFFIC_REROUTING:
                    sonr_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
                    sonr_req_ev.traf_id = ev.traf_id
                    sonr_req_ev.route_type = ROUTE_REROUTE
		    hub.sleep(1)
                    self.send_event('Monitoring', sonr_req_ev)
		    hub.sleep(0.01)
                    tear_path_ev = Custom_event.EastWest_SendTearDownPath()
                    tear_path_ev.traf_id = ev.traf_id
                    tear_path_ev.route_type = ROUTE_WORKING
                    self.send_event('EastWest_message_send', tear_path_ev)
                    if this_traf.prot_type == TRAFFIC_1PLUS1_PROTECTION:
                        tear_path_ev = Custom_event.EastWest_SendTearDownPath()
                        tear_path_ev.traf_id = ev.traf_id
                        tear_path_ev.route_type = ROUTE_BACKUP
                        self.send_event('EastWest_message_send', tear_path_ev)
                else:
                    self.logger.info('Invalid traffic stage. (Cross_domain_connection_ctrl: _handle_receive_traffic_setup_reply)')
            else:
                self.logger.info('Invalid traffic state. (Cross_domain_connection_ctrl: _handle_receive_traffic_setup_reply)')    
                
    @set_ev_cls(Custom_event.South_OSNRMonitoringReplyEvent)
    def _handle_OSNR_monitoring_reply(self,ev):
        pass
        #if ev.result is not SUCCESS:
        #   if this domain is not the source domain:
        #       send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
        #   else:
        #       print OSNR monitoring error or timeout
        #else:
        #   if is_OSNR_all_good == True:
        #       if this domain is not the destination domain:
        #           send EastWest_SendOSNRMonitoringRequestEvent to 'EastWest_message_send' 
        #       else:
        #           send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
        #       return
        #   traffic on working path:
        #   if impairment at this domain
        #       if traffic protection type is TRAFFIC_REROUTING_RESTORATION:
        #           update traf_state to TRAFFIC_INTRA_DOMAIN_REROUTE
        #           update traff_stage to TRAFFIC_REROUTING
        #           send Custom_event.IntraDomainReroutingRequest to Path_computation
        #       elif traffic protection type is TRAFFIC_1PLUS1_PROTECTION
        #           switch to backup path
        #           update traf_state to TRAFFIC_ON_BACKUP_PATH:
        #           send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #           trigger backup path OSNR monitering
        #       elif traffic protection type is TRAFFIC_NO_PROTECTION:
        #           update traffic state to TRAFFIC_INACTIVE
        #           if this domain is the source domain:
        #               send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #           else:
        #               send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
        #   else: 
        #       send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' (is_inter_domain_impairment == True)
        #   traffic on rerouting path:
        #   update traffic state to TRAFFIC_INACTIVE
        #   if this domain is the source domain:
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #   else:
        #       send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
        self.logger.debug('Cross_domain_connection_ctrl module receives South_OSNRMonitoringReplyEvent')
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
            return
        if ev.result != SUCCESS:
            #need to be completed later
            self.logger.info('OSNR monitoring fail. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
        else:
            if ev.is_OSNR_all_good == True:
                if this_traf.traf_stage == TRAFFIC_WORKING:
                    route_type = ROUTE_WORKING
                elif (this_traf.traf_stage == TRAFFIC_REROUTING) and (this_traf.traf_state == TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS):
                    route_type = ROUTE_INTRA_REROUTE
		elif this_traf.traf_stage == TRAFFIC_REROUTING:
		    route_type = ROUTE_REROUTE
                else:
                    self.logger.critical('Invalid traffic stage. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
                    return
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) != True:
                    osnr_req_ev = Custom_event.EastWest_SendOSNRMonitoringRequestEvent()
                    osnr_req_ev.traf_id = ev.traf_id
                    osnr_req_ev.route_type = route_type
                    self.send_event('EastWest_message_send', osnr_req_ev)
                else:
                    osnr_reply_ev = Custom_event.EastWest_SendOSNRMonitoringReplyEvent()
                    osnr_reply_ev.traf_id = ev.traf_id
                    osnr_reply_ev.route_type = route_type
                    osnr_reply_ev.result = ev.result
                    if (ev.is_OSNR_all_good == False) and (is_impairtment_at_this_domain == False):
                        osnr_reply_ev.is_inter_domain_impairment = True
                    else:
                        osnr_reply_ev.is_inter_domain_impairment = False
                    osnr_reply_ev.traf_stage = this_traf.traf_stage
                    osnr_reply_ev.traf_state = this_traf.traf_state
                    self.send_event('EastWest_message_send', osnr_reply_ev)
                return
            if this_traf.traf_stage == TRAFFIC_WORKING:
                if ev.is_impairtment_at_this_domain == True:
                    if this_traf.prot_type == TRAFFIC_REROUTING_RESTORATION:
                        Database.Data.traf_list.update_traf_stage(ev.traf_id, TRAFFIC_REROUTING)
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE)
                        intra_domain_reroute_ev = Custom_event.IntraDomainReroutingRequest()
                        intra_domain_reroute_ev.traf_id = ev.traf_id
                        self.send_event('Path_computation', intra_domain_reroute_ev)
                    elif this_traf.prot_type == TRAFFIC_1PLUS1_PROTECTION:
                        # need to be completed later
                        pass    
                    elif this_traf.prot_type == TRAFFIC_NO_PROTECTION:
                        # need to be completed later
                        pass
                    else:
                        self.logger.warning('Invalid traffic protection type. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
                else:
		    if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) != True:
                        #send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' (is_inter_domain_impairment == True)
                        osnr_reply_ev = Custom_event.EastWest_SendOSNRMonitoringReplyEvent()
                        osnr_reply_ev.traf_id = ev.traf_id
                        osnr_reply_ev.route_type = ev.route_type
                        osnr_reply_ev.result = ev.result
                        osnr_reply_ev.is_inter_domain_impairment = True
                        osnr_reply_ev.traf_stage = this_traf.traf_stage
                        osnr_reply_ev.traf_state = this_traf.traf_state
                        self.send_event('EastWest_message_send', osnr_reply_ev)
		    else:
			self.logger.critical('Attention! OSNR at the sending point is not good!')
            elif this_traf.traf_stage == TRAFFIC_REROUTING:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INACTIVE)
                if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                    #send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
                    traf_state_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                    traf_state_update_ev.traf_id = ev.traf_id
                    traf_state_update_ev.traf_stage = this_traf.traf_stage
                    traf_state_update_ev.traf_state = None
                    self.send_event('North_bound_message_send', traf_state_update_ev)
		    self.logger.info('Traffic inactive')
                else:
                    #send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
                    osnr_reply_ev = Custom_event.EastWest_SendOSNRMonitoringReplyEvent()
                    osnr_reply_ev.traf_id = ev.traf_id
                    osnr_reply_ev.route_type = ev.route_type
                    osnr_reply_ev.result = ev.result
                    osnr_reply_ev.is_inter_domain_impairment = None
                    osnr_reply_ev.traf_stage = TRAFFIC_INACTIVE
                    osnr_reply_ev.traf_state = this_traf.traf_state
                    self.send_event('EastWest_message_send', osnr_reply_ev)
            else:
                self.logger.info('Invalid traffic stage. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
        
    @set_ev_cls(Custom_event.EastWest_ReceiveOSNRMonitoringRequestEvent)
    def _handle_cross_domain_OSNR_monitoring_request(self,ev):
        #pass
        #send Custom_event.South_OSNRMonitoringRequest to 'Monitoring'
        self.logger.debug('Cross_domain_connection_ctrl module receives EastWest_ReceiveOSNRMonitoringRequestEvent')
	#hub.sleep(1)
        osnr_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
        osnr_req_ev.traf_id = ev.traf_id
        osnr_req_ev.route_type = ev.route_type
        self.send_event('Monitoring', osnr_req_ev)
        
    @set_ev_cls(Custom_event.EastWest_ReceiveOSNRMonitoringReplyEvent)
    def _handle_cross_domain_OSNR_monitoring_reply(self,ev):
        #pass
        #if ev.result == SUCCESS
        #   if traffic stage at this domain is TRAFFIC_REROUTING
        #       update ev.traf_stage and ev.traf_state as those at this domain
        #if this domain is not the source domain:
        #   send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send' 
        #else:
        #   if ev.result != SUCCESS
        #       print OSNR monitoring error or timeout
        #   else:
        #       if traf_stage is working:
        #           if ev.is_inter_domain_impairment == True or (ev.traf_stage == TRAFFIC_REROUTING and ev.traf_state != TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS)
        #               send Custom_event.CrossDomainReroutingRequestEvent to 'Path_computation'
        #           else:
        #               print osnr good
        #               update traffic stage and state
        #               send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #       elif traf_stage is rerouting:
        #           if ev.traf_stage == TRAFFIC_INACTIVE:
        #               update traffic stage
        #               send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #               send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send' if necessary
        #           else:
        #               print osnr good
        self.logger.debug('Cross_domain_connection_ctrl module receives EastWest_ReceiveOSNRMonitoringReplyEvent')
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
            return
        if ev.result == SUCCESS:
            if (this_traf.traf_stage == TRAFFIC_REROUTING) and (this_traf.traf_state != TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS):
                tmp_traf_stage = this_traf.traf_stage
                tmp_traf_state = this_traf.traf_state
            else:
                tmp_traf_stage = ev.traf_stage
                tmp_traf_state = ev.traf_state
        if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) != True:
            osnr_reply_ev = Custom_event.EastWest_SendOSNRMonitoringReplyEvent()
            osnr_reply_ev.traf_id = ev.traf_id
            osnr_reply_ev.route_type = ev.route_type
            osnr_reply_ev.result = ev.result
            osnr_reply_ev.is_inter_domain_impairment = ev.is_inter_domain_impairment
            osnr_reply_ev.traf_stage = tmp_traf_stage
            osnr_reply_ev.traf_state = tmp_traf_state
        else:
            if ev.result != SUCCESS:
                self.logger.info('OSNR monitoring fail! (Cross_domain_connection_ctrl: _handle_cross_domain_OSNR_monitoring_reply)')
            else:
                if this_traf.traf_stage == TRAFFIC_WORKING:
                    if (ev.is_inter_domain_impairment == True) or ((ev.traf_stage == TRAFFIC_REROUTING) and (ev.traf_state != TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS)) or (ev.traf_stage == TRAFFIC_INACTIVE):
                        cross_domain_reroute_req_ev = Custom_event.CrossDomainReroutingRequestEvent()
                        cross_domain_reroute_req_ev.traf_id = ev.traf_id
                        self.send_event('Path_computation', cross_domain_reroute_req_ev)
                    else:
                        self.logger.info('OSNR for traffic %d is good (working)!' % ev.traf_id)
                        Database.Data.traf_list.update_traf_stage(ev.traf_id, ev.traf_stage)
                        Database.Data.traf_list.update_traf_state(ev.traf_id, ev.traf_state)
                        #send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
                        traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                        traf_update_ev.traf_id = ev.traf_id
                        traf_update_ev.traf_stage = ev.traf_stage
                        traf_update_ev.traf_state = ev.traf_state
                        self.send_event('North_bound_message_send', traf_update_ev)
                elif this_traf.traf_stage == TRAFFIC_REROUTING:
                    if ev.traf_stage == TRAFFIC_INACTIVE:
                        Database.Data.traf_list.update_traf_stage(ev.traf_id, ev.traf_stage)
			self.logger.info('Traffic %d inactive.' % ev.traf_id)
                        #send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
                        traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                        traf_update_ev.traf_id = ev.traf_id
                        traf_update_ev.traf_stage = ev.traf_stage
                        traf_update_ev.traf_state = ev.traf_state
                        self.send_event('North_bound_message_send', traf_update_ev)
                        #send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send' in the future
                    else:
                        self.logger.info('OSNR for traffic %d is good (rerouting)!' % ev.traf_id)
                else:
                    self.logger.info('Traffic in inactive. (Cross_domain_connection_ctrl: _handle_cross_domain_OSNR_monitoring_reply)')
    
    
    @set_ev_cls(Custom_event.IntraDomainReroutingReply)
    def _handle_intra_domain_rerouting_reply(self,ev):
        pass
        #if SUCCESS:
        #   update traf_state to TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        #elif FAIL:
        #   update traf_state to TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL 
        #   if this domain is the source domain:
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #       send Custom_event.CrossDomainReroutingRequestEvent to 'Path_computation'
        #   else:
        #       send EastWest_SendOSNRMonitoringReplyEvent to 'EastWest_message_send'
        #else:
        #   error   
        self.logger.debug('Cross_domain_connection_ctrl module receives IntraDomainReroutingReply')
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
            return
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS)
            lsp_setup_req_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_req_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', lsp_setup_req_ev)
        elif ev.result == FAIL:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL)
            if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True:
                traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                traf_update_ev.traf_id = ev.traf_id
                traf_update_ev.traf_stage = this_traf.traf_stage
                traf_update_ev.traf_state = this_traf.traf_state
                self.send_event('North_bound_message_send', traf_update_ev)
                cross_domain_reroute_req_ev = Custom_event.CrossDomainReroutingRequestEvent()
                cross_domain_reroute_req_ev.traf_id = ev.traf_id
                self.send_event('Path_computation', cross_domain_reroute_req_ev)
            else:
                osnr_reply_ev = Custom_event.EastWest_SendOSNRMonitoringReplyEvent()
                osnr_reply_ev.traf_id = ev.traf_id
                osnr_reply_ev.route_type = ROUTE_INTRA_REROUTE
                osnr_reply_ev.result = ev.result
                osnr_reply_ev.is_inter_domain_impairment = None 
                osnr_reply_ev.traf_stage = this_traf.traf_stage
                osnr_reply_ev.traf_state = this_traf.traf_state
                self.send_event('EastWest_message_send', osnr_reply_ev)
        else:
            self.logger.info('Invalid intra-domain rerouting reply result. (Cross_domain_connection_ctrl: _handle_intra_domain_rerouting_reply)')
                
    
    
    @set_ev_cls(Custom_event.CrossDomainReroutingReplyEvent)
    def _handle_cross_domain_rerouting_reply(self,ev):
        pass
        #if result is SUCCESS:
        #   update traffic state to TRAFFIC_SETUP
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        #elif FAIL:
        #   send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #   send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #else:
        #   error 
        self.logger.debug('Cross_domain_connection_ctrl module receives CrossDomainReroutingReplyEvent')
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP)
            lsp_setup_req_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_req_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', lsp_setup_req_ev)
        elif ev.result == FAIL:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
            traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.result = ev.result
            traf_reply_ev.traf_stage = traf.traf_stage
            traf_reply_ev.traf_state = traf.traf_state
            self.send_event('North_bound_message_send', traf_reply_ev)
            traf_tear_req_ev = Custom_event.EastWest_SendTrafTeardownRequest()
            traf_tear_req_ev.traf_id = ev.traf_id
            traf_tear_req_ev.traf_stage = traf.traf_stage
            traf_tear_req_ev.traf_state = traf.traf_state
            self.send_event('EastWest_message_send', traf_tear_req_ev)
        else:
            self.logger.info('Invalid cross-domain path computation result. (Cross_domain_connection_ctrl: _handle_cross_domain_pc_reply)')

        
        
    @set_ev_cls(Custom_event.EastWest_ReceiveTrafTeardownRequest)
    def _handle_receive_traffic_teardown_request(self,ev): 
        #pass
        #if this domain is not the destination domain:
        #   send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_receive_traffic_teardown_request)' % ev.traf_id)
            return
        if (Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) == False):
            traf_tear_ev = Custom_event.EastWest_SendTrafTeardownRequest()
            traf_tear_ev.traf_id = ev.traf_id
            traf_tear_ev.traf_stage = ev.traf_stage
            traf_tear_ev.traf_state = ev.traf_state
            self.send_event('EastWest_message_send', traf_tear_ev)

        flag = False
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id and this_lsp.lsp_state != LSP_UNPROVISIONED:
                flage = True
        if flag:
            lsp_tear_ev = Custom_event.South_LSPTeardownRequestEvent()
            lsp_tear_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', lsp_tear_ev)
        else:   # traffic was not successfully setup in this domain 
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_TEARDOWN_SUCCESS)
            if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) == True:
                #send Custom_event.EastWest_SendTrafTeardownReply to 'EastWest_message_send'
                ew_tear_traf_reply_ev = Custom_event.EastWest_SendTrafTeardownReply()
                ew_tear_traf_reply_ev.traf_id =ev.traf_id
                ew_tear_traf_reply_ev.result = SUCCESS
                self.send_event('EastWest_message_send', ew_tear_traf_reply_ev)
                #delete traffic, lsp informations
                ready_remove = list()
                for this_lsp in Database.Data.lsp_list.lsp_list:
                    if this_lsp.traf_id == ev.traf_id:
                        ready_remove.append(this_lsp)
                for lsp in ready_remove:
                    Database.Data.lsp_list.lsp_list.remove(lsp)
                Database.Data.traf_list.remove(this_traf)
                
        
    @set_ev_cls(Custom_event.EastWest_ReceiveTrafTeardownReply)
    def _handle_receive_traffic_teardown_reply(self,ev): 
        pass
        #if traffic state at this domain is TRAFFIC_TEARDOWN_FAIL
        #   update ev.result to be FAIL
        #if this domain is not the source domain:
        #   send Custom_event.EastWest_SendTrafTeardownReply to 'EastWest_message_send'
        #else:
        #   if this teardown is launched by central controller:
        #       send Custom_event.North_TrafficTeardownReplyEvent to 'North_bound_message_send'
        #   else:
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #delete traffic, lsp informations
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_receive_traffic_teardown_reply)' % ev.traf_id)
            return
        if this_traf.traf_state == TRAFFIC_TEARDOWN_FAIL:
            tmp_result = FAIL
        else:
            tmp_result = ev.result
        if (Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == False):   # not the source domain
            ew_traf_tear_reply_ev = Custom_event.EastWest_SendTrafTeardownReply()
            ew_traf_tear_reply_ev.traf_id = ev.traf_id
            ew_traf_tear_reply_ev.result = tmp_result
            self.send_event('EastWest_message_send', ew_traf_tear_reply_ev)
        else:   # source domain
            find_timer = False
            for this_timer in Database.Data.north_timer:
                if this_timer.traf_id == ev.traf_id and this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                    find_timer = True
                    break
            if find_timer:
                n_traf_tear_reply = Custom_event.North_TrafficTeardownReplyEvent()
                n_traf_tear_reply.traf_id = ev.trad_id
                n_traf_tear_reply.result = tmp_result
                n_traf_tear_reply.traf_stage = this_traf.traf_stage
                if tmp_result == SUCCESS:
                    n_traf_tear_reply.traf_state = TRAFFIC_TEARDOWN_SUCCESS
                else:
                    n_traf_tear_reply.traf_state = TRAFFIC_TEARDOWN_FAIL
                self.send_event('North_bound_message_send', n_traf_tear_reply)
            else:
                n_traf_tear_update = Custom_event.North_TrafficStateUpdateEvent()
                n_traf_tear_update.traf_id = ev.trad_id
                n_traf_tear_update.traf_stage = this_traf.traf_stage
                if tmp_result == SUCCESS:
                    n_traf_tear_update.traf_state = TRAFFIC_TEARDOWN_SUCCESS
                else:
                    n_traf_tear_update.traf_state = TRAFFIC_TEARDOWN_FAIL
                self.send_event('North_bound_message_send', n_traf_tear_update)
                
        ready_remove = list()
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id:
                ready_remove.append(this_lsp)
        for lsp in ready_remove:
            Database.Data.lsp_list.lsp_list.remove(lsp)
        Database.Data.traf_list.remove(this_traf)
    
    @set_ev_cls(Custom_event.EastWest_ReceiveTearDownPath)
    def _handle_receive_teardown_path_request(self,ev): 
        pass
        #if this domain is not the destination domain:
        #   send Custom_event.EastWest_SendTearDownPath to 'EastWest_message_send'
        #send Custom_event.EastWest_ReceiveTearDownPath to 'Intra_domain_connection_ctrl'
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_receive_teardown_path_request)' % ev.traf_id)
            return
        if (Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) == False):   # not the destination domain
            ew_tear_path_ev = Custom_event.EastWest_SendTearDownPath()
            ew_tear_path_ev.traf_id = ev.traf_id
            ew_tear_path_ev.route_type = ev.route_type
            self.send('EastWest_message_send', ew_tear_path_ev)
        ew_r_tear_path_ev = Custom_event.EastWest_ReceiveTearDownPath()
        ew_r_tear_path_ev.traf_id = ev.traf_id
        ew_r_tear_path_ev.route_type = ev.route_type
        self.send('Intra_domain_connection_ctrl', ew_r_tear_path_ev)
        
              
    @set_ev_cls(Custom_event.North_CrossDomainTrafficTeardownRequestEvent)
    def _handle_cross_domain_traffic_teardown_request(self,ev):
        pass
        #if this domain is the source domain:
        #   send Custom_event.EastWest_SendTrafTeardownRequest to 'EastWest_message_send'
        #   send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #else:
        #   do nothing
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_cross_domain_traffic_teardown_request)' % ev.traf_id)
            return
        if (Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[0]) == True):   # source domain
            ew_traf_tear_ev = Custom_event.EastWest_SendTrafTeardownRequest()
            ew_traf_tear_ev.traf_id = ev.traf_id
            ew_traf_tear_ev.traf_stage = this_traf.traf_stage
            ew_traf_tear_ev.traf_state = this_traf.traf_state
            self.send_event('EastWest_message_send', ew_traf_tear_ev)
            s_lsp_tear_ev = Custom_event.South_LSPTeardownRequestEvent()
            s_lsp_tear_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl', s_lsp_tear_ev)
        


    
