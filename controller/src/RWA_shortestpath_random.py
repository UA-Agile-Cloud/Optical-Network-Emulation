"""
Routing and wavelength assignment
Routing: shortest path (one path)
wavlength assignment: random

Author:   Yao Li (yaoli@optics.arizona.edu)
          Jiakai Yu (jiakaiyu@email.arizona.edu)
Created:  2017/05/03
Version:  1.0

Last modified by Yao: 2017/05/19

"""

from Common import *
import random
import Database


def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if not graph.has_key(start):

        return None
    shortest = []
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    #print shortest
    return shortest

def get_common_avi_chnls (src_node_ip, dst_node_ip):
    common_avi_chnls= list()
    for this_link in Database.Data.phy_topo.link_list:
        if (this_link.src_node_ip == src_node_ip) and (this_link.dst_node_ip == dst_node_ip):
            for key, value in this_link.chnl_ava.iteritems():
                    if value == 0:
                        common_avi_chnls.append(key)
            return common_avi_chnls

def routing(traf_id, sources, destinations, bw_demand):
    """input: traf_id, sources, destinations, bw_demand
              sources: a list of [node_ip, node_port_id, route_type, cost, [common_avai_chnls]]
              destinations: a list of [node_ip, node_port_id]
       output: a list of [traf_id, route_type, cost, route(a list of [node_ip, add_port_id, drop_port_id]), common_avai_chnl(a list)]
               If fail, return None
    """
    paths = []
    topo = Database.Data.phy_topo.get_topo()
    print("Routing and wavelength assignment: TOPO")
    print(topo)
    route_ = []
    shortest = find_shortest_path(topo, sources[0][0], destinations[0][0])
    print('RWA_shortestpath_random: routing: shortest_path:')
    print(shortest)
    if shortest == [] :
        return None
    traf_id_ = traf_id
    route_type_ = sources[0][2]
    cost_ = sources[0][3] + len(shortest)
    common_avai_chnls_ = list(set(sources[0][4]))
    next_add_port_id_ = sources[0][1]
    for i in range(0, len(shortest)):
        node_ip_ = shortest[i] 
        if i < (len(shortest)-1):
            src_ = shortest[i]
            dst_ = shortest[i+1]
        if i == (len(shortest)-1):
            src_ = shortest[i-1]
            dst_ = shortest[i]
        for this_link in Database.Data.phy_topo.link_list:
            if (this_link.dst_node_ip == dst_) and (this_link.src_node_ip == src_):
                add_port_id_ = next_add_port_id_                
                drop_port_id_ = this_link.src_port_id
                next_add_port_id_ = this_link.dst_port_id
                
                if i == (len(shortest)-1):
                    drop_port_id_ = destinations[0][1]
                    add_port_id_ = this_link.dst_port_id

        route_.append([node_ip_, add_port_id_, drop_port_id_])
        if i < (len(shortest)-1): 
            common_avai_chnls_ = list(set(common_avai_chnls_) & set(get_common_avi_chnls(shortest[i], shortest[i+1])))

    if common_avai_chnls_ == []:
        return None
    if len(common_avai_chnls_) < (bw_demand/50):
        return None
    else:
        paths.append([traf_id_, route_type_, cost_, route_, common_avai_chnls_])
        return paths
    

def rerouting(traf_id, sources, destinations, bw_demand):
    """input: traf_id, sources, destinations, bw_demand
              sources: a list of [node_ip, node_port_id, route_type, cost, [common_avai_chnls]]
              destinations: a list of [node_ip, node_port_id]
       output: a list of [traf_id, route_type, cost, route(a list of [node_ip, add_port_id, drop_port_id]), common_avai_chnl(a list)]
               If fail, return None
    """
    #intra-domain rerouting
    traf_ = Database.Data.traf_list.find_traf_by_id(traf_id)
    if traf_.traf_state == TRAFFIC_INTRA_DOMAIN_REROUTE:
        return routing(traf_id, sources, destinations, bw_demand)

    #cross-domain rerouting
    paths = []
    topo = Database.Data.phy_topo.get_topo()
    for i in range(0, len(Database.Data.intra_domain_path_list.intra_domain_path_list)):
        if Database.Data.intra_domain_path_list.intra_domain_path_list[i].traf_id == str(traf_id):
            for this_node in Database.Data.intra_domain_path_list.intra_domain_path_list[i].route:
                if (this_node.node_ip != sources[0][0]) or (this_node.node_ip != destinations[0][0]):
                    for j in range(0, len(topo)):
                        topo[j].remove(Database.Data.get_node_id_by_ip(this_node.node_ip))
    route_ = []
    shortest = find_shortest_path (topo, sources[0][0], destinations[0][0])
    if shortest == [] :
        return None
    traf_id_ = traf_id
    route_type_ = sources[0][2]
    cost_ = sources[0][3] + len(shortest)
    common_avai_chnls_ = list(set(source[0][4]))
    for i in range(0, len(shortest)):
        node_ip_ = shortest[i] 
        if i < (len(shortest)-1):
            src_ = shortest[i]
            dst_ = shortest[i+1]
        if i == (len(shortest)-1):
            src_ = shortest[i-1]
            dst_ = shortest[i]
        next_add_port_id_ = sources[0][1]
        for this_link in Database.Data.phy_topo.link_list:
            if (this_link.dst_node_ip == dst_) and (this_link.src_node_ip == src_):
                add_port_id_ = next_add_port_id_                
                drop_port_id_ = this_link.src_port_id
                next_add_port_id_ = this_link.dst_port_id
                if i == (len(shortest)-1):

                    drop_port_id_ = destinations[0][1]
                    add_port_id_ = this_link.dst_port_id

        route_.append([node_ip_, add_port_id_, drop_port_id_])
        if i < (len(shortest)-1): 
            common_avai_chnls_ = list(set(common_avai_chnls_) & set(get_common_avi_chnls(shortest[i], shortest[i+1])))

    print [traf_id_, route_type_, cost_, route_, common_avai_chnls_]
    if common_avai_chnls_ == []:
        return None
    if len(common_avai_chnls_) < (bw_demand/50):
        return None
    else:
        paths.append([traf_id_, route_type_, cost_, route_, common_avai_chnls_])
        return paths
    
