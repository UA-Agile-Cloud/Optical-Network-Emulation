import net_config as nc
from database import database_management as dbm
import json

db = dbm.DatabaseManagement()
node_mgmt = db.NodeManagement()
port_mgmt = db.PortManagement()
link_mgmt = db.LinkManagement()


# GENERATE NODE INSTANCES AND INSERT THEM IN DATABASE
with open(nc.init_files_dir+'nodes.json') as f:
    node_data = json.load(f)
    f.close()
for node in node_data["node"]:
    node_tuple = [node["node_id"],  node["dpid"],  node["port_no"],  node["status"]]
    node_mgmt.add_node(node_tuple)
    
## GENERATE PORT INSTANCES AND INSERT THEM IN DATABASE
#with open(nc.init_files_dir+'ports.json') as f:
#    port_data = json.load(f)
#    f.close()
#for port in port_data["port"]:
#    port_tuple = [port["port_id"],  port["type"],  port["description"]]
#    port_mgmt.add_port(port_tuple)
#    
# GENERATE NODE TO PORT INSTANCES AND INSERT THEM IN DATABASE
with open(nc.init_files_dir+'node_to_port.json') as f:
    node_to_port_data = json.load(f)
    f.close()
for node_to_port in node_to_port_data["node_to_port"]:
    node_to_port_tuple = [node_to_port["node_id"],  node_to_port["port_id"], node_to_port["port_type"], node_to_port["status"]]
    node_mgmt.add_node_to_port(node_to_port_tuple)

# GENERATE LINK INSTANCES AND INSERT THEM IN DATABASE
with open(nc.init_files_dir+'link.json') as f:
    links = json.load(f)
    f.close()
for link in links["link"]:
    link_tuple = [link["link_id"],  link["tx_node"],  link["tx_node_port"],  link["rx_node"],  link["rx_node_port"],  link["amplifier_no"],  link["length"]]
    link_mgmt.add_link(link_tuple)
    
# GENERATE LINK TO CHANNEL INSTANCES AND INSERT THEM IN DATABASE
with open(nc.init_files_dir+'link_to_channel.json') as f:
    link_to_channels = json.load(f)
    f.close()
for link_to_channel in link_to_channels["link_to_channel"]:
    link_to_channel_tuple = [link_to_channel["link_id"],  link_to_channel["channel"]]
    link_mgmt.add_link_to_channel(link_to_channel_tuple)
