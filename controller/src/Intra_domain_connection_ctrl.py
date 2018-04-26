"""
Intra-domain connection control

Author:   Yao Li (yaoli@optics.arizona.edu)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/05/101

"""

from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import time
from Common import *
import Database
import Custom_event
import logging
from Common import log_level
import remote_mininet_client
#from time import sleep

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
                #for testing
                Custom_event.South_LSPSetupReplyEvent]
                
    def __init__(self,*args,**kwargs):
        super(Intra_domain_connection_ctrl, self).__init__(*args,**kwargs)
                    
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
                if this_traf.traf_id == ev.traf_id:
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
        """Intra-domain lightpath setup 
        """
        #update Phy_topo
        #for all the unprovisioned lsps with lsp.traf_id == ev.traf_id
        #   send OFPT_SETUP_CONFIG_WSS_REQUEST message
        #   setup a timer in south_timer
        self.logger.debug('Intra_domain_connection_ctrl module receives South_LSPSetupRequestEvent')
        for new_lsp in Database.Data.lsp_list.lsp_list:
            if (new_lsp.traf_id == ev.traf_id) and (new_lsp.lsp_state == LSP_UNPROVISIONED):
                if Database.Data.update_phytopo(new_lsp.traf_id, new_lsp.lsp_id, ACTION_SETUP) == False:
                    self.logger.critical('Update phytopo fail! (Intra_domain_connection_ctrl: _handle_lsp_setup_request)')
                    return
                    
        new_timer = Database.Timer()
        new_timer.traf_id = ev.traf_id
        new_timer.timer_type = TIMER_TRAFFIC_SETUP
        new_timer.end_time = time.time() + SOUTH_WAITING_TIME
        Database.Data.south_timer.append(new_timer)
        for new_lsp in Database.Data.lsp_list.lsp_list:
            if (new_lsp.traf_id == ev.traf_id) and (new_lsp.lsp_state == LSP_UNPROVISIONED):
                new_msgs = Database.LSP_msg_list()
                new_msgs.lsp_id = new_lsp.lsp_id
                new_msgs.route_type = new_lsp.route_type
                new_timer.lsp_msg_list.append(new_msgs)
                for key,new_node in enumerate(new_lsp.explicit_route.route):
                    Database.Data.message_id += 1 
                    new_msgs.msgs[key] = Database.Data.message_id
                if Database.Data.south_setup_time == 0:   
                    Database.Data.south_setup_time = time.time()
                else:
                    self.logger.critical('south_setup_time error! \n')
                scr_node_id = 0
                dest_node_id = 0
                for traf in Database.Data.traf_list.traf_list:
                    if (traf.traf_id == ev.traf_id):
                        scr_node = traf.src_node_ip
                        scr_node_id = Database.Data.phy_topo.get_node_id_by_ip(scr_node)
                        dest_node = traf.dst_node_ip
                        dest_node_id = Database.Data.phy_topo.get_node_id_by_ip(dest_node)
                FLAG_ALT = 1
                for key,new_node in enumerate(new_lsp.explicit_route.route):
                    dpid = Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip)
                    datapath = Database.Data.ip2datapath[new_node.node_ip]
                    msg_id = new_msgs.msgs[key]
                    mod1 = datapath.ofproto_parser.OFPTSetupConfigWSSRequest(
                                            datapath,
                                            datapath_id=dpid,
                                            message_id= msg_id,
                                            ITU_standards= ITU_C_50, 
                                            node_id= Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip),
                                            input_port_id = new_node.add_port_id,
                                            output_port_id = new_node.drop_port_id,
                                            start_channel=new_lsp.occ_chnl[0],
                                            end_channel= new_lsp.occ_chnl[-1],
                                            experiment1= new_lsp.traf_id,
                                            experiment2=0)
                    datapath.send_msg(mod1)
                    hub.sleep(0.05)
                    FLAG_ALT = FLAG_ALT + 1
        remote_mininet_client.main(new_lsp.traf_id, scr_node_id, dest_node_id, hex(new_lsp.occ_chnl[0]))
        
    @set_ev_cls(Custom_event.South_LSPSetupReplyEvent)
    def _handle_lsp_setup_reply(self,ev):
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.info('Cannot find traffic %d. (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        for lsp in Database.Data.lsp_list.lsp_list:
            if (lsp.traf_id == ev.traf_id) and (lsp.lsp_state == LSP_UNPROVISIONED):
                unpro_lsp = Database.Data.lsp_list.get_unprovisioned_lsps(ev.traf_id)
        if unpro_lsp == None:
            self.logger.info('Cannot find traffic %d\'s unprovisioned lsps. (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)' % ev.traf_id)
            return
        if this_traf.traf_stage == TRAFFIC_WORKING:
            if ev.result == SUCCESS:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP_SUCCESS)
                for lsp_id in range(len(unpro_lsp)):
                    Database.Data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_SUCCESS)
