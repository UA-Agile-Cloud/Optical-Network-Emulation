# Build json with network configuration for a LINEAR topology
# LINKS
import json

link_id_struct = "link_id"
tx_node_struct = "tx_node"
tx_node_port_struct = "tx_node_port"
rx_node_struct = "rx_node"
rx_node_port_struct = "rx_node_port"
amplifier_no_struct = "amplifier_no"
length_struct = "length"

nodes_no = 5
tx_node = 1
rx_node = 2
tx_node_port = 1
rx_node_port = 2
link = {"link":[]}
for link_id in range(1, nodes_no):
    new_link= {link_id_struct: link_id,  tx_node_struct: tx_node,  tx_node_port_struct: tx_node_port,  rx_node_struct: rx_node,  rx_node_port_struct: rx_node_port,  amplifier_no_struct: 5,  length_struct: 400}
    link["link"].append(new_link)
    tx_node = rx_node
    rx_node = rx_node + 1

with open('link.json', 'w') as fp:
    json.dump(link, fp)
