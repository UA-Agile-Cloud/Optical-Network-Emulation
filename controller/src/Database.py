"""
contains data structures in Ryu controller

Author:   Yao Li (yaoli@optics.arizona.edu)
Created:  2017/01/09
Version:  2.0

Last modified by Yao: 2017/05/16

"""

from Common import *
import random

# Physical layer information

class Phy_node:
    def __init__(self):
        self.node_ip = ''
        self.node_id = 0
        self.node_type = 0
        self.port_num = 0
        self.ports = dict()        # port_id: port_type
     
     
class Phy_link:
    def __init__(self):
        self.link_id = 0
        self.link_type = 0
        self.src_node_ip = ''
        self.src_port_id = 0
        self.src_domain_id = 0
        self.dst_node_ip = ''
        self.dst_port_id = 0 
        self.dst_domain_id = 0 
        self.length = 0  
        self.ITU_Standards = 0  
        self.chnl_num = 0  
        self.chnl_ava = dict()      # chnl_id: chnl_avai    0:available, 1: occupied
                
class Phy_topo:
    def __init__(self):
        self.node_num = 0
        self.link_num = 0
        self.node_list = []
        self.link_list = []
        
    def get_node_id_by_ip(self, node_ip):
        """input: node_ip
           output: node_id. if not found, return None
        """
        for node in self.node_list:
            if node.node_ip == node_ip:
                return node.node_id
        return None
     
    def get_node_ip_by_id(self, node_id):
        """input: node_id
           output: node_ip. if not found, return None
        """
        for node in self.node_list:
            if node.node_id == node_id:
                return node.node_ip
        return None
        
    def get_out_node_id(self, next_domain_id):
        """get all the edge nodes go outside this domain to 'next_domain_id'
           input: next_domain_id
           output: a list of [node_ip, node_port_id]. if not found, return None
        """
        out_node_list = list()
        for this_node in self.node_list:
            if this_node.node_type == NODE_EDGE:
                for this_link in self.link_list:
                    if (this_link.link_type == LINK_INTER_DOMAIN) and (this_link.src_node_ip == this_node.node_ip) and (this_link.dst_domain_id == next_domain_id):
                        out_node_list.append([this_node.node_ip, this_link.src_port_id])
        if out_node_list != []:      
            return out_node_list    
        else:    
            return None 

    def get_traf_add_port(self, src_node_ip):
        """get the add port id of src_node_ip
           input: src_node_ip
           output: traf_add_port_id. If not found, return None
        """
        for this_link in self.link_list:
            if (this_link.link_type == LINK_AUXILIARY) and (this_link.dst_node_ip == src_node_ip):
                return this_link.dst_port_id
        return None
        
    def get_traf_drop_port(self, dst_node_ip):
        """get the drop port id of dst_node_ip
           input: dst_node_ip
           output: traf_drop_port_id. If not found, return None
        """
        for this_link in self.link_list:
            if (this_link.link_type == LINK_AUXILIARY) and (this_link.src_node_ip == dst_node_ip):
                return this_link.src_port_id
        return None

    def get_traf_add_port_resouce(self, src_node_ip, traf_add_port_id):
        """get available resouces of traf_add_port_id
           input: src_node_ip, traf_add_port_id
           output: [common_avai_chnls] (a list). If not found, return None
        """
        chnls = list()
        for this_link in self.link_list:
            if (this_link.link_type == LINK_AUXILIARY) and (this_link.dst_node_ip == src_node_ip) and (this_link.dst_port_id == traf_add_port_id):
                for key, value in this_link.chnl_ava.iteritems():
                    if value == 0:
                        chnls.append(key)
                return chnls
        return None
        
    def get_exit_of_previous_domain(self, node_ip, port_id):
        """get exit of previous domain by this domain's entry
           input: this domain's entry: [node_ip, port_id]
           output: previous domain's exit: [node_ip, port_id]. If not found, return None
        """
        #print 'test'
        for this_link in self.link_list:
            if (this_link.link_type == LINK_INTER_DOMAIN) and (this_link.dst_node_ip == node_ip) and (this_link.dst_port_id == port_id):
                return [this_link.src_node_ip, this_link.src_port_id]
        return None

    # from Yiwen
    def get_edge_node_id(self):
        """randomly get an edge node go outside this domain
           input: null
           output: node_id
        """
        for i in range(0, len(self.node_list)):
            if self.node_list[i].node_type == NODE_EDGE:
                return self.node_list[i].node_id
        
    def get_edge_node_ip(self):
        for i in range(0, len(self.node_list)):
            if self.node_list[i].node_type == NODE_EDGE:
                return self.node_list[i].node_ip

    def get_port_id(self, node_ip):
        for i in range(0, len(self.node_list)):
            if self.node_list[i].node_ip == node_ip:
                return self.node_list[i].ports

    def get_topo(self):     #translate network topo into adjacency list 
        topo = {}
        #modified by Yao 2017-05-03
        for node in self.node_list:
            topo[node.node_ip] = []
        for link in self.link_list:
            if link.src_node_ip != '0.0.0.0' and link.link_type == LINK_INTRA_DOMAIN:
                topo[link.src_node_ip].append(link.dst_node_ip)
            
        '''for i in range(0, len(self.link_list)):
            topo[self.link_list[i].src_node_ip]=[self.link_list[i].dst_node_ip]'''
        
        return topo   
    # from Yiwen end
        
