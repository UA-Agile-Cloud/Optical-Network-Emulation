"""
Intra_domain path computation 

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
          Yiwen Shen (ys2799@columbia.edu)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/05/19

"""
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from Common import *
import Database
import Custom_event
import logging
import RWA_shortestpath_random as RWA
from Common import log_level
import scipy.constants as sc
import link_distance_mapping
from time import sleep
import random
import numpy as np
import macros

logging.basicConfig(level = log_level)

class Path_computation(app_manager.RyuApp):
    
    _EVENTS =  [Custom_event.IntraDomainPathCompRequestEvent,
                Custom_event.IntraDomainPathCompReplyEvent,
                Custom_event.CrossDomainPathCompRequestEvent,
                Custom_event.CrossDomainPathCompReplyEvent,
                Custom_event.CrossDomainReroutingRequestEvent,
                Custom_event.CrossDomainReroutingReplyEvent,
                Custom_event.EastWest_SendPathCompRequestEvent,
                Custom_event.EastWest_ReceivePathCompRequestEvent,
                Custom_event.EastWest_SendPathCompReplyEvent,
                Custom_event.EastWest_ReceivePathCompReplyEvent,
                Custom_event.IntraDomainReroutingRequest,
                Custom_event.IntraDomainReroutingReply]
                
    def __init__(self,*args,**kwargs):
        super(Path_computation, self).__init__(*args,**kwargs)
        # for OSNR estimation purposes
        self.flow_id = 0
        # Converting 0.2dB loss, and multiplying
        # for 60km.
        self.abs_fiber_loss = self.dB_to_abs(0)
        # Converting 6dB loss
        self.abs_WSS_loss = self.dB_to_abs(9) # constant
        self.link_distance_mapping = link_distance_mapping.main()
        
        # TEMPORAL FOR TESTING PURPOSES - START
        self.CHANNEL_AVAIL = 1  # For incremental usage of channels
                                               # i.e. 1, 2, 3, etc.
        self.CHANNELS = macros.CHANNELS
        # TEMPORAL FOR TESTING PURPOSES - END

    @set_ev_cls(Custom_event.IntraDomainPathCompRequestEvent)
    def _handle_intra_domain_traffic_pc_request(self,ev): 
        """Path computation of a intra-domain traffic
        """
        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION)     # update traffic state to path_computation
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if (traf == None):
            self.logger.info('Can not find traf_id in database! (intra_domain_path_domputation: _handle_intra_domain_traffic_pc_request)')
            return
        if (traf.prot_type == TRAFFIC_NO_PROTECTION or traf.prot_type == TRAFFIC_REROUTING_RESTORATION): 
            #source_node_id = Database.Data.phy_topo.get_node_id_by_ip(traf.src_node_ip)
            #destination_node_id = Database.Data.phy_topo.get_node_id_by_ip(traf.dst_node_ip)
            sources = list()
            traf_add_port_id = Database.Data.phy_topo.get_traf_add_port(traf.src_node_ip)
            if traf_add_port_id == None:
                self.logger.critical('Cannot find an add port. (Path_computation: _handle_intra_domain_traffic_pc_request)')
                print('non-addport')
                return
            common_avai_chnls = Database.Data.phy_topo.get_traf_add_port_resouce(traf.src_node_ip, traf_add_port_id)
            if common_avai_chnls == None:
                self.logger.critical('Cannot find an add port. (Path_computation: _handle_intra_domain_traffic_pc_request)')
                print('non-avachnls')
                return
            sources.append([traf.src_node_ip, traf_add_port_id, ROUTE_WORKING, 0, common_avai_chnls])
            destinations = list()
            traf_drop_port_id = Database.Data.phy_topo.get_traf_drop_port(traf.dst_node_ip)
            if traf_drop_port_id == None:
                self.logger.critical('Cannot find an drop port. (Path_computation: _handle_intra_domain_traffic_pc_request)')
                return
            destinations.append([traf.dst_node_ip, traf_drop_port_id])
            paths = RWA.routing(ev.traf_id, sources, destinations, 50)
            # OSNR Estimation
            selected_path = paths[0][3]
            # Although inaccurate, the selection of a random wavelength for the
            # OSNR estimation is irrelevant, due to the fact that the ripple
            # function applied to it has a flat behaviour.
            chnl = random.randint(1, len(common_avai_chnls)-1)
            wavelength = common_avai_chnls[chnl]
            estimatedOSNR = self.handle_osnr_estimation(selected_path, wavelength)
        if (paths == None):
                print('Path_computation: _handle_intra_domain_traffic_pc_request: paths None')
                print(paths)
                #Database.Data.traf_list.update_traf_state(traf.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL) 
                pc_reply_ev = Custom_event.IntraDomainPathCompReplyEvent()
                pc_reply_ev.traf_id = ev.traf_id
                pc_reply_ev.result = FAIL
                self.send_event('Intra_domain_connection_ctrl',pc_reply_ev)
                # delete traffic information
                Database.Data.traf_list.remove(traf)
        else:
                result = SUCCESS
                for path in paths:
                    Database.Data.intra_domain_path_list.insert_a_new_path(path)    #record the result of routing
                # The channel to be used is assigned in
                # RWA.rsc_allocation(traf_id, bw_dmd)
                tmp_list = []
                channel_to_use = self.CHANNELS.pop(0)
                #tmp_list.append(self.CHANNEL_AVAIL)
                tmp_list.append(channel_to_use)
                resources = RWA.rsc_allocation(ev.traf_id, traf.bw_dmd,  tmp_list)
                #self.CHANNEL_AVAIL = self.CHANNEL_AVAIL + 1
                for path_item in resources:
                    new_path = Database.Data.intra_domain_path_list.find_a_path_by_id(path_item[0])
                    if new_path == None:
                        self.logger.critical('Cannot intra-domain path for traffic %d.' % ev.traf_id)
                        result = FAIL
                        break
                    if new_path.route_type == ROUTE_WORKING:
                        db_to_abs_estimatedOSNR = 10*np.log10(estimatedOSNR)
                        if db_to_abs_estimatedOSNR >= OSNR_THRESHOLD:
                            Database.Data.insert_new_lsp(new_path, path_item[1])
                            current_lsp = Database.Data.lsp_list.find_lsp_by_id(ev.traf_id, Database.Data.lsp_id)
                            if current_lsp != None:
                                current_lsp.estimated_drop_OSNR = estimatedOSNR
                            else:
                                self.logger.info('Cannot find newly inserted LSP. (Path_computation: _handle_intra_domain_traffic_pc_request)')
                            with open(root_path_controller+'log/estimatedOSNR.log', 'a') as f:
                                f.write(str(ev.traf_id)+'\t'+'0\n')
                        else:
                            result = FAIL
                            with open(root_path_controller+'log/estimatedOSNR.log', 'a') as f:
                                f.write(str(ev.traf_id)+'\t'+'1\n')
                    else: 
                        self.logger.critical('Wrong route type. (Path_computation: _handle_intra_domain_traffic_pc_request)')
                        return
                Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                if result == SUCCESS:
                    Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
                else:
                    Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                pc_reply_ev = Custom_event.IntraDomainPathCompReplyEvent()
                pc_reply_ev.traf_id = ev.traf_id
                pc_reply_ev.result = result
                print('Path_computation: _handle_intra_domain_traffic_pc_request: result')
                print(result)
                self.send_event('Intra_domain_connection_ctrl',pc_reply_ev)
