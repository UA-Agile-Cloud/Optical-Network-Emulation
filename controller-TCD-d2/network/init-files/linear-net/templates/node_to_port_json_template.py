# Build json with network configuration for a LINEAR topology
# NODE TO PORTS
import json

def set_port_type(port_id,  port_no):
    if port_id == 1:
        port_type = 0 #TX
    elif port_id == port_no:
        port_type = 1 #RX
    else:
        if port_id%2 == 0:
            port_type = 2 #IN
        else:
            port_type = 3 #OUT
    return port_type
# Structures as given in database
node_id_struct = "node_id"
port_id_struct = "port_id"
port_type_struct = "port_type"
status_struct = "status"

# Definition of base values
nodes_no = 5
port_no_base = 4
node_to_port = {"node_to_port":[]}
for node_id in range(1, nodes_no+1):
    if node_id > 1 and node_id < nodes_no:
        port_no = port_no_base + 2
    else:
        port_no = port_no_base
    for port_id in range(1,  port_no+1):
        port_type = set_port_type(port_id,  port_no)
        new_node_to_port = {node_id_struct: node_id,  port_id_struct: port_id,  port_type_struct: port_type, status_struct: 0}
        node_to_port["node_to_port"].append(new_node_to_port)

# Create json file to be stored in the json folder
# and called by the network builder
with open('node_to_port.json', 'w') as fp:
    json.dump(node_to_port, fp)
    fp.close()
