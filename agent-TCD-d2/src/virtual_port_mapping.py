#!/usr/bin/env python
import sys
from macros import *

virtual_ports_per_node = VIRTUAL_PORTS_PER_NODE
virtual_links = VIRTUAL_LINKS

def main():
    node_to_ports = {}
    dict_key = 1
    for node in virtual_ports_per_node:
        _list = []
        i=1
        for port in range(i,2*node+1):
            _list.append(port)
        node_to_ports[dict_key] = _list
        dict_key = dict_key + 1
    virtual_node_to_ports = {}
    dict_key = 1
    for node in virtual_ports_per_node:
        _list = []
        i=1
        for port in range(i,node+1):
            _list.append(port)
        virtual_node_to_ports[dict_key] = _list
        dict_key = dict_key + 1
        
    virtual_port_mapping = {0: []}
    dict_key = 0
    for link in virtual_links:
        src_node = link[0]
        dst_node = link[1]
        
        src_port = node_to_ports[src_node].pop(1)
        dst_port = node_to_ports[dst_node].pop(2)
        
        try: 
            virtual_src_port = virtual_node_to_ports[src_node].pop(1)
            virtual_dst_port = virtual_node_to_ports[dst_node].pop(1)
            
            if src_node not in virtual_port_mapping.keys():
                virtual_port_mapping[src_node] = []
            virtual_port_mapping[src_node].append((src_port, virtual_src_port))
            if dst_node not in virtual_port_mapping.keys():
                virtual_port_mapping[dst_node] = []
            virtual_port_mapping[dst_node].append((dst_port, virtual_dst_port))
        except:
            print('Err (virtual_port_mapping): pop index out of range for link: ' + str(src_node) + " --- " + str(dst_node))

		# Bidirectional link

        src_port = node_to_ports[dst_node].pop(1)
        dst_port = node_to_ports[src_node].pop(1)
        virtual_port_mapping[dst_node].append((src_port, virtual_dst_port))
        virtual_port_mapping[src_node].append((dst_port, virtual_src_port))
        
    i = 1
    for node in virtual_ports_per_node:
        ports_no = node*2
        virtual_port_mapping[i].append((1, 1))
        virtual_port_mapping[i].append((ports_no, 1))
        i = i + 1

    return virtual_port_mapping

if __name__=='__main__':
    sys.exit(main)
