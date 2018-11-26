# Database procedures (INSERT, SELECT, UPDATE)

insert_node = ("INSERT INTO node "
               "(node_id, dpid, ports_no, status) "
               "VALUES (%s, %s, %s, %s)")

n_insert_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: add_node(self,  node_data). \nNew node added successfully.'
n_insert_error_message = 'ERROR:\nClass: DatabaseManagemen.NodeManagement. \nFunction: add_node(self,  node_data). \nUnable to add new node.'

select_node_all = ("SELECT * FROM node")

n_select_all_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: select_node_all(self). \nNodes selected successfully.'
n_select_all_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: select_node_all(self). \nUnable to select all nodes.'

select_node_with_id = ("SELECT * FROM node "
                            "WHERE node_id = %s")
                            
n_select_node_with_id_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: select_node_with_id(self, node_id). \nNode selected successfully.'
n_select_node_with_id_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: select_node_with_id(self, node_id). \nUnable select node.'

select_node_with_dpid = ("SELECT * FROM node "
                            "WHERE dpid = %s")
                            
n_select_success_message_with_dpid = 'Class: DatabaseManagement.NodeManagement. \nFunction: select_node_with_dpid(self, dpid). \nNode selected successfully.'
n_select_success_message_with_dpid = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: select_node_with_dpid(self, dpid). \nUnable to select node.'

update_node_status_with_ID = ("UPDATE node SET node.status = %s "
                                                    "WHERE node_id = %s")
                                                    
n_update_node_status_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: update_node_status(self, new_status, node_id). \nNode status updated successfully.'
n_update_node_status_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: update_node_status(self, new_status, node_id). \nUnable to update node status.'

count_node_all = ("SELECT COUNT(*) FROM node")
                                                    
n_count_all_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: count_node_all(self). \nNodes counted successfully.'
n_count_all_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: count_node_all(self). \nUnable to count nodes.'


insert_node_to_port = ("INSERT INTO node_to_port "
                        "(node_id, port_id, port_type, status) "
                        "VALUES (%s, %s, %s, %s)")
                        
ntp_insert_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: add_node_to_port(self, node_to_port_data). \nNew node_to_port relation added successfully.'
ntp_insert_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: add_node_to_port(self, node_to_port_data). \nUnable to add new node_to_port relation.'

select_rx_port_id = ("SELECT port_id FROM node_to_port "
                        " WHERE node_id = %s AND "
                        " port_type = 1")
                        
ntp_select_rx_port_id_success_message = 'Class: DatabaseManagement.NodeManagement. \nFunction: select_rx_port_id(self). \nRX port_id successfully.'
ntp_select_rx_port_id_error_message = 'ERROR:\nClass: DatabaseManagement.NodeManagement. \nFunction: select_rx_port_id(self). \nUnable to select RX port_id.'

# PORT CLASS

insert_port = ("INSERT INTO port "
                        "(port_id, type, description) "
                        "VALUES (%s, %s, %s)")
                        
p_insert_success_message = 'Class: DatabaseManagement.PortManagement. \nFunction: add_port(self, port_data). \nNew port added successfully.'
p_insert_error_message = 'ERROR:\nClass: DatabaseManagement.PortManagement. \nFunction: add_port(self, port_data). \nUnable to add new port.'

# LINK CLASS

insert_link = ("INSERT INTO link "
                        "(link_id, tx_node, tx_node_port, rx_node, rx_node_port, amplifier_no, length) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)")
                        
l_insert_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: add_link(self, link_data). \nNew link added successfully.'
l_insert_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: add_link(self, link_data). \nUnable to add new link.'

insert_link_to_channel = ("INSERT INTO link_to_channel "
                        "(link_id, channel) "
                        "VALUES (%s, %s)")
                        
ltc_insert_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: add_link_to_channel(self, link_to_channel_data). \nNew link_to_channel added successfully.'
ltc_insert_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: add_link_to_channel(self, link_to_channel_data). \nUnable to add new link_to_channel.'

select_link_id_with_nodes = ("SELECT link_id FROM link "
                                                "WHERE tx_node = %s AND rx_node = %s")

