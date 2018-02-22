"""
Intra-domain connection control

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/02/13

"""

import sys
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import time
from Common import *
import Database
import Custom_event
import logging
from Common import log_level
import virtual_port_mapping
import os
from ryu.lib import dpid as dpid_lib
import json
from glob import glob
from time import sleep

logging.basicConfig(level = log_level)

class Intra_domain_connection_ctrl(app_manager.RyuApp):
    
    _EVENTS =  [Custom_event.North_IntraDomainTrafficRequestEvent,
                Custom_event.North_IntraDomainTrafficTeardownRequestEvent,
                Custom_event.North_TrafficStateUpdateEvent,
                Custom_event.North_TrafficReplyEvent,
                Custom_event.North_TrafficTeardownReplyEvent,
                Custom_event.IntraDomainPathCompRequestEvent,
                Custom_event.IntraDomainPathCompReplyEvent,
                Custom_event.South_LSPSetupRequestEvent,
                Custom_event.South_LSPSetupReplyEvent,
                Custom_event.South_OSNRMonitoringRequestEvent,
                Custom_event.South_OSNRMonitoringReplyEvent,
                Custom_event.IntraDomainReroutingRequest,
                Custom_event.IntraDomainReroutingReply,
                Custom_event.EastWest_ReceiveTearDownPath,
		#for testng
		Custom_event.South_LSPSetupReplyEvent]
                
    def __init__(self,*args,**kwargs):
        super(Intra_domain_connection_ctrl, self).__init__(*args,**kwargs)
        #self.virtual_port_mapping = virtual_port_mapping.main()
        self.rules_path = 'json_rules/2'
        self.rules_path_teardown = 'json_rules/teardown/2'
                    
    @set_ev_cls(Custom_event.North_IntraDomainTrafficRequestEvent)
    def _handle_intra_domain_traffic_request(self,ev):
        if (Database.Data.traf_list.insert_new_traf(ev) == False):   #insert new traffic information to database
            self.logger.info('Insert traffic to database error! (Intra_domain_connection_ctrl: _handle_intra_domain_traffic_request)')
        intra_domain_traffic_pc_ev = Custom_event.IntraDomainPathCompRequestEvent()   # send custom event to trigger traffic setup
        intra_domain_traffic_pc_ev.traf_id = ev.traf_id
        self.send_event('Path_computation',intra_domain_traffic_pc_ev)

    @set_ev_cls(Custom_event.IntraDomainPathCompReplyEvent)
    def _handle_intra_domain_pc_reply(self,ev):
        #pass
        #if SUCCESS: 
        #   update traffic state: Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        #elif FAIL:
        #   update traffic state: Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL) 
        #   send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #   delete traffic and lsp information in database
        #else:
        #   error
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
            lsp_setup_req_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_req_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl',lsp_setup_req_ev)
        elif ev.result == FAIL:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.result = FAIL
            for this_traf in Database.Data.traf_list.traf_list:
                if this_traf.traf_id == ev_traf_id:
                    traf_reply_ev.traf_stage = this_traf.traf_stage
                    traf_reply_ev.traf_state = this_traf.traf_state
                    break
            self.send_event('North_bound_message_send',traf_reply_ev)
            Database.Data.traf_list.traf_list = filter(lambda traf: traf.traf_id != ev.traf_id, Database.Data.traf_list.traf_list)  
            Database.Data.lsp_list.lsp_list = filter(lambda lsp: lsp.traf_id != ev.traf_id, Database.Data.lsp_list.lsp_list)  
        else:
            self.logger.info('Invalid intra-domain path computatoin reply result! (Intra_domain_connection_ctrl: _handle_intra_domain_pc_reply)')
                

    @set_ev_cls(Custom_event.South_LSPSetupRequestEvent)
    def _handle_lsp_setup_request(self,ev):
        i = 0
        files_list = glob(os.path.join(self.rules_path, '*.json'))
        for filename in sorted(files_list):
            f = open(filename,"r")
            entry = f.readline()
            #print(entry)
            self.setup_config_wss_request_handler(entry)
            sleep(0.01)
                                                                                              
        
    @set_ev_cls(Custom_event.South_LSPSetupReplyEvent)
    def _handle_lsp_setup_reply(self,ev):
        #pass
        #lsp is working or protection:
        #if SUCCESS:
        #   update traffic state to TRAFFIC_SETUP_SUCCESS
        #   update lsp state to LSP_SETUP_SUCCESS
        #   send Custom event.South_OSNRMonitoringRequest to 'Monitoring'
        #elif FAIL or TIMEOUT:
        #   update traffic state to TRAFFIC_SETUP_FAIL
        #   update lsp state to LSP_SETUP_FAIL
        #   send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #lsp is rerouting:
        #if SUCCESS:
        #   update traffic state to TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS
        #   update lsp state to LSP_SETUP_SUCCESS
        #   send Custom_event.South_OSNRMonitoringRequest to 'Monitoring'
        #   tear down old lsp
        #elif FAIL or TIMEOUT:
        #   update traffic state to TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL
        #   update lsp state to LSP_SETUP_FAIL
        #   send Custom_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        this_traf = Database.data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.info('Cannot find traffic %d. (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        unpro_lsp = Database.data.lsp_list.get_unprovisioned_lsps(ev.traf_id)
        if unpro_lsp == None:
            self.logger.info('Cannot find traffic %d\'s unprovisioned lsps. (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        if this_traf.traf_stage == TRAFFIC_WORKING:
            if ev.result == SUCCESS:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP_SUCCESS) 
                for lsp_id in range(len(unpro_lsp)):
                    Database.data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_SUCCESS)
                osnr_monitor_req_ev = Custom_event.South_OSNRMonitoringRequest()
                osnr_monitor_req_ev.traf_id = ev.traf_id
                osnr_monitor_req_ev.route_type = ROUTE_WORKING
                self.send_event('Monitoring',osnr_monitor_req_ev)
            elif ev.result == FAIL or ev.result == TIMEOUT_TRAF_SETUP:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP_FAIL)
                for lsp_id in range(len(unpro_lsp)):
                    Database.data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_FAIL) 
                lsp_teardown_req_ev = Custom_event.South_LSPTeardownRequestEvent()
                lsp_teardown_req_ev.traf_id = ev.traf_id
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
            else:
                self.logger.info('Invalid lsp setup result! (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)')
                return
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.result = ev.result
            traf_reply_ev.traf_stage = this_traf.traf_stage
            traf_reply_ev.traf_state = this_traf.traf_state
            self.send_event('North_bound_message_send',traf_reply_ev)
        elif this_traf.traf_stage == TRAFFIC_REROUTING:
            if ev.result == SUCCESS:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS) 
                for lsp_id in range(len(unpro_lsp)):
                    Database.data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_SUCCESS)
                osnr_monitor_req_ev = Custom_event.South_OSNRMonitoringRequest()
                osnr_monitor_req_ev.traf_id = ev.traf_id
                osnr_monitor_req_ev.route_type = ROUTE_REROUTE
                self.send_event('Monitoring',osnr_monitor_req_ev)
                lsp_teardown_req_ev = Custom_event.EastWest_ReceiveTearDownPath()
                lsp_teardown_req_ev.traf_id = ev.traf_id
                lsp_teardown_req_ev.route_type = ROUTE_WORKING
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
                if this_traf.prot_type == TRAFFIC_1PLUS1_PROTECTION:
                    lsp_teardown_req_ev = Custom_event.EastWest_ReceiveTearDownPath()
                    lsp_teardown_req_ev.traf_id = ev.traf_id
                    lsp_teardown_req_ev.route_type = ROUTE_BACKUP
                    self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
            elif ev.result == FAIL or ev.result == TIMEOUT_REROUTING:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL)
                for lsp_id in range(len(unpro_lsp)):
                    Database.data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_FAIL) 
                lsp_teardown_req_ev = Custom_event.South_LSPTeardownRequestEvent()
                lsp_teardown_req_ev.traf_id = ev.traf_id
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)     
            else:
                self.logger.info('Invalid lsp setup result (rerouting)! (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)')
                return       
            traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.traf_stage = this_traf.traf_stage
            traf_reply_ev.traf_state = this_traf.traf_state
            self.send_event('North_bound_message_send',traf_reply_ev)
                                 
    @set_ev_cls(Custom_event.South_OSNRMonitoringReplyEvent)
    def _handle_OSNR_monitoring_reply(self,ev):
        pass
        #if result is not SUCCESS:
        #   error
        #else:
        #   if is_OSNR_all_good == True
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
        #           send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #   else: 
        #       update traffic state to TRAFFIC_INACTIVE
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #   traffic on rerouting path:
        #   if impairment at this domain
        #       update traffic state to TRAFFIC_INACTIVE
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #   else: 
        #       update traffic state to TRAFFIC_INACTIVE
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        
    @set_ev_cls(Custom_event.IntraDomainReroutingReply)
    def _handle_intra_domain_rerouting_reply(self,ev):
        #pass
        #if SUCCESS:
        #   update traf_state to TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS
        #   send Custom_event.South_LSPSetupRequestEvent to 'Intra_domain_connection_ctrl'
        #elif FAIL:
        #   traffic is intra_domain:
        #   update traf_state to TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL 
        #   send Custom_event.North_TrafficReplyEvent to 'North_bound_message_send'
        #   delete traffic and lsp information in database
        #else:
        #   error         
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS) 
            lsp_setup_req_ev = Custom_event.South_LSPSetupRequestEvent()
            lsp_setup_req_ev.traf_id = ev.traf_id
            self.send_event('Intra_domain_connection_ctrl',lsp_setup_req_ev)
        elif ev.result == FAIL:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL)
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.result = FAIL
            for this_traf in Database.Data.traf_list.traf_list:
                if this_traf.traf_id == ev_traf_id:
                    traf_reply_ev.traf_stage = this_traf.traf_stage
                    traf_reply_ev.traf_state = this_traf.traf_state
                    break
            self.send_event('North_bound_message_send',traf_reply_ev)
            Database.Data.traf_list.traf_list = filter(lambda traf: traf.traf_id != ev.traf_id, Database.Data.traf_list.traf_list)
            Database.Data.lsp_list.lsp_list = filter(lambda lsp: lsp.traf_id != ev.traf_id, Database.Data.lsp_list.lsp_list)
        else:
            self.logger.info('Invalid intra-domain path computatoin reply result! (Intra_domain_connection_ctrl: _handle_intra_domain_pc_reply)')
        
    @set_ev_cls(Custom_event.South_LSPTeardownRequestEvent)
    def _handle_lsp_teardown_request(self,ev):
        i = 0
        files_list = glob(os.path.join(self.rules_path_teardown, '*.json'))
        for filename in sorted(files_list):
            f = open(filename,"r")
            entry = f.readline()
            print(entry)
            self.teardown_config_wss_request_handler(entry)
            sleep(0.01)
        
        
    @set_ev_cls(Custom_event.South_LSPTeardownReplyEvent)
    def _handle_lsp_teardown_reply(self,ev):
        pass
        #if SUCCESS:
        #   update traffic state to TRAFFIC_TEARDOWN_SUCCESS
        #   recover Phy_topo 
        #else:
        #   update traffic state to TRAFFIC_TEARDOWN_FAIL 
        #if traffic is intra-domain:
        #   if this teardown is launched by central controller:
        #       send Custom_event.North_TrafficTeardownReplyEvent to 'North_bound_message_send'
        #   else:
        #       send Custom_event.North_TrafficStateUpdateEvent to 'North_bound_message_send'
        #   delete traffic, lsp informations
        #else:
        #   if this domain is the destination domain:
        #       send Custom_event.EastWest_SendTeardownTrafficReply to 'EastWest_message_send'
        #       delete traffic, lsp informations
        
        
    @set_ev_cls(Custom_event.EastWest_ReceiveTearDownPath)
    def _handle_receive_teardown_path_request(self,ev): 
        """teardown specified lsp(s) of a traffic 
        """
        #pass
        #Urgent!
        #for lsps need to be teardown:
        #   send OFPT_TEARDOWN_CONFIG_WSS_REQUEST messages to agent 
        #setup a time in south_timer_no_response
        new_timer = Database.Timer()
        new_timer.traf_id = ev.traf_id
        new_timer.timer_type = TIMER_TRAFFIC_TEARDOWN
        new_timer.end_time = time.time() + SOUTH_WAITING_TIME
	Database.Data.south_timer.append(new_timer)
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id and this_lsp.route_type == ev.route_type:
                new_msgs = LSP_msg_list()
                new_msgs.lsp_id = this_lsp.lsp_id
                new_msgs.route_type = this_lsp.route_type
		new_timer.lsp_msg_list.append(new_msgs)
		for key,new_node in enumerate(new_lsp.explicit_route.route):
		    Database.Data.message_id += 1	
		    #new_msgs.msgs.append(Database.Data.message_id)
		    new_msgs.msgs[key] = Database.Data.message_id
		self.logger.debug(str(new_msgs.msgs))
		if Database.Data.south_teardown_path_time == 0:		
		    Database.Data.south_teardown_path_time = time.time()
		else:
		    self.logger.critical('south_teardown_path_time error! \n')
                for key,new_node in enumerate(new_lsp.explicit_route.route):
                    dpid = DPID
                    datapath = Database.Data.ip2datapath[new_node.node_ip]
                    msg_id = new_msgs.msgs[key]
                    mod = datapath.ofproto_parser.OFPTTeardownConfigWSSRequest(datapath,
                                                                            datapath_id=dpid,
                                                                            message_id= msg_id,
                                                                            ITU_standards= ITU_C_50, 
                                                                            node_id= Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip),
                                                                            input_port_id= new_node.add_port_id, 
                                                                            output_port_id= new_node.drop_port_id,
                                                                            start_channel= this_lsp.occ_chnl[0],
                                                                            end_channel= this_lsp.occ_chnl[-1],
                                                                            experiment1=0,
                                                                            experiment2=0)
                    datapath.send_msg(mod)
                    self.logger.info('a WSS teardown-path config request is sent by RYU. (Intra_domain_connection_ctrl: _handle_receive_teardown_path_request)') 
                    self.logger.debug('msg_id = %d' % msg_id)
                    self.logger.debug('node_id = %d' % Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip))
                    self.logger.debug('input_port_id = %d' % new_node.add_port_id)
                    self.logger.debug('output_port_id = %d' % new_node.drop_port_id)
		    hub.sleep(0.05)
                if (not new_msgs.msgs) and (new_msgs in new_timer.lsp_msg_list):
		    new_timer.lsp_msg_list.remove(new_msgs)
        if (new_timer.lsp_msg_list == []) and (new_timer in Database.Data.south_timer):
	    Database.Data.south_timer.remove(new_timer)
            self.logger.info('No unprovisioned LSPs are found! (Intra_domain_connection_ctrl: _handle_receive_teardown_path_request')
        
    @set_ev_cls(Custom_event.North_IntraDomainTrafficTeardownRequestEvent)
    def _handle_intra_domain_traffic_teardown_request(self,ev):   
        #pass
        #send Custm_event.South_LSPTeardownRequestEvent to 'Intra_domain_connection_ctrl'
        #if Database.data.traf_list.find_traf_by_id(ev.traf_id) == None:
        #    self.logger.inf('Cannot find traffic %d! (Intra_domain_connection_ctrl: _handle_intra_domain_traffic_teardown_request)' % ev.traf_id)
        #    return
        intra_domain_traffic_teardown_ev = Custom_event.South_LSPTeardownRequestEvent()   
        intra_domain_traffic_teardown_ev.traf_id = ev.traf_id
        self.send_event('Intra_domain_connection_ctrl',intra_domain_traffic_teardown_ev)
        
    #@set_ev_cls(Custom_event.EastWest_TearDownPathReply)
   #     """reply of teardown specified lsp(s) of a traffic 
   #     """
   # def _handle_teardown_path_reply(self,ev): 
   #     #
   
    #def _virtual_port_mapping(self, node_id, port):
    #    node = self.virtual_port_mapping[node_id]
    #    for _map in node:
    #        if(_map[0] == port):
    #            print(_map[1])

    # Retrieve the proper values from the entry, and
    # delete_flow(), once formed the
    # Matching -- OutputActions relation.
    def teardown_config_wss_request_handler(self, entry):

        entry = json.loads(entry)

        dpid = dpid_lib.str_to_dpid(entry['datapath_id'])
        datapath = Database.Data.dpid2datapath[dpid]

        message_id = entry['message_id']
        ITU_standards = entry['ITU_standards']
        node_id = entry['node_id']
        input_port_id = entry['input_port_id']
        output_port_id = entry['output_port_id']
        start_channel = entry['start_channel']
        end_channel = entry['end_channel']
        experiment1 = entry['experiment1']
        experiment2 = entry['experiment2']

        parser = datapath.ofproto_parser

        msg = parser.OFPTTeardownConfigWSSRequest( datapath,
                                                dpid,
                                                message_id,
                                                ITU_standards,
                                                node_id,
                                                input_port_id,
                                                output_port_id,
                                                start_channel,
                                                end_channel,
                                                experiment1,
                                                experiment2)

        datapath.send_msg(msg)


    # Retrieve the proper values from the entry, and
    # invoke the WSS_setup function, once formed the
    # Matching -- OutputActions relation.
    def setup_config_wss_request_handler(self, entry):

        entry = json.loads(entry)
        
        dpid = dpid_lib.str_to_dpid(entry['datapath_id'])
        datapath = Database.Data.dpid2datapath[dpid]

        message_id = entry['message_id']
        ITU_standards = entry['ITU_standards']
        node_id = entry['node_id']
        input_port_id = entry['input_port_id']
        output_port_id = entry['output_port_id']
        start_channel = entry['start_channel']
        end_channel = entry['end_channel']
        experiment1 = entry['experiment1']
        experiment2 = entry['experiment2']

        parser = datapath.ofproto_parser

        msg = parser.OFPTSetupConfigWSSRequest( datapath,
                                                dpid,
                                                message_id,
                                                ITU_standards,
                                                node_id,
                                                input_port_id,
                                                output_port_id,
                                                start_channel,
                                                end_channel,
                                                experiment1,
                                                experiment2)

        datapath.send_msg(msg)
