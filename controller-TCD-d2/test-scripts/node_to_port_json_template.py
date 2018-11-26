# Build json with network configuration for a LINEAR topology
# NODE TO PORTS
import json

node_id_struct = "node_id"
port_id_struct = "port_id"
status_struct = "status"

nodes_no = 5
port_no_base = 4

node_to_port = {"node_to_port":[]}
for node_id in range(1, nodes_no+1):
    if node_id > 1 and node_id < nodes_no:
        port_no = port_no_base + 2
    else:
        port_no = port_no_base
    for port_id in range(1,  port_no+1):
        new_node_to_port = {node_id_struct: node_id,  port_id_struct: port_id,  status_struct: 0}
        node_to_port["node_to_port"].append(new_node_to_port)

with open('node_to_port.json', 'w') as fp:
    json.dump(node_to_port, fp)
