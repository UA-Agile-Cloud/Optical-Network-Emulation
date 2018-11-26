# Path Computation Element
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
import event_config
import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-TCD-d2')
from database import database_management as dbm
from rwa import rwa

import algorithm

class PathComputationElement(app_manager.RyuApp):
    
    _EVENTS = [event_config.LightpathCancelEvent]
    
    def __init__(self, *args, **kwargs):
        super(PathComputationElement, self).__init__(*args, **kwargs)
        self.dbm = dbm.DatabaseManagement()
        self.adjacency_matrix = self.build_adjacency_matrix()
        self.rwa = rwa.RoutingWavelengthAssignmentElement()
        self.algorithm = algorithm.Algorithm()
        
    # input: none
    # output: adjacency matrix (2D array)
    def build_adjacency_matrix(self):
        
        node_no = self.dbm.n_handle_count_nodes()
        
        nodes = self.dbm.n_handle_get_all_nodes()
        # init adjacency matrix
        adjacency_matrix = [[0 for column in range(node_no)] 
                                        for row in range(node_no)]
        links = self.dbm.l_handle_get_all_links()
        link_no = len(links)
        
        index_to_node = {}
        index = 0
        for node in nodes:
            index_to_node[node[0]] = index 
            index += 1
        
        # fill adjacency matrix with link-length weights    
        for link_index in range(0,  link_no):
            link = links[link_index]
            tx_node = index_to_node[link[1]]
            rx_node = index_to_node[link[3]]
            length = link[6]
            adjacency_matrix[tx_node][rx_node] = length
            
        return adjacency_matrix
        
    # Input: TX-node, RX-node
    # Output: sequence of links that form the path.
    @set_ev_cls(event_config.LightpathCreateEvent)
    def path_computation(self,  ev):
        lightpath_id,  tx_node,  rx_node = ev.lightpath_id,  ev.tx_node,  ev.rx_node
        try:
            # check for direct lightpath
            if self.adjacency_matrix[tx_node-1][rx_node-1] is not 0:
                print("PathComputationElement: path_computation: There is a direct lightpath [%s] from node %s to node %s" %(lightpath_id, tx_node,  rx_node))
                #build route
                route = self.build_route_single(lightpath_id, tx_node,  rx_node)
                # delegate to RWA component for evaluation
                self.rwa.route_evaluation(route, 1)
    #            if not self.rwa.route_evaluation(route, 1):
    #                print("PathComputationElement: path_computation: ERROR IN: Routing and Wavelength Assignment Module.")
            else:
                # invoke an algorithm for traversing the adjacency matrix
                path = self.algorithm.floyd_warshall_shortest_path(len(self.adjacency_matrix), tx_node, rx_node, self.adjacency_matrix)
                sequence = self.build_routes(lightpath_id, path)
                sequence_length = len(sequence)
                last_node_in_sequence = 0 # Default: False
                sequence_iteration = 1
                for route in sequence:
                    if sequence_iteration == sequence_length:
                        last_node_in_sequence = 1
                    if not self.rwa.route_evaluation(route, last_node_in_sequence):
                        print("PathComputationElement: path_computation: ERROR IN: Routing and Wavelength Assignment Module.")
                    sequence_iteration += 1
        except:
            lightpath_cancel_event = event_config.LightpathCancelEvent()
            lightpath_cancel_event.lightpath_id = lightpath_id
            self.send_event("DatabaseManagement", lightpath_cancel_event)
        
    # input: lightpath_id, tx_node,  rx_node (int, int, int)
    # output: route (tuple)
    def build_route_single(self,  lightpath_id, tx_node,  rx_node):
        link_id = self.dbm.l_handle_get_link_id(tx_node,  rx_node)
        route = (lightpath_id,  1,  link_id)
        return route
        
    def build_routes(self, lightpath_id, path):
        sequence = []
        sequence_no = 1
        for element in path:
            tx_node = element[0]
            rx_node = element[1]
            link_id = self.dbm.l_handle_get_link_id(tx_node,  rx_node)
            route = (lightpath_id,  sequence_no,  link_id)
            sequence.append(route)
            sequence_no += 1
        return sequence