#                sleep(16)
#                osnr_monitor_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
#                osnr_monitor_req_ev.traf_id = ev.traf_id
#                osnr_monitor_req_ev.route_type = ROUTE_WORKING
#                self.send_event('Monitoring',osnr_monitor_req_ev)
            elif ev.result == FAIL or ev.result == TIMEOUT_TRAF_SETUP:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_SETUP_FAIL)
                for lsp_id in range(len(unpro_lsp)):
                    Database.Data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_FAIL) 
                lsp_teardown_req_ev = Custom_event.South_LSPTeardownRequestEvent()
                lsp_teardown_req_ev.traf_id = this_traf.traf_id
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
            else:
                self.logger.info('Invalid lsp setup result! (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)')
                return
            traf_reply_ev = Custom_event.North_TrafficReplyEvent()
            traf_reply_ev.traf_id = this_traf.traf_id
            traf_reply_ev.result = ev.result
            traf_reply_ev.traf_stage = this_traf.traf_stage
            traf_reply_ev.traf_state = this_traf.traf_state
            self.send_event('North_bound_message_send',traf_reply_ev)
        elif this_traf.traf_stage == TRAFFIC_REROUTING:
            if ev.result == SUCCESS:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS) 
                for lsp_id in range(len(unpro_lsp)):
                    Database.Data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_SUCCESS)
                osnr_monitor_req_ev = Custom_event.South_OSNRMonitoringRequestEvent()
                osnr_monitor_req_ev.traf_id = this_traf.traf_id
                osnr_monitor_req_ev.route_type = ROUTE_REROUTE
                self.send_event('Monitoring',osnr_monitor_req_ev)
                lsp_teardown_req_ev = Custom_event.EastWest_ReceiveTearDownPath()
                lsp_teardown_req_ev.traf_id = ev.traf_id
                lsp_teardown_req_ev.route_type = ROUTE_WORKING
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
                if this_traf.prot_type == TRAFFIC_1PLUS1_PROTECTION:
                    lsp_teardown_req_ev = Custom_event.EastWest_ReceiveTearDownPath()
                    lsp_teardown_req_ev.traf_id = this_traf.traf_id
                    lsp_teardown_req_ev.route_type = ROUTE_BACKUP
                    self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)
            elif ev.result == FAIL or ev.result == TIMEOUT_REROUTING:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL)
                for lsp_id in range(len(unpro_lsp)):
                    Database.Data.lsp_list.update_lsp_state(ev.traf_id, lsp_id, LSP_SETUP_FAIL) 
                lsp_teardown_req_ev = Custom_event.South_LSPTeardownRequestEvent()
                lsp_teardown_req_ev.traf_id = ev.traf_id
                self.send_event('Intra_domain_connection_ctrl',lsp_teardown_req_ev)     
            else:
                self.logger.info('Invalid lsp setup result (rerouting)! (Intra_domain_connection_ctrl: _handle_lsp_setup_reply)')
                return       
            traf_reply_ev = Custom_event.North_TrafficStateUpdateEvent()
            traf_reply_ev.traf_id = ev.traf_id
            traf_reply_ev.traf_stage = this_traf.traf_stage
            traf_reply_ev.traf_state = this_traf.traf_state
            self.send_event('North_bound_message_send',traf_reply_ev)
                                 
    @set_ev_cls(Custom_event.South_OSNRMonitoringReplyEvent)
    def _handle_OSNR_monitoring_reply(self,ev):
        pass
        # Ignore this for the moment - April 24, 2018 - Alan
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critcal('Cannot find traffic %d. (Intra_domain_connection_ctrl: _handle_lsp_teardown_reply)' % ev.traf_id)
            return
        if ev.result != SUCCESS:
            self.logger.info('OSNR monitoring not success! (Intra_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
        else:
            if ev.is_OSNR_all_good == True:
                self.logger.info('OSNR of traffic %d is good! (Intra_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
                with open(root_path_controller+'log/measuredOSNR.log', 'a') as f:
                    f.write(str(ev.traf_id)+'\t'+'0\n')
                return
            with open(root_path_controller+'log/measuredOSNR.log', 'a') as f:
                f.write(str(ev.traf_id)+'\t'+'1\n')
            if ev.route_type == ROUTE_WORKING:
                if ev.is_impairtment_at_this_domain == True:
                    if this_traf.prot_type == TRAFFIC_REROUTING_RESTORATION:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE) 
                        Database.Data.traf_list.update_traf_stage(ev.traf_id, TRAFFIC_REROUTING) 
                        rerouting_ev = Custom_event.IntraDomainReroutingRequest()
                        rerouting_ev.traf_id = ev.traf_id
                        self.send_event('Path_computation', rerouting_ev)
                    elif this_traf.prot_type == TRAFFIC_1PLUS1_PROTECTION:
                        pass
                    elif this_traf.prot_type == TRAFFIC_NO_PROTECTION:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INACTIVE)
                        traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                        traf_update_ev.traf_id = ev.traf_id
                        traf_update_ev.traf_stage = this_traf.traf_stage
                        traf_update_ev.traf_state = this_traf.traf_state
                        self.send_event('North_bound_message_send', traf_update_ev)
                        ## for Alan use
                        intra_domain_traffic_teardown_ev = Custom_event.South_LSPTeardownRequestEvent()   
                        intra_domain_traffic_teardown_ev.traf_id = ev.traf_id
                        self.send_event('Intra_domain_connection_ctrl',intra_domain_traffic_teardown_ev)
                        ## for Alan use end
                    else:
                        self.logger.critical('Wrong traffic protection type (traffic %d)! (Intra_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
                else:
                    Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INACTIVE)
                    traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                    traf_update_ev.traf_id = ev.traf_id
                    traf_update_ev.traf_stage = this_traf.traf_stage
                    traf_update_ev.traf_state = this_traf.traf_state
                    self.send_event('North_bound_message_send', traf_update_ev)
            elif ev.route_type == ROUTE_INTRA_REROUTE or ev.route_type == ROUTE_REROUTE:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INACTIVE)
                traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                traf_update_ev.traf_id = ev.traf_id
                traf_update_ev.traf_stage = this_traf.traf_stage
                traf_update_ev.traf_state = this_traf.traf_state
                self.send_event('North_bound_message_send', traf_update_ev)
            elif ev.route_type == ROUTE_BACKUP:
                pass
            else:
                self.logger.critical('Wrong route type! (Intra_domain_connection_ctrl: _handle_OSNR_monitoring_reply)')
                    
        
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
        """Intra-domain lightpath teardown 
        """
        #pass
        #for all the provisioned lsps with lsp.traf_id == ev.traf_id
        #   send OFPT_TEARDOWN_CONFIG_WSS_REQUEST message
        #setup a timer in south_timer
        new_timer = Database.Timer()
        new_timer.traf_id = ev.traf_id
        new_timer.timer_type = TIMER_TRAFFIC_TEARDOWN
        new_timer.end_time = time.time() + SOUTH_WAITING_TIME
        Database.Data.south_timer.append(new_timer)
        # print '=========teardown_LSP_list_traf================='
        # print ev.traf_id
        # print '=========teardown_LSP_list_traf================='
        # print '=========teardown_LSP_list_len================='
        # print len(Database.Data.lsp_list.lsp_list)
        # print Database.Data.lsp_list.lsp_list[0].traf_id
        # print '=========teardown_LSP_list_len================='
        for this_lsp in Database.Data.lsp_list.lsp_list:
	    # print '---------lsp_loop!!!!------------'
	    # print this_lsp.traf_id
            if (this_lsp.traf_id == this_lsp.traf_id):
                this_msgs = Database.LSP_msg_list()
