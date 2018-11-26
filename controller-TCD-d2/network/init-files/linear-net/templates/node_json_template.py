# Build json with network configuration for a LINEAR topology
# NODES
import json

# Structures as given in database
node_id_struct = "node_id"
dpid_struct = "dpid"
port_no_struct = "port_no"
status_struct = "status"
dpid_base = "00000000000000"
nodes_no = 5
ports_no_base = 4

def build_dpid(id):
    id_s = str(id)
    if id < 10:
        id_s = "0" + id_s
    return dpid_base + id_s

# Definition of base values
node = {"node":[]}
ports_no = ports_no_base
for id in range(1, nodes_no+1):
    if id > 1 and id < nodes_no:
        ports_no = ports_no_base + 2
    else:
        ports_no = ports_no_base
    dpid = build_dpid(id)
    new_node = {node_id_struct: id,  dpid_struct: dpid,  port_no_struct: ports_no,  status_struct: 0}
    node["node"].append(new_node)

# Create json file to be stored in the json folder
# and called by the network builder
with open('nodes.json', 'w') as fp:
    json.dump(node, fp)
    fp.close()