# Physical layer information ends

# Lightpath information

class Node_for_route:
    def __init__(self):
        self.node_ip = ''
        self.add_port_id = 0
        self.add_port_power = 0
        self.drop_port_id = 0
        self.drop_port_power = 0

class Explicit_route:
    def __init__(self):
        self.hope_num = 0
        self.cost = 0
        self.route = []

class LSP:
    def __init__(self):
        self.lsp_id = 0
        self.traf_id = 0
        self.route_type = 0
        self.lsp_state = 1
        self.add_node_ip = ''
        self.add_port_id = 0
        self.add_port_OSNR = None
        self.drop_node_ip = ''
        self.drop_port_id = 0
        self.drop_port_OSNR = None
        self.ITU_Standards = 0
        self.occ_chnl_num = 0
        self.occ_chnl = []
        self.explicit_route = Explicit_route()
        self.estimated_drop_OSNR = None
        
class LSP_list:
    def __init__(self):
        self.lsp_num = 0
        self.lsp_list = []    

    def find_lsp_by_id(self, traf_id, lsp_id):
        """input: traf_id, lsp_id
           output: a lsp. if not found, return None
        """
        for lsp in self.lsp_list:
            if (lsp.traf_id == traf_id) and (lsp.lsp_id == lsp_id):
                return lsp
        return None
        
    def update_lsp_state(self, traf_id, lsp_id, lsp_state):
        """input: traf_id, lsp_id, lsp_state
           output: a bool indicates result
        """
        for lsp in self.lsp_list:
            if (lsp.traf_id == traf_id) and (lsp.lsp_id == lsp_id):
                lsp.lsp_state = lsp_state
                return True
        return False
    
    def update_lsp_osnr(self, traf_id, lsp_id, node_ip, OSNR):
        """input: traf_id, lsp_id, node_id, OSNR
           output: a bool indicates result
        """
        for lsp in self.lsp_list:
            if (lsp.traf_id == traf_id) and (lsp.lsp_id == lsp_id):
                if lsp.add_node_ip == node_ip:
                    lsp.add_port_OSNR = OSNR
                    return True
                elif lsp.drop_node_ip == node_ip:
                    lsp.drop_port_OSNR = OSNR
                    return True
                else:
                    print 'Cannot find node %s' % node_ip
                    return False
        return False

    def get_unprovisioned_lsps(self, traf_id):
        """input: traf_id
           output: a tuple of lsp_id (unprovisioned LSPs) 
        """
        lsp_list = list()
        for lsp in self.lsp_list:
            if (lsp.traf_id == traf_id) and (lsp.lsp_state == LSP_UNPROVISIONED):
                lsp_list.append(lsp.lsp_id)
        if len(lsp_list) == 0:
            return None
        elif len(lsp_list) == 1:
            return (lsp_list[0],)
        elif len(lsp_list) == 2:
            return (lsp_list[0], lsp_list[1])
        else:
            print 'Invalid number of unprovisioned LSPs.'
            return None
    
