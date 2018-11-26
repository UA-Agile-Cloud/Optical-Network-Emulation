# Build json with network configuration for a LINEAR topology
# PORTS
import json

# Structures as given in database
port_id_struct = "port_id"
type_struct = "type"
description_struct = "description"

# Definition of base values
port_no = 6
port_tx_type = 0
port_rx_type = 1
tx_description = "TX port"
rx_description = "RX port"
port = {"port":[]}
for port_id in range(1, port_no+1):
    if port_id%2 is 0:
        port_type = port_rx_type
        description = rx_description
    else:
        port_type = port_tx_type
        description = tx_description
    new_port = {port_id_struct: port_id,  type_struct: port_type,  description_struct: description}
    port["port"].append(new_port)

# Create json file to be stored in the json folder
# and called by the network builder
with open('ports.json', 'w') as fp:
    json.dump(port, fp)
    fp.close()