#                print('this_msgs')
#                print(this_msgs)
		#print '----------get_this_msgs_teardown------------'
                this_msgs.lsp_id = this_lsp.lsp_id
                this_msgs.route_type = this_lsp.route_type
                new_timer.lsp_msg_list.append(this_msgs)
                for key,this_node in enumerate(this_lsp.explicit_route.route):
                    Database.Data.message_id += 1 
                    # print '==============Database.Data.message_id==============='
                    # print Database.Data.message_id

                    # print len(this_lsp.explicit_route.route)

                    # print '==============Database.Data.message_id==============='

                    #new_msgs.msgs.append(Database.Data.message_id)

                    this_msgs.msgs[key] = Database.Data.message_id
                    # print '==============this_msgs.msgs[key]==============='
                    # print this_msgs.msgs[key]
                    # print '==============this_msgs.msgs[key]==============='
                self.logger.debug(str(this_msgs.msgs))
                if Database.Data.south_teardown_time == 0:    
                    Database.Data.south_teardown_time = time.time()
                else:
                    self.logger.critical('south_teardown_time error! \n')
                FLAG_ALT = 1
                for key,this_node in enumerate(this_lsp.explicit_route.route):
                    print('Entering to generation OFP_TEARDOWN')
                    dpid = Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip)
                    datapath = Database.Data.ip2datapath[this_node.node_ip]
                    msg_id = this_msgs.msgs[key]
                    mod = datapath.ofproto_parser.OFPTTeardownConfigWSSRequest(datapath,
                                                                            datapath_id=dpid,
                                                                            message_id= msg_id,
                                                                            ITU_standards= ITU_C_50, 
                                                                            node_id= Database.Data.phy_topo.get_node_id_by_ip(this_node.node_ip),
                                                                            input_port_id= this_node.add_port_id, 
                                                                            output_port_id= this_node.drop_port_id,
                                                                            start_channel= this_lsp.occ_chnl[0],
                                                                            end_channel= this_lsp.occ_chnl[-1],
                                                                            experiment1=this_lsp.traf_id,
                                                                            experiment2=0)
                    datapath.send_msg(mod)
                    self.logger.info('a WSS teardown config request is sent by RYU. (Intra_domain_connection_ctrl: _handle_lsp_teardown_request)') 
                    #self.logger.debug('msg_id = %d' % msg_id)
                    self.logger.debug('node_id = %d' % Database.Data.phy_topo.get_node_id_by_ip(this_node.node_ip))
                    self.logger.debug('input_port_id = %d' % this_node.add_port_id)
                    self.logger.debug('output_port_id = %d' % this_node.drop_port_id)
                    hub.sleep(0.05)
                    FLAG_ALT = FLAG_ALT + 1
                    #new_msgs.msgs.append(Database.Data.message_id)
                # if (FLAG_ALT == len(this_msgs.msgs)):
                #     new_timer.lsp_msg_list.remove(this_msgs)
                #     Database.Data.south_timer.remove(new_timer)