# Lightpath information ends
        
# Traffic information

class Time:
    def __init__(self):
        self.valid = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.day = 0
        self.month = 0
        self.year = 0

class Traffic:
    def __init__(self):
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        self.src_node_ip = ''
        self.dst_node_ip = ''
        self.traf_type = 0
        self.prot_type = 0
        self.up_time = None
        self.down_time = None
        self.bw_dmd = 0
        self.OSNR_req = 0
        self.domain_num = 0
        self.domain_sequence = []
       
class Traffic_list:
    def __init__(self):
        self.traf_num = 0
        self.traf_list = []
        
    def insert_new_traf(self, ev):
        """input: an instance of class North_TrafficRequestEvent
           output: a bool indicates result
        """
        if self.find_traf_by_id(ev.traf_id) != None:
            print 'Traffic %d already exits!' % ev.traf_id
            return False
        new_traf = Traffic()
        new_traf.traf_id = ev.traf_id
        new_traf.traf_stage = ev.traf_stage
        new_traf.traf_state = ev.traf_state
        new_traf.src_node_ip = ev.src_node_ip
        new_traf.dst_node_ip = ev.dst_node_ip
        new_traf.traf_type = ev.traf_type
        new_traf.prot_type = ev.prot_type
        new_traf.up_time = ev.up_time
        new_traf.down_time = ev.down_time
        new_traf.bw_dmd = ev.bw_demand
        new_traf.OSNR_req = ev.OSNR_req
        new_traf.domain_num = ev.domain_num
        new_traf.domain_sequence = list(ev.domain_sequence)
        self.traf_list.append(new_traf)
        return True
        
    def find_traf_by_id(self, traf_id):
        """input: a traffic id
           output: an instance of class Traffic or None(not found)
        """ 
        for traf in self.traf_list:
            if traf.traf_id == traf_id:
                return traf
        return None
        
    def update_traf_state(self, traf_id, traf_state):
        """input: traf_id, traf_state
           output: a bool indicates result
        """
        for traf in self.traf_list:
            if traf.traf_id == traf_id:
                traf.traf_state = traf_state
                return True
        return False
        
    def update_traf_stage(self, traf_id, traf_stage):
        """input: traf_id, traf_stage
           output: a bool indicates result
        """
        for traf in self.traf_list:
            if traf.traf_id == traf_id:
                traf.traf_stage = traf_stage
                return True
        return False      
        
    def find_next_domain_id(self, traf_id, this_domain_id):
        """input: traf_id, this_domain_id
           output: next_domain_id. if not found, return None
        """
        for traf in self.traf_list:
            if traf.traf_id == traf_id:
                for i in range(len(traf.domain_sequence)):
                    if traf.domain_sequence[i] == this_domain_id:
                        if (i+1)<len(traf.domain_sequence):
                            return traf.domain_sequence[i+1]
                        else:
                            return None
        return None
        
    def find_previous_domain_id(self, traf_id, this_domain_id):
        """input: traf_id, this_domain_id
           output: previous_domain_id. if not found, return None
        """
        for traf in self.traf_list:
            if traf.traf_id == traf_id:
                for i in range(len(traf.domain_sequence)):
                    if traf.domain_sequence[i] == this_domain_id:
                        if i>0:
                            return traf.domain_sequence[i-1]
                        else:
                            return None
        return None
       
# Traffic information ends

# Controller information

class Controller:
    def __init__(self):
        self.controller_type = 0
        self.controller_ip = ''
        self.domain_id = 0
        
class Domain_sequence:
    def __init__(self):
        self.src_domain_id = 0
        self.dst_domain_id = 0
        self.hop_num = 0
        self.domain_list = []
        
