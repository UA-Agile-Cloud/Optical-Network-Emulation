"""
Handle physical layer monitoring

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/02/13

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
import math
from decimal import *
import numpy as np
getcontext().prec = 8

logging.basicConfig(level = log_level)

class Monitoring(app_manager.RyuApp):
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    _EVENTS =  [Custom_event.South_OSNRMonitoringRequestEvent,
                Custom_event.South_OSNRMonitoringReplyEvent]
                
    def __init__(self,*args,**kwargs):
        super(Monitoring, self).__init__(*args,**kwargs)
        
    @set_ev_cls(Custom_event.South_OSNRMonitoringRequestEvent)
    def _handle_OSNR_monitoring_request(self,ev):
        #pass
        #send OFPT_GET_OSNR_REQUEST to agent
        #setup a timer in south_timer
        self.logger.debug('Monitoring module receives South_OSNRMonitoringRequestEvent')
        new_timer = Database.Timer()
        new_timer.traf_id = ev.traf_id
        new_timer.timer_type = TIMER_OSNR_MONITORING
        new_timer.end_time = time.time() + SOUTH_WAITING_TIME
	Database.Data.south_timer.append(new_timer)
	self.logger.debug('ev.traf_id = %d' % ev.traf_id)
	self.logger.debug('ev.route_type = %d' % ev.route_type)
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id and this_lsp.route_type == ev.route_type:
                new_msgs = Database.LSP_msg_list()
                new_msgs.lsp_id = this_lsp.lsp_id
                new_msgs.route_type = this_lsp.route_type
		new_timer.lsp_msg_list.append(new_msgs)
		Database.Data.message_id += 1
		new_msgs.msgs[0] = Database.Data.message_id
		Database.Data.message_id += 1
		new_msgs.msgs[1] = Database.Data.message_id
		#for resording excution time
		if Database.Data.south_osnr_monitor_time == 0:		
		    Database.Data.south_osnr_monitor_time = time.time()
		else:
		    self.logger.critical('south_osnr_monitor_time error! \n')
		#for resording excution time end
                new_node = this_lsp.explicit_route.route[0]
                if new_node != None:
                    dpid = DPID
                    datapath = Database.Data.ip2datapath[new_node.node_ip]
		    msg_id = new_msgs.msgs[0]
                    mod = datapath.ofproto_parser.OFPTGetOSNRRequest(datapath,
                                                                    datapath_id=dpid,
                                                                    message_id= msg_id,
                                                                    ITU_standards= ITU_C_50, 
                                                                    node_id= Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip),
                                                                    port_id= new_node.add_port_id, 
								    start_channel=this_lsp.occ_chnl[0],
                                                                    end_channel= this_lsp.occ_chnl[-1],
                                                                    experiment1=0,
                                                                    experiment2=0)
                    datapath.send_msg(mod)
                    self.logger.info('a OSNR monitor request is sent by RYU. (Monitoring: _handle_OSNR_monitoring_request)') 
                    self.logger.debug('msg_id = %d'% msg_id)
                    self.logger.debug('node_id = %d' % Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip))
                    self.logger.debug('port_id = %d' % new_node.add_port_id)
		    hub.sleep(0.05)
                    #new_msgs.msgs.append(Database.Data.message_id)
                new_node = this_lsp.explicit_route.route[-1]
                if new_node != None:
                    dpid = DPID
                    datapath = Database.Data.ip2datapath[new_node.node_ip]
                    msg_id = new_msgs.msgs[1]
                    mod = datapath.ofproto_parser.OFPTGetOSNRRequest(datapath,
                                                                    datapath_id=dpid,
                                                                    message_id= msg_id,
                                                                    ITU_standards= ITU_C_50, 
                                                                    node_id= Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip),
                                                                    port_id= new_node.drop_port_id, 
								    start_channel=this_lsp.occ_chnl[0],
                                                                    end_channel= this_lsp.occ_chnl[-1],
                                                                    experiment1=0,
                                                                    experiment2=0)
                    datapath.send_msg(mod)
                    self.logger.info('a OSNR monitor request is sent by RYU. (Monitoring: _handle_OSNR_monitoring_request)') 
                    self.logger.debug('msg_id = %d'% msg_id)
                    self.logger.debug('node_id = %d' % Database.Data.phy_topo.get_node_id_by_ip(new_node.node_ip))
                    self.logger.debug('port_id = %d' % new_node.drop_port_id)
                    #new_msgs.msgs.append(Database.Data.message_id)
                   
		if (not new_msgs.msgs) and (new_msgs in new_timer.lsp_msg_list):
		    new_timer.lsp_msg_list.remove(new_msgs)
        if (new_timer.lsp_msg_list == []) and (new_timer in Database.Data.south_timer):
	    Database.Data.south_timer.remove(new_timer)
            self.logger.info('No unprovisioned LSPs are found! (Monitoring: _handle_OSNR_monitoring_request)')

	'''# for testing
	this_traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if this_traf == None:
            self.logger.critical('Cannot find traffic %d. (Cross_domain_connection_ctrl: _handle_OSNR_monitoring_reply)' % ev.traf_id)
            return
	ev_osnr_reply = Custom_event.South_OSNRMonitoringReplyEvent()
        ev_osnr_reply.traf_id = ev.traf_id
        ev_osnr_reply.route_type = ev.route_type
        ev_osnr_reply.result = SUCCESS	
	# scenario 1
	if Database.Data.controller_list.this_controller.domain_id == 1:
	    ev_osnr_reply.is_OSNR_all_good = True
	    ev_osnr_reply.is_impairtment_at_this_domain = False
	else:
	    if this_traf.traf_stage == TRAFFIC_WORKING:
	        ev_osnr_reply.is_OSNR_all_good = False
	        ev_osnr_reply.is_impairtment_at_this_domain = True
	    else:
		ev_osnr_reply.is_OSNR_all_good = True
	        ev_osnr_reply.is_impairtment_at_this_domain = False
	# scenario 1 end
	# scenario 2
	if Database.Data.controller_list.this_controller.domain_id == 1:
	    if this_traf.traf_stage == TRAFFIC_WORKING:
	        ev_osnr_reply.is_OSNR_all_good = False
	        ev_osnr_reply.is_impairtment_at_this_domain = True
	    else:
		ev_osnr_reply.is_OSNR_all_good = True
	        ev_osnr_reply.is_impairtment_at_this_domain = False
	else:
	    ev_osnr_reply.is_OSNR_all_good = True
	    ev_osnr_reply.is_impairtment_at_this_domain = False
	# scenario 2 end
	self.send_event('Cross_domain_connection_ctrl',ev_osnr_reply)
	Database.Data.south_timer.remove(new_timer)
	# for testing end'''
            
            
    @set_ev_cls(ofp_event.EventOFPTGetOSNRReply,[CONFIG_DISPATCHER,MAIN_DISPATCHER,DEAD_DISPATCHER])
    def _handle_OSNR_monitoring_reply(self,ev):
        #pass
        #receive OFPT_GET_OSNR_REPLY
        #if cannot find a timer in south_timer:
        #   print error information
        #else:
        #   record monitored OSNR in Database
        #   update timer
        #   if all the replies are received:
        #       delete this timer
        #       if traf is intra-domain:
        #           send Custom_event.South_OSNRMonitoringReply to 'Intra_domain_connection_ctrl'
        #       else:
        #           send Custom_event.South_OSNRMonitoringReply to 'Cross_domain_connection_ctrl'
        msg = ev.msg
        (datapath_id,message_id,node_id,result,OSNR) = (msg.datapath_id,msg.message_id,msg.node_id,msg.result,msg.OSNR)
        try:
            datapath=Database.Data.dpid2datapath[datapath_id]
        except:
            print 'Bad things occur......Datapath not found...'
        #OSNR = (Decimal(10*np.log10(OSNR)),1)
        self.logger.info('RYU get a GET_OSNR_REPLY from agent %s' % datapath_id)
        if (Database.Data.msg_in_south_timer(message_id) == False) and (Database.Data.msg_in_south_timer_no_response(message_id) == False):
            self.logger.info('Cannot find this reply message in timer! (Monitoring: _handle_OSNR_monitoring_reply)')
            return
        if Database.Data.msg_in_south_timer(message_id) == True:
            if result == SUCCESS:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_OSNR_MONITORING:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            for key,msg_id in tmp_lsp_msg_list.msgs.items():
				if msg_id == message_id:
                                    self.logger.debug('Monitoring module receives a success osnr reply. msg_id = %d, OSNR = %s' % (message_id,OSNR))
                                    flag_find_msg = True
                                    #tmp_lsp_msg_list.msgs = filter(lambda msg: msg != message_id, tmp_lsp_msg_list.msgs)
				    del tmp_lsp_msg_list.msgs[key]
                                    Database.Data.lsp_list.update_lsp_osnr(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id, Database.Data.phy_topo.get_node_ip_by_id(node_id), OSNR)
                                    if not tmp_lsp_msg_list.msgs:
                                        ev_osnr_reply = Custom_event.South_OSNRMonitoringReplyEvent()
                                        ev_osnr_reply.traf_id = tmp_timer.traf_id
                                        ev_osnr_reply.route_type = tmp_lsp_msg_list.route_type
                                        ev_osnr_reply.result = SUCCESS
                                        this_lsp = Database.Data.lsp_list.find_lsp_by_id(tmp_timer.traf_id, tmp_lsp_msg_list.lsp_id)
                                        with open(root_path_controller+'log/ES_MS_OSNRS.log', 'a') as f:
                                            estimated_osnr = math.floor(Decimal(10*np.log10(this_lsp.estimated_drop_OSNR)))
                                            f.write(str(tmp_timer.traf_id)+'\t'+str(estimated_osnr)+'\t'+str(this_lsp.drop_port_OSNR)+'\n')
                                        if this_lsp == None:
                                            self.logger.info('Cannot find lsp in database! (Monitoring: _handle_OSNR_monitoring_reply)')
                                            return
                                        if this_lsp.add_port_OSNR>=OSNR_THRESHOLD and this_lsp.drop_port_OSNR>=OSNR_THRESHOLD:
                                            ev_osnr_reply.is_OSNR_all_good = True
                                            ev_osnr_reply.is_impairtment_at_this_domain = False
                                        elif this_lsp.add_port_OSNR<OSNR_THRESHOLD and this_lsp.drop_port_OSNR<OSNR_THRESHOLD:
                                            ev_osnr_reply.is_OSNR_all_good = False
                                            ev_osnr_reply.is_impairtment_at_this_domain = False
                                        else:
                                            ev_osnr_reply.is_OSNR_all_good = False
                                            ev_osnr_reply.is_impairtment_at_this_domain = True
                                        tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                                        if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                            self.send_event('Intra_domain_connection_ctrl',ev_osnr_reply)
                                        elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                            self.send_event('Cross_domain_connection_ctrl',ev_osnr_reply)
                                        else:
                                            self.logger.info('Invalid traffic type! (Monitoring: _handle_OSNR_monitoring_reply)')
                                        tmp_timer.lsp_msg_list.remove(tmp_lsp_msg_list)
					#for recording excusion time
					with open(root_path_controller+'log/record_time.log', 'a') as f:
					    f.write('South OSNR monitoring: (route_type = %d) \n' % tmp_lsp_msg_list.route_type)
					    f.write(str(time.time() - Database.Data.south_osnr_monitor_time)+'\n')
					Database.Data.south_osnr_monitor_time = 0
					#for recording excusion time end
                                        break     
                        if tmp_timer.lsp_msg_list == []:
                            Database.Data.south_timer.remove(tmp_timer)
                            break
                        if flag_find_msg == True:
                            break
            elif result == FAIL:
                flag_find_msg = False
                for tmp_timer in Database.Data.south_timer:
                    if tmp_timer.timer_type == TIMER_OSNR_MONITORING:
                        for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                            if message_id in tmp_lsp_msg_list.msgs:
                                self.logger.debug('Monitoring module receives a fail osnr reply. msg_id = %d' % message_id)
                                flag_find_msg = True
                                ev_osnr_reply = Custom_event.South_OSNRMonitoringReplyEvent()
                                ev_osnr_reply.traf_id = tmp_timer.traf_id
                                ev_osnr_reply.route_type = tmp_lsp_msg_list.route_type
                                ev_osnr_reply.result = FAIL
                                ev_osnr_reply.is_OSNR_all_good = None
                                ev_osnr_reply.is_impairtment_at_this_domain = None
                                tmp_traf = Database.Data.traf_list.find_traf_by_id(tmp_timer.traf_id)
                                if tmp_traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                                    self.send_event('Intra_domain_connection_ctrl',ev_osnr_reply)
                                elif tmp_traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                                    self.send_event('Cross_domain_connection_ctrl',ev_osnr_reply)
                                else:
                                    self.logger.info('Invalid traffic type! (Monitoring: _handle_OSNR_monitoring_reply)')
                                Database.Data.south_timer.remove(tmp_timer)
                                break
                        if flag_find_msg == True:
                            break
            else:
                self.logger.info('Invalid OSNR monitoring reply result! (Monitoring: _handle_OSNR_monitoring_reply)')
        else:   #Database.Data.msg_in_south_timer_no_response(message_id) == True:
            self.logger.info('Wrong timer type, OSNR monitoring reply should not in a no-response timer! (Monitoring: _handle_OSNR_monitoring_reply)')