l_select_link_id_with_nodes_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: select_link_id_with_nodes(self, nodes_data). \nLink ID selected successfully.'
l_select_link_id_with_nodes_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: select_link_id_with_nodes(self, nodes_data). \nUnable to select Link ID.'

select_link_with_id = ("SELECT * FROM link "
                                                "WHERE link_id = %s")

l_select_link_with_id_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: select_link_with_id(self, link_id). \nLink selected successfully.'
l_select_link_with_id_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: select_link_with_id(self, link_id). \nUnable to select Link.'


select_link_all = ("SELECT * FROM link")

l_select_all_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: select_link_all(self). \nLinks selected successfully.'
l_select_all_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: select_link_all(self). \nUnable to select all links.'

select_available_channels = ("SELECT * FROM link_to_channel "
                                                "WHERE link_id = %s AND "
                                                "lightpath_id = 0")

l_select_available_channels_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: select_available_channels(self, link_id). \nAvailable channels selected successfully.'
l_select_available_channels_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: select_available_channels(self, link_id). \nUnable to select available channels.'

# TRAFFIC CLASS

insert_lightpath = ("INSERT INTO lightpath "
                        "(lightpath_id, tx_node, rx_node) "
                        "VALUES (%s, %s, %s)")
                        
t_insert_success_message = 'Class: DatabaseManagement.TrafficManagement. \nFunction: create_lightpath(self, lightpath_data). \nNew lightpath created successfully.'
t_insert_error_message = 'ERROR:\nClass: DatabaseManagement.TrafficManagement. \nFunction: create_lightpath(self, lightpath_data). \nUnable to create new lightpath.'

update_lightpath = ("UPDATE lightpath SET lightpath.status = %s, lightpath.start_timestamp = %s "
                        "WHERE lightpath_id = %s")
                        
t_update_success_message = 'Class: DatabaseManagement.TrafficManagement. \nFunction: update_lightpath(self, lightpath_data). \nLightpath updated successfully.'
t_update_error_message = 'ERROR:\nClass: DatabaseManagement.TrafficManagement. \nFunction: update_lightpath(self, lightpath_data). \nUnable to update lightpath.'

t_get_nodes_with_id = ("SELECT tx_node, rx_node FROM lightpath "
                        "WHERE lightpath_id = %s")
                        
t_get_nodes_success_message = 'Class: DatabaseManagement.TrafficManagement. \nFunction: t_get_nodes_with_id(self, lightpath_id). \nNodes selected successfully.'
t_get_nodes_error_message = 'ERROR:\nClass: DatabaseManagement.TrafficManagement. \nFunction: t_get_nodes_with_id(self, lightpath_id). \nUnable to select nodes.'


insert_route = ("INSERT INTO route "
                        "(lightpath_id, sequence, link_id) "
                        "VALUES (%s, %s, %s)")
                        
r_insert_success_message = 'Class: DatabaseManagement.TrafficManagement. \nFunction: add_route(self, route_data). \nNew route added successfully.'
r_insert_error_message = 'ERROR:\nClass: DatabaseManagement.TrafficManagement. \nFunction: add_route(self, route_data). \nUnable to add new route.'

update_link_to_channel_link = ("UPDATE link_to_channel SET link_to_channel.lightpath_id = %s "
                                                    "WHERE link_id = %s AND channel = %s")
                        
ltc_update_link_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: update_link_to_channel(self, link_to_channel_data). \nlink_to_channel updated successfully.'
ltc_update_link_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: update_link_to_channel(self, link_to_channel_data). \nUnable to update link_to_channel.'

cancel_lightpath = ("DELETE FROM lightpath "
                                                    "WHERE lightpath_id = %s")
                        
lp_cancel_lightpath_success_message = 'Class: DatabaseManagement.LinkManagement. \nFunction: cancel_lightpath(self, lightpath_id). \Lightpath cancelled successfully.'
lp_cancel_lightpath_error_message = 'ERROR:\nClass: DatabaseManagement.LinkManagement. \nFunction: cancel_lightpath(self, lightpath_id). \nUnable to cancel lightpath.'