def rsc_allocation(traf_id, bw_demand,  CHANNEL_AVAIL):
    """input: traf_id, bw_demand
       output: a list of [path_id, resources (a list)]. If not found, return None
    """  
    res_allc_ = []
    for i in range(0, len(Database.Data.intra_domain_path_list.intra_domain_path_list)):
        if Database.Data.intra_domain_path_list.intra_domain_path_list[i].traf_id == traf_id:
            common_avai_chnls_ = Database.Data.intra_domain_path_list.intra_domain_path_list[i].chnl
            path_id_ = Database.Data.intra_domain_path_list.intra_domain_path_list[i].path_id
    res_bw_ = list(common_avai_chnls_)
    while len(res_bw_) > bw_demand/50 :
        res_bw_.remove(random.choice(res_bw_))
    if (list(res_bw_) != []) and len(res_bw_) == bw_demand/50:
#        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#        print(res_bw_)
#        print(CHANNEL_AVAIL)
#        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #res_allc_.append([path_id_, res_bw_])
        res_allc_.append([path_id_, CHANNEL_AVAIL])
        return res_allc_
    else:
        return None
    
              
def find_exit_of_this_domain(next_domain_id):        #completed by Yao Li
    """randomly get one edge node go outside this domain to 'next_domain_id'
       input: next_domain_id
       output: a list of [node_ip, node_port_id]. if not found, return None
    """
    out_node_list = Database.Data.phy_topo.get_out_node_id(next_domain_id)
    if out_node_list != []:
        random.shuffle(out_node_list)
        #print 'exit:'
        #print  out_node_list       
        return [out_node_list[0],]
    else:
        return None
    
    
def find_entry_of_next_domain(traf_id):
    """find one next domain's entry of traf_id's Traffic, based on Database.Data.intra_domain_path_list's information
       input: traf_id
       output: a list of [node_ip, node_port_id, route_type, cost, [common_avai_chnls]]. If not found, return None
    """
    print(Database.Data.intra_domain_path_list.intra_domain_path_list[0].traf_id)
    for i in range(0, len(Database.Data.intra_domain_path_list.intra_domain_path_list)):
        if Database.Data.intra_domain_path_list.intra_domain_path_list[i].traf_id == traf_id:

            route_type_        = Database.Data.intra_domain_path_list.intra_domain_path_list[i].route_type
            cost_              = Database.Data.intra_domain_path_list.intra_domain_path_list[i].cost
            routes_            = Database.Data.intra_domain_path_list.intra_domain_path_list[i].route
            common_avai_chnls_ = Database.Data.intra_domain_path_list.intra_domain_path_list[i].chnl
        else:
            return None
   
    this_domain_id = Database.Data.controller_list.this_controller.domain_id
    #print this_domain_id
    next_domain_id = Database.Data.traf_list.find_next_domain_id (traf_id, this_domain_id)
    #print next_domain_id
    entry_info_of_next_domain=[]
    #for i in range(0, len(routes_)):        
    edge_nodes_ip = routes_[-1].node_ip
    edge_nodes_port = routes_[-1].drop_port_id
    for this_link in Database.Data.phy_topo.link_list:
        if (this_link.link_type == LINK_INTER_DOMAIN) and (this_link.src_node_ip == edge_nodes_ip) and (this_link.src_port_id == edge_nodes_port) and (this_link.dst_domain_id == next_domain_id):
            node_ip_ = this_link.dst_node_ip
            node_port_id_ = this_link.dst_port_id
            entry_info_of_next_domain.append([node_ip_, node_port_id_, route_type_, cost_, common_avai_chnls_])
            if entry_info_of_next_domain != []: 
                return entry_info_of_next_domain
    return None

    
def find_intra_domain_paths(exit_of_this_domain):
    """find the intra-domain routing path(s) from several candidates in Database.Data.intra_domain_path_list, based on 
       the exit node and port.
       input: exit_of_this_domain: a list of [node_ip, node_port_id, route_type, [chnls]]
       output: a list of [path_id, resources (a list)]. If not found, return None
    """
    rand_exit = random.choice(exit_of_this_domain)
    intra_domain_path = []
    for i in range(0, len(Database.Data.intra_domain_path_list.intra_domain_path_list)):
        for this_node in Database.Data.intra_domain_path_list.intra_domain_path_list[i].route:
            if (this_node.node_ip == rand_exit[0]) and (this_node.drop_port_id == rand_exit[1]):
                common_avai_chnls_ = Database.Data.intra_domain_path_list.intra_domain_path_list[i].chnl
                path_id_ = Database.Data.intra_domain_path_list.intra_domain_path_list[i].path_id
                intra_domain_path.append([path_id_, common_avai_chnls_])
                if intra_domain_path !=[]:
                    return intra_domain_path
    return None
