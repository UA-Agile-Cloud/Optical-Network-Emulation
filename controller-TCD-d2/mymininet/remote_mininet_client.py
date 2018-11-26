#!/usr/bin/env python
import socket
import sys
import json
from mininet_config import MININET_SERVER_IP, MININET_SERVER_PORT

def main(flow_id, src_node, dst_node, wavelength):

	remote_mininet_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	mininet_server_address = (MININET_SERVER_IP, MININET_SERVER_PORT)
	remote_mininet_client_sock.connect(mininet_server_address)
	print("Remote Mininet Client: Connection OK.")
	try:
	    # Send data
	    remote_mininet_client_sock.send(json.dumps({'flow_id':flow_id, 'src_node':src_node, 'dst_node':dst_node, 'wavelength':wavelength}))
	    print("Remote Mininet Client: JSON sent with: flow_id: %s, src_node: %s, dst_node: %s, wavelength: %s" %(flow_id, src_node, dst_node, wavelength))
	    remote_mininet_client_sock.close()
	except:
	    print("Remote Mininet Client: Err: fail to connect to Remote Mininet handler.")

if __name__=='__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