#        elif(ev.prot_type == TRAFFIC_1PLUS1_PROTECTION):
#            pass
#        else:
#            self.logger.info('Protection type error! Protection type = %d' % ev.prot_type)


    @set_ev_cls(Custom_event.CrossDomainPathCompRequestEvent)
    def _handle_cross_domain_traffic_pc_request(self,ev): 
        """Path computation of a cross-domain traffic at its source domain
        """
        self.logger.debug('Path_computation module receives CrossDomainPathCompRequestEvent')
        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION)     # update traffic state to path_computation
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if (traf == None):
            self.logger.critical('Can not find traf_id in database! (cross_domain_path_domputation_at_src_domain)')
            return
        if (traf.prot_type == TRAFFIC_NO_PROTECTION or traf.prot_type == TRAFFIC_REROUTING_RESTORATION): 
            #source_node_id = Database.Data.phy_topo.get_node_id_by_ip(traf.src_node_ip)
            #destination_node_id = RWA.find_exit_of_this_domain(traf.domain_sequence[1])
            sources = list()
            traf_add_port_id = Database.Data.phy_topo.get_traf_add_port(traf.src_node_ip)
            if traf_add_port_id == None:
                self.logger.critical('Cannot find an add port. (Path_computation: _handle_cross_domain_traffic_pc_request)')
                return
            common_avai_chnls = Database.Data.phy_topo.get_traf_add_port_resouce(traf.src_node_ip, traf_add_port_id)
            if common_avai_chnls == None:
                self.logger.critical('Cannot find an add port. (Path_computation: _handle_cross_domain_traffic_pc_request)')
                return
            sources.append([traf.src_node_ip, traf_add_port_id, ROUTE_WORKING, 0, common_avai_chnls])
            destinations = RWA.find_exit_of_this_domain(traf.domain_sequence[1])
            if destinations == None:
                self.logger.critical('Cannot find a interlink. (Path_computation: _handle_cross_domain_traffic_pc_request)')
                return
            paths = RWA.routing(ev.traf_id, sources, destinations, traf.bw_dmd)    #routing. calculate one path
            #print '==============================='
            # from Yiwen
            #src_node_ip = traf.src_node_ip
            #src_port_id = Database.Data.phy_topo.get_port_id(src_node_ip)
            #edge_node_ip = Database.Data.phy_topo.get_edge_node_ip()
            #edge_node_id = Database.Data.phy_topo.get_edge_node_id()
            #self.logger.info ("Begin path computation in source domain from source node {0} to edge node {1}".format(src_node_ip, edge_node_ip))
            #topo = Database.Data.phy_topo.get_topo()
            #nlambda = 3
            #paths = self.routing(str(ev.traf_id), topo, nlambda, src_node_ip, src_port_id, edge_node_ip, traf.bw_dmd)    #routing. calculate one path
            # from Yiwen end
            
            # tmp routing. for temp use only
            #path = list()
            #path.append(ev.traf_id)
            #path.append(ROUTE_WORKING)
            #path.append(0)
            #path.append([['192.168.1.1',1,2],['192.168.1.2',1,2],['192.168.1.3',1,2]])
            #path.append([15])
            # tmp routing end
            
            if (paths == None):
                #Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                # send pc reply event to Cross_domain_connection_ctrl
                pc_reply_ev = Custom_event.CrossDomainPathCompReplyEvent()
                pc_reply_ev.traf_id = traf.traf_id
                pc_reply_ev.result = FAIL
                self.send_event('Cross_domain_connection_ctrl', pc_reply_ev)
            else:
                for path in paths:
                    #print '.....................'                   
                    Database.Data.intra_domain_path_list.insert_a_new_path(path)    #record the result of routing
                    #print path
                entry_of_next_domain = RWA.find_entry_of_next_domain(ev.traf_id)  # find entry of next domain
                #entry_of_next_domain = []
                if entry_of_next_domain != None:
                    cross_domain_pc_ev = Custom_event.EastWest_SendPathCompRequestEvent()
                    cross_domain_pc_ev.traf_id = ev.traf_id
                    cross_domain_pc_ev.route_type = ROUTE_WORKING
                    cross_domain_pc_ev.entry_of_next_domain = entry_of_next_domain
                    self.send_event('EastWest_message_send',cross_domain_pc_ev)
                else:
                    pc_reply_ev = Custom_event.CrossDomainPathCompReplyEvent()
                    pc_reply_ev.traf_id = traf.traf_id
                    pc_reply_ev.result = FAIL
                    self.send_event('Cross_domain_connection_ctrl', pc_reply_ev)
        elif (traf.prot_type == TRAFFIC_1PLUS1_PROTECTION):
            pass
        else:
            self.logger.info('Protection type error! Protection type = %d' % ev.prot_type)

    @set_ev_cls(Custom_event.EastWest_ReceivePathCompRequestEvent)
    def _handle_cross_domain_pc_request(self,ev):
        """path computation at domains (which are not the source domain) of a cross-domain traffic
        """
        pass
        #if (traf.prot_type == TRAFFIC_1PLUS1_PROTECTION):
        #   pass
        #if ev.route_type == ROUTE_REROUTE:
        #   update traffic stage to TRAFFIC_REROUTING in database
        #path computation in this domain
        #if SUCCESS:
        #   if this domain is not the destination domain:
        #       send Custom_event.EastWest_SendPathCompRequestEvent to 'EastWest_message_send'
        #   else:
        #       do resource allocation, update Database.Data.lsp_list
        #       update traffic state in database (TRAFFIC_PATH_COMPUTATION_SUCCESS)
        #       send Custom_event.EastWest_SendPathCompReplyEvent to 'EastWest_message_send'
        #else:
        #   update traffic state in database (TRAFFIC_PATH_COMPUTATION_FAIL)
        #   send Custom_event.EastWest_SendPathCompReplyEvent to 'EastWest_message_send'
        
        self.logger.debug('Path_computation module receives EastWest_ReceivePathCompRequestEvent')
        if ev.route_type == ROUTE_REROUTE:
            Database.Data.traf_list.update_traf_stage(ev.traf_id, TRAFFIC_REROUTING)
        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION)
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if traf == None:
            self.logger.critical('Cannot find traffic %d. (Path_computation: _handle_cross_domain_pc_request)' % ev.traf_id)
            return
        if (traf.prot_type == TRAFFIC_NO_PROTECTION or traf.prot_type == TRAFFIC_REROUTING_RESTORATION): 
            #source_node_id = Database.Data.phy_topo.get_node_id_by_ip(ev.entry_of_next_domain[0])
            #destination_node_id = RWA.find_exit_of_this_domain(traf.domain_sequence[1])
            sources = ev.entry_of_next_domain
            if Database.Data.controller_list.is_this_domain(traf.domain_sequence[-1]) == False:
                next_domain_id = Database.Data.traf_list.find_next_domain_id(ev.traf_id, Database.Data.controller_list.this_controller.domain_id)
                destinations = RWA.find_exit_of_this_domain(next_domain_id)
                if destinations == None:
                    self.logger.critical('Cannot find a interlink. (Path_computation: _handle_cross_domain_traffic_pc_request)')
                    return
            else:
                destinations = list()
                traf_drop_port_id = Database.Data.phy_topo.get_traf_drop_port(traf.dst_node_ip)
                if traf_drop_port_id == None:
                    self.logger.critical('Cannot find an drop port. (Path_computation: _handle_cross_domain_pc_request)')
                    return
                destinations.append([traf.dst_node_ip, traf_drop_port_id])
            if ev.route_type == ROUTE_REROUTE:
                paths = RWA.rerouting(ev.traf_id, sources, destinations, traf.bw_dmd)
            else:
                paths = RWA.routing(ev.traf_id, sources, destinations, traf.bw_dmd)
            if paths == None:
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                ew_pc_reply = Custom_event.EastWest_SendPathCompReplyEvent()
                ew_pc_reply.traf_id = ev.traf_id
                ew_pc_reply.route_type = ev.route_type
                ew_pc_reply.result = FAIL
                #ew_pc_reply.resource_allocation = []
                ew_pc_reply.exit_of_previous_domain = None
                self.send_event('EastWest_message_send', ew_pc_reply)
            else:
                for path in paths:
                    Database.Data.intra_domain_path_list.insert_a_new_path(path)    #record the result of routing
                if Database.Data.controller_list.is_this_domain(traf.domain_sequence[-1]) == False:
                    entry_of_next_domain = RWA.find_entry_of_next_domain(ev.traf_id)  # find entry of next domain
                    cross_domain_pc_ev = Custom_event.EastWest_SendPathCompRequestEvent()
                    cross_domain_pc_ev.traf_id = ev.traf_id
                    cross_domain_pc_ev.route_type = ev.route_type
                    cross_domain_pc_ev.entry_of_next_domain = entry_of_next_domain
                    self.send_event('EastWest_message_send',cross_domain_pc_ev)
                else:
                    resources = RWA.rsc_allocation(ev.traf_id, traf.bw_dmd)
                    result = SUCCESS
                    exit_of_previous_domain = list()
                    for path_item in resources:
                        new_path = Database.Data.intra_domain_path_list.find_a_path_by_id(path_item[0])
                        if new_path == None:
                            self.logger.critical('Cannot intra-domain path for traffic %d.' % ev.traf_id)
                            result = FAIL
                            break
                        Database.Data.insert_new_lsp(new_path, path_item[1])
                        exit_node_port_tmp = Database.Data.phy_topo.get_exit_of_previous_domain(new_path.route[0].node_ip, new_path.route[0].add_port_id)
                        if exit_node_port_tmp == None:
                            self.logger.critical('Can not find inter-domain link. (Path_computation: _handle_cross_domain_pc_request)')
                            result = FAIL
                            break
                        exit_tmp = [exit_node_port_tmp[0], exit_node_port_tmp[1], new_path.route_type, path_item[1]]
                        exit_of_previous_domain.append(exit_tmp)
                    Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                    if result == SUCCESS:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
                    else:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                    pc_reply_ev = Custom_event.EastWest_SendPathCompReplyEvent()
                    pc_reply_ev.traf_id = ev.traf_id
                    pc_reply_ev.route_type = ev.route_type
                    pc_reply_ev.result = result
                    #pc_reply_ev.resource_allocation = list(resources)
                    if result == SUCCESS:
                        pc_reply_ev.exit_of_previous_domain = exit_of_previous_domain
                    else:
                        pc_reply_ev.exit_of_previous_domain = None
                    self.send_event('EastWest_message_send', pc_reply_ev)
        elif (traf.prot_type == TRAFFIC_1PLUS1_PROTECTION):
            pass
        else:
            self.logger.info('Protection type error! Protection type = %d' % ev.prot_type)

     
    @set_ev_cls(Custom_event.EastWest_ReceivePathCompReplyEvent)
    def _handle_cross_domain_pc_reply(self,ev):
        """handle cross-domain path computation reply 
        """

        pass
        #if (traf.prot_type == TRAFFIC_1PLUS1_PROTECTION):
        #   pass
        #if ev.result == SUCCESS:
        #   do resource allocation, update Database.Data.lsp_list
        #   update traffic state to TRAFFIC_PATH_COMPUTATION_SUCCESS in database
        #else:
        #   update traffic state to TRAFFIC_PATH_COMPUTATION_FAIL in database  
        #if this domain is not the source domain:       
        #   send Custom_event.EastWest_SendPathCompReplyEvent to 'EastWest_message_send'
        #else:
        #   if ev.route_type == ROUTE_REROUTE:
        #       send Custom_event.CrossDomainReroutingReplyEvent to 'Cross_domain_connection_ctrl'
        #   else:
        #       send Custom_event.CrossDomainPathCompReplyEvent to 'Cross_domain_connection_ctrl'
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if traf == None:
            self.logger.critical('Cannot find traffic %d. (Path_computation: _handle_cross_domain_pc_reply)' % ev.traf_id)
            return
        if (traf.prot_type == TRAFFIC_NO_PROTECTION or traf.prot_type == TRAFFIC_REROUTING_RESTORATION): 
            self.logger.debug('Path_computation module receives EastWest_ReceivePathCompReplyEvent')
            if ev.result == SUCCESS:
                #path = Database.Data.intra_domain_path_list.find_a_path(ev.traf_id, ev.route_type)
                paths = RWA.find_intra_domain_paths(ev.exit_of_this_domain)
                if paths == None:
                    self.logger.critical('Cannot find intra-domain path for traffic %d.' % ev.traf_id)
                    return
                #Database.Data.insert_new_lsp(path, ev.resource_allocation)
                #Database.Data.intra_domain_path_list.pop_a_path(ev.traf_id, ev.route_type)
                #Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
                if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) != True:
                    result = SUCCESS
                    exit_of_previous_domain = list()
                    for path_item in paths:
                        new_path = Database.Data.intra_domain_path_list.find_a_path_by_id(path_item[0])
                        if new_path == None:
                            self.logger.critical('Cannot intra-domain path for traffic %d.' % ev.traf_id)
                            result = FAIL
                            break
                        Database.Data.insert_new_lsp(new_path, path_item[1])
                        exit_node_port_tmp = Database.Data.phy_topo.get_exit_of_previous_domain(new_path.route[0].node_ip, new_path.route[0].add_port_id)
                        if exit_node_port_tmp == None:
                            self.logger.critical('Can not find inter-domain link. (Path_computation: _handle_cross_domain_pc_request)')
                            result = FAIL
                            break
                        exit_tmp = [exit_node_port_tmp[0], exit_node_port_tmp[1], new_path.route_type, path_item[1]]
                        exit_of_previous_domain.append(exit_tmp)
                    Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                    if result == SUCCESS:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
                    else:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                    pc_reply_ev = Custom_event.EastWest_SendPathCompReplyEvent()
                    pc_reply_ev.traf_id = ev.traf_id
                    pc_reply_ev.route_type = ev.route_type
                    pc_reply_ev.result = result
                    if result == SUCCESS:
                        pc_reply_ev.exit_of_previous_domain = exit_of_previous_domain
                    else:
                        pc_reply_ev.exit_of_previous_domain = None
                    self.send_event('EastWest_message_send', pc_reply_ev)
                else:
                    result = SUCCESS
                    for path_item in paths:
                        new_path = Database.Data.intra_domain_path_list.find_a_path_by_id(path_item[0])
                        if new_path == None:
                            self.logger.critical('Cannot intra-domain path for traffic %d.' % ev.traf_id)
                            result = FAIL
                            break
                        Database.Data.insert_new_lsp(new_path, ev.exit_of_this_domain[0][3])  
                    Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                    if result == SUCCESS:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_SUCCESS) 
                    else:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL)
                    if ev.route_type == ROUTE_REROUTE:
                        rerouing_reply_ev = Custom_event.CrossDomainReroutingReplyEvent()
                        rerouing_reply_ev.traf_id = ev.traf_id
                        rerouing_reply_ev.result = result
                        self.send_event('Cross_domain_connection_ctrl', rerouing_reply_ev)
                    else:
                        pc_reply_ev = Custom_event.CrossDomainPathCompReplyEvent()
                        pc_reply_ev.traf_id = ev.traf_id
                        pc_reply_ev.result = result
                        self.send_event('Cross_domain_connection_ctrl', pc_reply_ev)
            else:   #FAIL or TIMEOUT
                self.logger.info('EastWest_ReceivePathCompReplyEvent result == FAIL or TIMEOUT')
                Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION_FAIL) 
                Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                if Database.Data.controller_list.is_this_domain(traf.domain_sequence[0]) != True:
                    pc_reply_ev = Custom_event.EastWest_SendPathCompReplyEvent()
                    pc_reply_ev.traf_id = ev.traf_id
                    pc_reply_ev.route_type = ev.route_type
                    pc_reply_ev.result = ev.result
                    pc_reply_ev.exit_of_previous_domain = None
                    self.send_event('EastWest_message_send', pc_reply_ev)
                else:
                    if ev.route_type == ROUTE_REROUTE:
                        rerouing_reply_ev = Custom_event.CrossDomainReroutingReplyEvent()
                        rerouing_reply_ev.traf_id = ev.traf_id
                        rerouing_reply_ev.result = ev.result
                        self.send_event('Cross_domain_connection_ctrl', rerouing_reply_ev)
                    else:
                        pc_reply_ev = Custom_event.CrossDomainPathCompReplyEvent()
                        pc_reply_ev.traf_id = ev.traf_id
                        pc_reply_ev.result = ev.result
                        self.send_event('Cross_domain_connection_ctrl', pc_reply_ev) 
        elif (traf.prot_type == TRAFFIC_1PLUS1_PROTECTION):
            pass
        else:
            self.logger.info('Protection type error! Protection type = %d' % ev.prot_type)
            

    @set_ev_cls(Custom_event.IntraDomainReroutingRequest)
    def _handle_intra_domain_rerouting_request(self,ev): 
        pass
        #rerouting
        #if SUCCESS:
        #   insert a new LSP to lsp_list
        #if traffic is intra-domain:
        #   send Custom_event.IntraDomainReroutingReply to 'Intra_domain_connection_ctrl'
        #elif traffic is cross-domain:
        #   send Custom_event.IntraDomainReroutingReply to 'Cross_domain_connection_ctrl'
        #else:
        #   error
        self.logger.debug('Path_computation module receives IntraDomainReroutingRequest')
        Database.Data.traf_list.update_traf_stage(ev.traf_id, TRAFFIC_REROUTING)
        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE)
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if traf == None:
            self.logger.critcal('Cannot find traffic %d. (Path_computation: _handle_intra_domain_rerouting_request)' % ev.traf_id)
            return
        if traf.prot_type != TRAFFIC_REROUTING_RESTORATION:
            self.logger.critcal('Wrong protection type. (Path_computation: _handle_intra_domain_rerouting_request)')
            return
        for this_lsp in Database.Data.lsp_list.lsp_list:
            if this_lsp.traf_id == ev.traf_id and this_lsp.route_type == ROUTE_WORKING:
                #source_node_id = Database.Data.phy_topo.get_node_id_by_ip(this_lsp.explicit_route.route[0].node_ip)
                #destination_node_id = Database.Data.phy_topo.get_node_id_by_ip(this_lsp.explicit_route.route[-1].node_ip)
                sources = list()
                if traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                    common_avai_chnls = Database.Data.phy_topo.get_traf_add_port_resouce(this_lsp.explicit_route.route[0].node_ip, this_lsp.explicit_route.route[0].add_port_id)
                elif traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                    common_avai_chnls = list(this_lsp.occ_chnl)
                else:
                    self.logger.info('Invalid traffic type! (Path_computation: _handle_intra_domain_rerouting_request)')
                if common_avai_chnls == None:
                    self.logger.critical('Cannot find an add port. (Path_computation: _handle_intra_domain_rerouting_request)')
                    return
                sources.append([this_lsp.explicit_route.route[0].node_ip, this_lsp.explicit_route.route[0].add_port_id, ROUTE_INTRA_REROUTE, 0, common_avai_chnls])
                destinations = list()
                destinations.append([this_lsp.explicit_route.route[-1].node_ip, this_lsp.explicit_route.route[-1].drop_port_id])
                #paths = RWA.rerouting(ev.traf_id, sources, destinations, traf.bw_demand)
                paths = RWA.rerouting(ev.traf_id, sources, destinations, 50)
                if paths == None:
                    reroute_reply_ev = Custom_event.IntraDomainReroutingReply()
                    reroute_reply_ev.traf_id = ev.traf_id
                    reroute_reply_ev.result = FAIL
                    if traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                        self.send_event('Intra_domain_connection_ctrl', reroute_reply_ev)
                    elif traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                        self.send_event('Cross_domain_connection_ctrl', reroute_reply_ev)
                    else:
                        self.logger.info('Invalid traffic type! (Path_computation: _handle_intra_domain_rerouting_request)')
                else:
                    result = SUCCESS
                    for path in paths:
                        Database.Data.intra_domain_path_list.insert_a_new_path(path)    #record the result of routing
                    resources = RWA.rsc_allocation(ev.traf_id, traf.bw_dmd)
                    for path_item in resources:
                        new_path = Database.Data.intra_domain_path_list.find_a_path_by_id(path_item[0])
                        if new_path == None:
                            self.logger.critical('Cannot intra-domain path for traffic %d.' % ev.traf_id)
                            result = FAIL
                            break
                        if new_path.route_type == ROUTE_INTRA_REROUTE:
                            Database.Data.insert_new_lsp(new_path, path_item[1])
                        else:
                            self.logger.critical('Wrong route type. (Path_computation: _handle_intra_domain_rerouting_request)')
                            return
                    Database.Data.intra_domain_path_list.pop_paths(ev.traf_id)
                    if result == SUCCESS:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_SUCCESS) 
                    else:
                        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_INTRA_DOMAIN_REROUTE_FAIL)
                    reroute_reply_ev = Custom_event.IntraDomainReroutingReply()
                    reroute_reply_ev.traf_id = ev.traf_id
                    reroute_reply_ev.result = result
                    if traf.traf_type == TRAFFIC_INTRA_DOMAIN:
                        self.send_event('Intra_domain_connection_ctrl', reroute_reply_ev)
                    elif traf.traf_type == TRAFFIC_CROSS_DOMAIN:
                        self.send_event('Cross_domain_connection_ctrl', reroute_reply_ev)
                    else:
                        self.logger.info('Invalid traffic type! (Path_computation: _handle_intra_domain_rerouting_request)')            
        
    @set_ev_cls(Custom_event.CrossDomainReroutingRequestEvent)
    def _handle_cross_domain_rerouting_request(self,ev):
        pass
        #update traffic stage to TRAFFIC_REROUTING
        #reroute at this first domain
        #if SUCCESS:
        #   update traffic state to TRAFFIC_PATH_COMPUTATION
        #   send Custom_event.EastWest_SendPathCompRequestEvent to 'EastWest_message_send'
        #else:
        #   update traffic state to TRAFFIC_PATH_COMPUTATION_FAIL
        #   send Custom_event.CrossDomainReroutingReplyEvent to 'Cross_domain_connection_ctrl'
        Database.Data.traf_list.update_traf_stage(ev.traf_id, TRAFFIC_REROUTING)
        Database.Data.traf_list.update_traf_state(ev.traf_id, TRAFFIC_PATH_COMPUTATION)
        traf = Database.Data.traf_list.find_traf_by_id(ev.traf_id)
        if (traf == None):
            self.logger.critical('Can not find traf_id in database! (cross_domain_reroute_at_src_domain)')
            return
        if traf.prot_type != TRAFFIC_REROUTING_RESTORATION:
            self.logger.critcal('Wrong protection type. (Path_computation: _handle_intra_domain_rerouting_request)')
            return
 
        sources = list()
        traf_add_port_id = Database.Data.phy_topo.get_traf_add_port(traf.src_node_ip)
        if traf_add_port_id == None:
            self.logger.critical('Cannot find an add port. (Path_computation: _handle_cross_domain_traffic_pc_request)')
            return
        common_avai_chnls = Database.Data.phy_topo.get_traf_add_port_resouce(traf.src_node_ip, traf_add_port_id)
        if common_avai_chnls == None:
            self.logger.critical('Cannot find an add port. (Path_computation: _handle_cross_domain_traffic_pc_request)')
            return
        sources.append([traf.src_node_ip, traf_add_port_id, ROUTE_WORKING, 0, common_avai_chnls])
        destinations = RWA.find_exit_of_this_domain(traf.domain_sequence[1])
        if destinations == None:
            self.logger.critical('Cannot find a interlink. (Path_computation: _handle_cross_domain_traffic_pc_request)')
            return
        paths = RWA.rerouting(ev.traf_id, sources, destinations, traf.bw_demand)    #routing. calculate one path

        if paths == None:
            # send pc reply event to Cross_domain_connection_ctrl
            pc_reply_ev = Custom_event.CrossDomainReroutingReplyEvent()
            pc_reply_ev.traf_id = traf.traf_id
            pc_reply_ev.result = FAIL
            self.send_event('Cross_domain_connection_ctrl', pc_reply_ev)
        else:
            for path in paths:                    
                Database.Data.intra_domain_path_list.insert_a_new_path(path)    #record the result of routing
            entry_of_next_domain = RWA.find_entry_of_next_domain(ev.traf_id)  # find entry of next domain
            if entry_of_next_domain != None:
                cross_domain_pc_ev = Custom_event.EastWest_SendPathCompRequestEvent()
                cross_domain_pc_ev.traf_id = ev.traf_id
                cross_domain_pc_ev.route_type = ROUTE_REROUTE
                cross_domain_pc_ev.entry_of_next_domain = entry_of_next_domain
                self.send_event('EastWest_message_send',cross_domain_pc_ev)
            else:
                pc_reply_ev = Custom_event.CrossDomainReroutingReplyEvent()
                pc_reply_ev.traf_id = traf.traf_id
                pc_reply_ev.result = FAIL
                self.send_event('Cross_domain_connection_ctrl', pc_reply_ev)
                
    #from Yiwen   modified by Yao 2017-05-03
    def routing_yiwen(self, traf_id, topo, nlambda, src_node_ip, src_port_id, edge_node_ip, bw_demand):
        """input: src_node_id, src_port_id, dst_node_id, bw_demand
           output: [traf_id, route_type, cost, route(a list of node_id), common_avai_chnl]. if fail, return []
        """
        computed_path = path_wav_compute(traf_id, topo, nlambda, src_node_ip, edge_node_ip)

        routes=[]
        wavelengths=[]
        for i in range(len(computed_path)):
            routes.append(computed_path[i][0])
            wavelengths.append(computed_path[i][1])

        return [traf_id, ROUTE_WORKING, 0, routes, wavelengths]
    #from Yiwen end
        
    def handle_osnr_estimation(self, selected_path, wavelength):
        self.flow_id = self.flow_id + 1
        flows_osnr = {}
        flows_osnr[self.flow_id] = []
        power = self.dB_to_abs(-2)
        noise = 1e-10
        LEN_PATH = len(selected_path)
        NODE_FLAG = 1
        self.abs_fiber_loss = self.dB_to_abs(1e-10)
        # # Converting 18dB loss (Two WSS)
        self.abs_WSS_loss = self.dB_to_abs(20)
        sleep(0.01)
        for node in selected_path:
            input_power, input_noise = self.estimate_input_power_noise(power, noise)
            a, b, c, node_id = node[0].split('.')
            output_power, output_noise = self.estimate_output_power_noise(int(node_id), input_power, input_noise, selected_path, wavelength)
            osnr = output_power / output_noise
            flows_osnr[self.flow_id].append(osnr)
            power = output_power
            noise = output_noise
            if NODE_FLAG == LEN_PATH-1:
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                # Converting 18dB loss (Two WSS)
                self.abs_WSS_loss = self.dB_to_abs(9)
                sleep(0.01)
            else:
                #self.abs_fiber_loss = self.dB_to_abs(0.2*60)
                self.abs_fiber_loss = self.dB_to_abs(1e-10)
                # Converting 18dB loss (Two WSS)
                self.abs_WSS_loss = self.dB_to_abs(20)
                sleep(0.01)
            NODE_FLAG = NODE_FLAG + 1
                    
        # This is considering a margin (of the mean of values in ripple function)
        #sim_vs_est_osnr = [value - 7.50992033577 for value in flows_osnr[self.flow_id]]
        sim_vs_est_osnr = flows_osnr[self.flow_id]
        f = open(root_path_controller+"log/rwa_osnr.log","a+")
        f.write(str(sim_vs_est_osnr) + "\n")
        f.close()
        
        return sim_vs_est_osnr[-1]
        
    def estimate_input_power_noise(self, in_signal_power, noise):
        in_power = (in_signal_power / self.abs_fiber_loss / self.abs_WSS_loss)
        in_noise = (noise / self.abs_fiber_loss / self.abs_WSS_loss)
        return in_power, in_noise

    def estimate_output_power_noise(self, node_id, input_power, input_noise, selected_path, wavelength):
        # Beware the hex format of the parameters
        #n_lambda = int(_lambda, 16)
        if(self.is_last_node_in_path(node_id, selected_path)):
            self.abs_WSS_loss = self.dB_to_abs(9)
            output_power = input_power / self.abs_WSS_loss
            output_noise = input_noise / self.abs_WSS_loss
            return output_power, output_noise

        try:
            dst_node = self.get_next_node(node_id, selected_path)