class Controller_list:
    def __init__(self):
        self.this_controller = Controller()
        self.central_controller = Controller()
        self.local_controllers = []
        self.domain_sequence_num = 0
        self.domain_sequence_list = dict()      #(src_domain_id, dst_domain_id): [domain_id1, domain_id2, ...]
        
    def is_this_domain(self, domain_id):  #if domain_id is this domain
        """input: domain_id
           output: a bool indicates if domain_id is this domain's id
        """
        if self.this_controller.domain_id == domain_id:
            return True
        else:
            return False
            
    def get_controller_ip_by_domain_id(self, domain_id):
        """input: domain_id
           output: a local controller ip. if not found, return None
        """
        for this_ctrl in self.local_controllers:
            if this_ctrl.domain_id == domain_id:
                return this_ctrl.controller_ip
        return None
        
        
# Controller information ends

# data structure used for cross-domain path computation

class Intra_domain_path:
    def __init__(self):
        self.path_id = 0
        self.traf_id = 0
        self.route_type = 0
        self.cost = 0
        self.route = []     # list of Node_for_route
        self.chnl = []      # common availabe channels
        
class Intra_domain_path_list:
    def __init__(self):
        self.path_id = 0
        self.intra_domain_path_list = []        # list of Intra_domain_path
        
    def insert_a_new_path(self, path):
        """input: (traf_id, route_type, cost, route(a list of [node_ip, add_port_id, drop_port_id]), common_avai_chnl(a list))
           output: a bool indicates result
        """
        #for this_path in self.intra_domain_path_list:
        #    if (this_path.traf_id == path[0]) and (this_path.route_type == path[1]):
        #        print 'Traffic %d\'s %d path already exits!'% (path[0], path[1])
        #        return False
        new_path = Intra_domain_path()
        self.path_id += 1
        new_path.path_id = self.path_id
        new_path.traf_id = path[0]
        new_path.route_type = path[1]
        new_path.cost = path[2]
        new_path.route = []
        for this_node in path[3]:
            new_node = Node_for_route()
            new_node.node_ip = this_node[0]
            new_node.add_port_id = this_node[1]
            new_node.add_port_power = 0
            new_node.drop_port_id = this_node[2]
            new_node.drop_port_power = 0
            new_path.route.append(new_node)
        new_path.chnl = list(path[4])
        self.intra_domain_path_list.append(new_path)
        return True
        
    def find_a_path_by_id(self, path_id):
        """input: path_id
           output: an instance of class Intra_domain_path; if not found, return None
        """
        for this_path in self.intra_domain_path_list:
            if this_path.path_id == path_id:
                return this_path
        else:
            return None
    
    def pop_paths(self, traf_id):
        """input: traf_id
           output: bool
        """
        ready_remove = list()
        for this_path in self.intra_domain_path_list:
            if this_path.traf_id == traf_id:
                #self.intra_domain_path_list.remove(this_path)
                #return True
                ready_remove.append(this_path)
        if ready_remove != []:
            for this_path in ready_remove:
                self.intra_domain_path_list.remove(this_path)
            ready_remove = []
            return True
        else:
            return False

    # from Yiwen
    def get_intra_domain_path(self, traf_id):
        for i in range(0, len(self.intra_domain_path_list)):
            if self.intra_domain_path_list[i][0] == traf_id:
                return self.intra_domain_path_list[i]

    def update_path_resources(self, traf_id, chosen_wavelength):
        for i in range(0, len(self.intra_domain_path_list)):
            if self.intra_domain_path_list[i][0] == traf_id:
                index_of_chosen_wavelength = self.intra_domain_path_list[i][4].index(chosen_wavelength)
                # update the route from a batch of routes and wavelengths to a single route and wavelength using the chosen wavelength by the destination controller
                self.intra_domain_path_list[i][3] = self.intra_domain_path_list[i][3][index_of_chosen_wavelength]
                self.intra_domain_path_list[i][4] = chosen_wavelength
                return True
        return False
    # from Yiwen
                

# data structure used for cross-domain path computation end

# timer

class LSP_msg_list:
    def __init__(self):
        self.lsp_id = 0
        self.route_type = 0
        self.msgs = dict()

