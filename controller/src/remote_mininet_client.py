#!/usr/bin/env python
import socket
import sys
import json

MININET_SERVER_PORT = 20001
#MININET_SERVER_IP = '10.129.36.255'
#MININET_SERVER_IP = '134.226.55.100'
MININET_SERVER_IP = '127.0.0.1'

def main(flow_id, src_node, dst_node, wavelength):

	remote_mininet_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	mininet_server_address = (MININET_SERVER_IP, MININET_SERVER_PORT)
	remote_mininet_client_sock.connect(mininet_server_address)
	print("Connection OK.")
	try:
	    # Send data
	    remote_mininet_client_sock.send(json.dumps({'flow_id':flow_id, 'src_node':src_node, 'dst_node':dst_node, 'wavelength':wavelength}))
	    print("JSON sent.")
	    remote_mininet_client_sock.close()
	except:
	    print("Err: fail to connect to Remote Mininet handler.")

if __name__=='__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