#                print('new_time.lsp_msg_list')
#                print(new_timer.lsp_msg_list)
                # if (new_timer.lsp_msg_list.msgs == {}):
                # #if (new_timer.lsp_msg_list == []) and (new_timer in Database.Data.south_timer):
                #     Database.Data.south_timer.remove(new_timer)
                #     self.logger.info('No unprovisioned LSPs are found! (Intra_domain_connection_ctrl: _handle_lsp_teardown_request)')
                    #new_msgs.msgs.append(Database.Data.message_id)
                    # print('len this_msgs.msgs')
                    # print(len(this_msgs.msgs))
                    # print('new_timer.lsp_msg_list')
                    # print(type(new_timer.lsp_msg_list)
	
        '''# for testing
        ev_lsp_teardown_reply = Custom_event.South_LSPTeardownReplyEvent()
              ev_lsp_teardown_reply.traf_id = new_timer.traf_id
              ev_lsp_teardown_reply.result = SUCCESS
        self.send_event('Cross_domain_connection_ctrl',ev_lsp_setup_reply)
        Database.Data.south_timer.remove(new_timer)
        #for testing end'''
        
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
        #       send Custom_event.EastWest_SendTrafTeardownReply to 'EastWest_message_send'
        #       delete traffic, lsp informations
        this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Intra_domain_connection_ctrl: _handle_lsp_teardown_reply)' % ev.traf_id)
            return
        if ev.result == SUCCESS:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_TEARDOWN_SUCCESS)
            for lsp in Database.Data.lsp_list.lsp_list:
                if lsp.traf_id == ev.traf_id:
                    if Database.Data.update_phytopo(lsp.traf_id, lsp.lsp_id, ACTION_TEARDOWN) == False:
                        self.logger.critical('Update phytopo fail! (Intra_domain_connection_ctrl: _handle_lsp_teardown_reply)')
        else:
            Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_TEARDOWN_FAIL)
            
        if this_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
            find_timer = False
            for this_timer in Database.Data.north_timer:
                if this_timer.traf_id == ev.traf_id and this_timer.timer_type == TIMER_TRAFFIC_TEARDOWN:
                    find_timer = True
                    break
            if find_timer:  # tear down is launched by central controller
                traf_tear_reply_ev = Custom_event.North_TrafficTeardownReplyEvent()
                traf_tear_reply_ev.traf_id = ev.traf_id
                traf_tear_reply_ev.result = ev.result
                traf_tear_reply_ev.traf_stage = this_traf.traf_stage
                traf_tear_reply_ev.traf_state = this_traf.traf_state
                self.send_event('North_bound_message_send', traf_tear_reply_ev)
            else:
                traf_update_ev = Custom_event.North_TrafficStateUpdateEvent()
                traf_update_ev.traf_id = ev.traf_id
                traf_update_ev.traf_stage = this_traf.traf_stage
                traf_update_ev.traf_state = this_traf.traf_state
                self.send_event('North_bound_message_send', traf_update_ev)
            # delete traffic, lsp informations
            ready_remove = list()
            for this_lsp in Database.Data.lsp_list.lsp_list:
                if this_lsp.traf_id == ev.traf_id:
                    ready_remove.append(this_lsp)
            for lsp in ready_remove:
                Database.Data.lsp_list.lsp_list.remove(lsp)
            Database.Data.traf_list.traf_list.remove(this_traf)
        else:
            if Database.Data.controller_list.is_this_domain(this_traf.domain_sequence[-1]) == True:
                ew_traf_tear_reply_ev = Custom_event.EastWest_SendTrafTeardownReply()
                ew_traf_tear_reply_ev.traf_id = ev.traf_id
                ew_traf_tear_reply_ev.result = ev.result
                self.send_event('EastWest_message_send', ew_traf_tear_reply_ev)
                for this_lsp in Database.Data.lsp_list.lsp_list:
                    if this_lsp.traf_id == ev.traf_id:
                       ready_remove.append(this_lsp)
                for lsp in ready_remove:
                    Database.Data.lsp_list.lsp_list.remove(lsp)
                Database.Data.traf_list.remove(this_traf)            
        
        
    @set_ev_cls(Custom_event.EastWest_ReceiveTearDownPath)
    def _handle_receive_teardown_path_request(self,ev): 
        """teardown specified lsp(s) of a traffic 
        """
        pass
        #Urgent!
        #for lsps need to be teardown:
        #   send OFPT_TEARDOWN_CONFIG_WSS_REQUEST messages to agent 
        #setup a time in south_timer_no_response
        new_timer = Database.Timer()
        new_timer.traf_id = ev.traf_id
        new_timer.timer_type = TIMER_TRAFFIC_TEARDOWN
        new_timer.end_time = time.time() + SOUTH_WAITING_TIME
        Database.Data.south_timer_no_response.append(new_timer)
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id:# and this_lsp.route_type == ev.route_type:
                new_msgs = Database.LSP_msg_list()
                new_msgs.lsp_id = this_lsp.lsp_id
                new_msgs.route_type = this_lsp.route_type
                new_timer.lsp_msg_list.append(new_msgs)
            for key,new_node in enumerate(this_lsp.explicit_route.route):
                Database.Data.message_id += 1 
                #new_msgs.msgs.append(Database.Data.message_id)
                new_msgs.msgs[key] = Database.Data.message_id
            self.logger.debug(str(new_msgs.msgs))
            if Database.Data.south_teardown_path_time == 0:   
                Database.Data.south_teardown_path_time = time.time()
            else:
                self.logger.critical('south_teardown_path_time error! \n')
            for key,new_node in enumerate(this_lsp.explicit_route.route):
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
                                                                        experiment1=ev.traf_id,
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
        '''if Database.Data.traf_list.find_traf_by_id(ev.traf_id) == None:
            print('traf_id')
            print(ev.traf_id)
            print (len(Database.Data.traf_list.traf_list))
            print (len(Database.Data.traf_list.traf_list[0].traf_id))
            print(Database.Data.traf_list.find_traf_by_id(ev.traf_id))
            #self.logger.info('Cannot find traffic %d! (Intra_domain_connection_ctrl: _handle_intra_domain_traffic_teardown_request)' % ev.traf_id)
            print('Err: _handle_intra_domain_traffic_teardown_request')
            return'''
        intra_domain_traffic_teardown_ev = Custom_event.South_LSPTeardownRequestEvent()   
        intra_domain_traffic_teardown_ev.traf_id = ev.traf_id
        self.send_event('Intra_domain_connection_ctrl',intra_domain_traffic_teardown_ev)
        
    #@set_ev_cls(Custom_event.EastWest_TearDownPathReply)
   #     """reply of teardown specified lsp(s) of a traffic 
   #     """
   # def _handle_teardown_path_reply(self,ev): 
   #     #

    # def _virtual_port_mapping(self, node_id, port):
    #     node = self.virtual_port_mapping[node_id]
    #     for _map in node:
    #         if(_map[0] == port):
    #             return _map[1]
    #     return 0