#            print('dst_node: %s', str(dst_node))
            EDFA_NO = self.get_EDFA_NO(node_id, dst_node)
#            print('EDFA_NO: %s', str(EDFA_NO))
            link_distance = self.get_link_distance(node_id, dst_node)
#            print('link_distance: %s', str(link_distance))

            RIPPLE = 1
            if EDFA_NO == 1:
                TARGET_GAIN = self.dB_to_abs(20)
                EDFA_OUT_POWER = TARGET_GAIN * input_power * RIPPLE
#                print('EDFA_OUT_POWER: ', str(EDFA_OUT_POWER))
                EDFA_NOISE = self.calculate_out_noise(input_noise, wavelength, TARGET_GAIN*RIPPLE)
#                print('EDFA 1, SHORT LINK, DISTANCE: %s', str(link_distance))
                self.abs_fiber_loss = self.dB_to_abs(0.2*link_distance)
                sleep(0.01)
                output_power = EDFA_OUT_POWER #/ self.abs_fiber_loss
                output_noise = EDFA_NOISE #/ self.abs_fiber_loss
#                print('output_power: ', str(output_power))
#                print('output_noise: ', str(output_noise))
                return output_power, output_noise

            self.update_fiber_loss(int(100)) # set standard span length
            sleep(0.01)
            for EDFA in range(int(EDFA_NO)):
