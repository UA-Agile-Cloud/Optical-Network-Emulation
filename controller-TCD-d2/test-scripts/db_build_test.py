import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-new')
import database_management
import json

db_mgmt = database_management.DatabaseManagement()

db_mgmt_node = db_mgmt.NodeManagement()
db_mgmt_port = db_mgmt.PortManagement()
db_mgmt_link = db_mgmt.LinkManagement()


#"Create the 5 switches of the net"
with open('nodes.json') as f:
    node_data = json.load(f)

for node in node_data["node"]:
    node_tuple = [node["node_id"],  node["dpid"],  node["port_no"],  node["status"]]
    db_mgmt_node.add_node(node_tuple)
    
#"Create ports"
with open('ports.json') as f:
    port_data = json.load(f)
    
for port in port_data["port"]:
    port_tuple = [port["port_id"],  port["type"],  port["description"]]
    db_mgmt_port.add_port(port_tuple)
    
    
#"Create node_to_port relation"
with open('node_to_port.json') as f:
    node_to_port_data = json.load(f)
    
for node_to_port in node_to_port_data["node_to_port"]:
    node_to_port_tuple = [node_to_port["node_id"],  node_to_port["port_id"],  node_to_port["status"]]
    db_mgmt_node.add_node_to_port(node_to_port_tuple)

#"Generate links between switches == establish network Topology"
with open('link.json') as f:
    links = json.load(f)
    
for link in links["link"]:
    link_tuple = [link["link_id"],  link["tx_node"],  link["tx_node_port"],  link["rx_node"],  link["rx_node_port"],  link["amplifier_no"],  link["length"]]
    db_mgmt_link.add_link(link_tuple)
    
# Add Link to channel relations
with open('link_to_channel.json') as f:
    link_to_channels = json.load(f)
    
for link_to_channel in link_to_channels["link_to_channel"]:
    link_to_channel_tuple = [link_to_channel["link_id"],  link_to_channel["channel"],  link_to_channel["status"]]
    db_mgmt_link.add_link_to_channel(link_to_channel_tuple)