class Timer:
    def __init__(self):
        self.traf_id = 0
        self.timer_type = 0
        self.end_time = 0
        self.lsp_msg_list = []  #a list of instances of class LSP_msg_list (only for south-bound timer use)
        
# timer end

# Global variables 
class Data:
    controller_list = Controller_list()
    phy_topo = Phy_topo()
    lsp_list = LSP_list()
    #unprovisioned_lsp_list = LSP_list()
    traf_list = Traffic_list()
    
    intra_domain_path_list = Intra_domain_path_list()       #for cross-domain path computation
    
    ip2datapath = dict()
    dpid2datapath = dict()
    
    lsp_id = 0
    message_id = 0
    north_timer = []
    eastwest_timer = []
    south_timer = []
    south_timer_no_response = []
    
    socket_server = None
    socket_client = dict()  # controller_ip: socket 

    #for recording excusion time
    south_setup_time = 0
    south_teardown_time = 0
    south_teardown_path_time = 0
    south_osnr_monitor_time = 0
    ew_ps_time = 0
    ew_setup_time = 0
    ew_teardown_time = 0
    ew_osnr_monitor_time = 0
    #for resording excution time end
    
    def __init__(self):
        pass
        
    '''@classmethod    
    def find_entry_of_next_domain(self, traf_id): # need to be completed in the future
        """input: traf_id
           output: a list of (node_ip, node_port_id, route_type, cost, [common_avai_chnls])
        """
        return None'''

    #from Yiwen
    @classmethod    
    def find_entry_of_next_domain(self, traf_id):       # entry point going into next domain
        """input: traf_id
           output: [[node_ip, wavelength], [...]]
        """
        #print ("PATH LIST", self.intra_domain_path_list.intra_domain_path_list)

        for i in range(0, len(self.intra_domain_path_list.intra_domain_path_list)):
            if self.intra_domain_path_list.intra_domain_path_list[i][0] == str(traf_id):
                traf_id_           = self.intra_domain_path_list.intra_domain_path_list[i][0]
                route_type_        = self.intra_domain_path_list.intra_domain_path_list[i][1]
                cost_              = self.intra_domain_path_list.intra_domain_path_list[i][2]
                routes_            = self.intra_domain_path_list.intra_domain_path_list[i][3]
                common_avai_chnls_ = self.intra_domain_path_list.intra_domain_path_list[i][4]

        # now use the last node of the route to get the edge node
        topo = self.phy_topo.get_topo()
        possible_edge_nodes_ip=[]
        possible_src_nodes_of_next_domain=[]
        src_node_ips_and_wavelengths=[]
        for i in range(0, len(routes_)):
            possible_edge_nodes_ip = routes_[i][-1]
            possible_src_nodes_of_next_domain.append(topo[possible_edge_nodes_ip])
            src_node_ips_and_wavelengths.append([topo[possible_edge_nodes_ip][0], common_avai_chnls_[i]])
        
        #print (src_node_ips_and_wavelengths)
        return src_node_ips_and_wavelengths
    #from Yiwen
        
    @classmethod
    def msg_in_south_timer(self,msg_id):
        for tmp_timer in self.south_timer:
            for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                for tmp_msg in tmp_lsp_msg_list.msgs.values():
                    if tmp_msg == msg_id:
                        return True
        return False
        
    @classmethod
    def msg_in_south_timer_no_response(self, msg_id):
        for tmp_timer in self.south_timer_no_response:
            for tmp_lsp_msg_list in tmp_timer.lsp_msg_list:
                for tmp_msg in tmp_lsp_msg_list.msgs.values():
                    if tmp_msg == msg_id:
                        return True
        return False
    
    @classmethod
    def msg_in_eastwest_timer(self, traf_id, timer_type):
        for tmp_timer in self.eastwest_timer:
            if (tmp_timer.traf_id == traf_id) and (tmp_timer.timer_type == timer_type):
                return True
        return False
        
    @classmethod
    def insert_new_lsp(self, path, resources):
        """input: path: an instance of class Intra_domain_path
                  resources: common_avai_chnl(a list)
           output: a bool indicates result
        """
        new_lsp = LSP()
        self.lsp_id += 1
        new_lsp.lsp_id = self.lsp_id
        new_lsp.traf_id = path.traf_id
        new_lsp.route_type = path.route_type
        new_lsp.lsp_state = LSP_UNPROVISIONED
        new_lsp.add_node_ip = path.route[0].node_ip
        new_lsp.add_port_id = path.route[0].add_port_id
        new_lsp.add_port_OSNR = None
        new_lsp.drop_node_ip = path.route[-1].node_ip
        new_lsp.drop_port_id = path.route[-1].drop_port_id
        new_lsp.drop_port_OSNR = None
        '''new_lsp.ITU_Standards = None
        for tmp_traf in self.traf_list.traf_list:
            if tmp_traf.traf_id == path.traf_id:          
                new_lsp.ITU_Standards = tmp_traf.ITU_Standards
                break
                if new_lsp.ITU_Standards == None:
            print ('Cannot find traffic %d.' % path.traf_id)
            return False'''
        new_lsp.ITU_Standards = ITU_C_50
        new_lsp.occ_chnl_num = len(resources)
        new_lsp.occ_chnl = list(resources)
        new_lsp.explicit_route.hope_num = len(path.route)
        new_lsp.explicit_route.cost = path.cost
        new_lsp.explicit_route.route = list(path.route)
        self.lsp_list.lsp_list.append(new_lsp)
        return True   
        
    @classmethod
    def update_phytopo(self, traf_id, lsp_id, action):
        """input: traf_id, lsp_id, action(ACTION_SETUP/ACTION_TEARDOWN)
           output: bool
        """
        for new_lsp in self.lsp_list.lsp_list:
            if (new_lsp.traf_id == traf_id) and (new_lsp.lsp_id == lsp_id):
                it_1 = 0 
                it_2 = it_1 + 1
                while (it_2 < len(new_lsp.explicit_route.route)):
                    node_1 = new_lsp.explicit_route.route[it_1]
                    node_2 = new_lsp.explicit_route.route[it_2]
                    for tmp_phy_link in self.phy_topo.link_list:
                        if (node_1.node_ip == tmp_phy_link.src_node_ip) and (node_1.drop_port_id == tmp_phy_link.src_port_id) and (node_2.node_ip == tmp_phy_link.dst_node_ip) and (node_2.add_port_id == tmp_phy_link.dst_port_id):
                            for chnl_no in new_lsp.occ_chnl:
                                if action == ACTION_SETUP:
                                    tmp_phy_link.chnl_ava[chnl_no] = lsp_id
                                elif action == ACTION_TEARDOWN:
                                    tmp_phy_link.chnl_ava[chnl_no] = 0
                                else:
                                    print ('invalid action! (Database: update_phytopo)')
                            break 
                    it_1 += 1
                    it_2 += 1
                node_1 = new_lsp.explicit_route.route[0]
                for tmp_phy_link in self.phy_topo.link_list:
                    if (node_1.node_ip == tmp_phy_link.dst_node_ip) and (node_1.add_port_id == tmp_phy_link.dst_port_id):
                        for chnl_no in new_lsp.occ_chnl:
                            if action == ACTION_SETUP:
                                tmp_phy_link.chnl_ava[chnl_no] = lsp_id
                            elif action == ACTION_TEARDOWN:
                                tmp_phy_link.chnl_ava[chnl_no] = 0
                            else:
                                print 'invalid action! (Database: update_phytopo)'
                        break
                node_2 = new_lsp.explicit_route.route[-1]
                for tmp_phy_link in self.phy_topo.link_list:
                    if (node_2.node_ip == tmp_phy_link.src_node_ip) and (node_2.drop_port_id == tmp_phy_link.src_port_id):
                        for chnl_no in new_lsp.occ_chnl:
                            if action == ACTION_SETUP:
                                tmp_phy_link.chnl_ava[chnl_no] = lsp_id
                            elif action == ACTION_TEARDOWN:
                                tmp_phy_link.chnl_ava[chnl_no] = 0
                            else:
                                print 'invalid action! (Database: update_phytopo)'
                    break
                return True
        return False
        
# Global variables end
       