#                print('EDFA: ', str(EDFA))
                if EDFA == 0:
                    TARGET_GAIN = self.dB_to_abs(20)
                elif EDFA == EDFA_NO-1:
                    TARGET_GAIN = self.compute_gain_last_span(input_power)
                else:
                    TARGET_GAIN = self.dB_to_abs(20)

                EDFA_OUT_POWER = TARGET_GAIN * input_power * RIPPLE
#                print('EDFA_OUT_POWER: ', str(EDFA_OUT_POWER))
                EDFA_NOISE = self.calculate_out_noise(input_noise, wavelength, TARGET_GAIN*RIPPLE)

                if EDFA == EDFA_NO-2:
                    last_span = self.get_last_span_length(EDFA_NO, link_distance)
                    self.abs_fiber_loss = self.dB_to_abs(0.2*last_span)
                    sleep(0.01)
                input_power = EDFA_OUT_POWER / self.abs_fiber_loss
                input_noise = EDFA_NOISE / self.abs_fiber_loss

                    
            output_power = EDFA_OUT_POWER
            output_noise = EDFA_NOISE
#            print('output_power: ', str(output_power))
#            print('output_noise: ', str(output_noise))
            return output_power, output_noise
        except:
            print('Err: estimate_output_power_noise. Unable to compute output power and noise.')
            return -1, -1

    def _ripple_function(self):
        try:
            #ripple_lambda = 1.00111792183 #Average from ripple function
            ripple_lambda = 1.0 #Average from ripple function
            target_gain = self.abs_fiber_loss * self.abs_WSS_loss
            sys_gain = ripple_lambda * target_gain
            return float(sys_gain)
        except:
            return float(self.abs_fiber_loss * self.abs_WSS_loss)

    def calculate_out_noise(self, input_noise, n_lambda, sys_gain):
        try:
            planck_const = sc.h # 6.62607004e-34
            speed_of_light = sc.speed_of_light # 299792460.0
            c_band_lambda = (1530+n_lambda*0.4)*10e-9
            noise_figure = self.dB_to_abs(6) 
            bandwidth = 12.5*(10e9) # Considering 50GHz bandwidth
            watt_to_mwatt = 1000
            out_noise = ((input_noise * sys_gain) + ((planck_const*(speed_of_light/c_band_lambda)) * sys_gain * watt_to_mwatt * noise_figure * bandwidth)) # 
