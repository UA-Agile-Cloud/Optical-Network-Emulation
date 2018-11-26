# Build json with network configuration for a LINEAR topology
# LINKS
import json
# Structures as given in database
link_id_struct = "link_id"
tx_node_struct = "tx_node"
tx_node_port_struct = "tx_node_port"
rx_node_struct = "rx_node"
rx_node_port_struct = "rx_node_port"
amplifier_no_struct = "amplifier_no"
length_struct = "length"

# Definition of base values
nodes_no = 2
tx_node = 1
rx_node = 2
tx_node_port = 3
rx_node_port = 2
link = {"link":[]}
for link_id in range(1, nodes_no):
    new_link= {link_id_struct: link_id,  tx_node_struct: tx_node,  tx_node_port_struct: tx_node_port,  rx_node_struct: rx_node,  rx_node_port_struct: rx_node_port,  amplifier_no_struct: 5,  length_struct: 400}
    link["link"].append(new_link)
    new_link_id = link_id +4
    new_link_b= {link_id_struct: new_link_id,  tx_node_struct: rx_node,  tx_node_port_struct: tx_node_port+2,  rx_node_struct: tx_node,  rx_node_port_struct: rx_node_port+2,  amplifier_no_struct: 5,  length_struct: 400}
    link["link"].append(new_link_b)
    print("link_id: %s new_link_id: %s" %(link_id, new_link_id))
    tx_node = rx_node
    rx_node = rx_node + 1

# Create json file to be stored in the json folder
# and called by the network builder
with open('link.json', 'w') as fp:
    json.dump(link, fp)
    fp.close()
