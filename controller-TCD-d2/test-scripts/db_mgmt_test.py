import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-new')
import database_management
import json

################ NODE MANAGEMENT TEST

#db_mgmt = database_management.DatabaseManagement.NodeManagement()

# INSERT TEST
#with open('insert_node.json') as f:
#    data = json.load(f)
#
#node = data["node"][0]
#node_tuple = [node["node_id"],  node["dpid"],  node["port_no"],  node["status"]]
#db_mgmt.add_node(node_tuple)

# END INSERT TEST

#node_id = 1
#dpid = "0000000000000001"

# SELECT TEST
#cursor_data = db_mgmt.select_node_with_dpid(dpid)
#for (node_id, dpid, ports_no, status)  in cursor_data:
#    print("Data of node: %s \nDPID: %s PORTS_NO: %s STATUS: %s"  % (node_id,  dpid, ports_no, status))
# END SELECT TEST

# UPDATE TEST
#db_mgmt.update_node_status(1,  2)
# END UPDATE TEST

################ END NODE MANAGEMENT TEST


########### PORT MANAGEMENT TEST

#db_mgmt = database_management.DatabaseManagement.PortManagement()
#
## INSERT TEST
#with open('insert_port.json') as f:
#    data = json.load(f)
#
#port = data["port"][0]
#port_tuple = [port["port_id"],  port["type"]]
#db_mgmt.add_port(port_tuple)

# END INSERT TEST

########### END PORT MANAGEMENT TEST


########### NODE_TO_PORT MANAGEMENT TEST

#db_mgmt = database_management.DatabaseManagement.NodeToPortManagement()
#
## INSERT TEST
#with open('insert_node_to_port.json') as f:
#    data = json.load(f)
#
#node_to_port = data["node_to_port"][0]
#node_to_port_tuple = [node_to_port["node_id"],  node_to_port["port_id"]]
#db_mgmt.add_node_to_port(node_to_port_tuple)

# END INSERT TEST

########### END NODE_TO_PORT MANAGEMENT TEST


########### LINK MANAGEMENT TEST

#db_mgmt = database_management.DatabaseManagement.LinkManagement()
#
### INSERT TEST
##with open('insert_link.json') as f:
##    data = json.load(f)
##
##link = data["link"][0]
##link_tuple = [link["link_id"],  link["tx_node"],  link["tx_node_port"],  link["rx_node"],  link["rx_node_port"],  link["amplifier_no"],  link["length"]]
##db_mgmt.add_link(link_tuple)
##
### END INSERT TEST
#
## INSERT LINK_TO_CHANNEL TEST
#with open('insert_link_to_channel.json') as f:
#    data = json.load(f)
#
#link = data["link_to_channel"][0]
#link_tuple = [link["link_id"],  link["channel"]]
#db_mgmt.add_link_to_channel(link_tuple)
#
## END INSERT LINK_TO_CHANNEL TEST

########### END LINK MANAGEMENT TEST

########### TRAFFIC MANAGEMENT TEST

db_mgmt = database_management.DatabaseManagement.TrafficManagement()

## INSERT LIGHTPATH TEST
#with open('insert_lightpath.json') as f:
#    data = json.load(f)
#
#lightpath = data["lightpath"][0]
#lightpath_tuple = [lightpath["lightpath_id"],  lightpath["tx_node"],  lightpath["rx_node"],  lightpath["status"]]
#db_mgmt.add_lightpath(lightpath_tuple)

# END INSERT LIGHTPATH TEST

# INSERT ROUTE TEST
with open('insert_route.json') as f:
    data = json.load(f)

route = data["route"][0]
route_tuple = [route["r_lightpath_id"],  route["sequence"],  route["r_link_id"]]
db_mgmt.add_route(route_tuple)

# END INSERT ROUTE TEST


########### END TRAFFIC MANAGEMENT TEST