#            print('calculate_out_noise: out_noise: %s', str(out_noise))
            return out_noise
        except:
            print('Err: calculate_out_noise. Unable to compute output noise.')
            return -1

    def remote_mininet_client(self, flow_id, src_node_id, dest_node_id, wavelength):
        file_path = root_path_controller+'remote_mininet_client/' + str(flow_id)
        line = str(flow_id) + " " + str(src_node_id) + " " + str(dest_node_id) + " " + str(wavelength)
        f = open(file_path, 'w+')
        f.write(line)
        f.close()
    
    def dB_to_abs(self, value):
        absolute_value = 10**(value/float(10))
        return absolute_value

    def get_link_distance(self, src_node, dst_node):
#        print('Entering get_link_distance')
#        print('src_node: %s', str(src_node))
#        print('dst_node: %s', str(dst_node))
        try:
            for link_id in self.link_distance_mapping:
                link = self.link_distance_mapping[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    distance = link[2]
                    return distance
        except:
            print('Err: get_link_distance. Unable to compute link distance.')
            return 1

    def get_EDFA_NO(self, src_node, dst_node):
        try:
            for link_id in self.link_distance_mapping:
                link = self.link_distance_mapping[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    EDFA_NO = link[3]
                    return EDFA_NO
        except:
            print('Err: get_EDFA_NO. Unable to compute EDFA number.')
            return 1

    def get_next_node(self, datapath_id, selected_path):
        try:
            NEXT_NODE_FLAG = False
            for _tuple in selected_path:
                a, b, c, snode_id = _tuple[0].split('.')
                node_id = int(snode_id)
                if NEXT_NODE_FLAG == True:
                    return node_id
                if node_id == datapath_id:
                    NEXT_NODE_FLAG = True
        except:
            print('Err: get_next_node. Unable to compute next node in path.')
            return -1

    def get_last_span_length(self, EDFA_NO, link_distance):
        try:
            # distance = self.get_link_distance(prev_node, src_node)
            # EDFA_NO = self.get_EDFA_NO(prev_node, src_node)
            last_span = link_distance - (100*(EDFA_NO-2))
            return last_span
        except:
            print('Err: get_last_span_length. Unable to compute last span length.')
            return 1

    def compute_gain_last_span(self, input_power):
        try:
            TARGET_POWER = self.dB_to_abs(-2)
            target_gain = TARGET_POWER / input_power
            return target_gain
        except:
            print('Err: compute_gain_last_span. Unable to compute gain at last amplifier.')
            return -1

    # Twin function of inter_domain_is_edge_node
    def is_last_node_in_path(self, datapath_id, selected_path):
        i = len(selected_path)
        last_tuple = selected_path[i-1]
        a, b, c, snode_id = last_tuple[0].split('.')
        last_node = int(snode_id)
        if(datapath_id == last_node):
            return True
        return False

    def update_fiber_loss(self, span):
        try:
            self.abs_fiber_loss = self.dB_to_abs(0.2*span)
        except:
            print('Err: update_fiber_loss. Unable to update out_fiber_loss')
