#!/usr/bin/env python
virtual_ports_per_node = [	3,
				4,
				5,
				4,
				5,
				3,
				5,
				5,
				5,
				4,
				5,
				5,
				5,
				5,
				4,
				3,
				4,
				4,
				4,
				5,
				4]

virtual_links = [	(1, 2),
			(1, 3),			
			(2, 3),
			(2, 4),
			(3, 5),
			(3, 7),
			(4, 5),
			(4, 10),
			(5, 6),
			(5, 8),
			(6, 9),
			(7, 9),
			(7, 14),
			(7, 15),
			(8, 9),
			(8, 11),
			(8, 12), 
			(9, 13),
			(10, 11),
			(10, 21),
			(11, 20),
			(11, 21),
			(12, 13),
			(12, 19),
			(12, 20),
			(13, 14),
			(13, 18),
			(14, 15),
			(14, 17),
			(15, 16),
			(16, 17),
			(17, 18),
			(18, 19),
			(19, 20),
			(20, 21)]

def main():

	node_to_ports = {}
	dict_key = 1
	for node in virtual_ports_per_node:
		_list = []
		i=1
		for port in range(i,2*node+1):
			_list.append(port)
		node_to_ports[dict_key] = _list
		dict_key = dict_key + 1

	virtual_node_to_ports = {}
	dict_key = 1
	for node in virtual_ports_per_node:
		_list = []
		i=1
		for port in range(i,node+1):
			_list.append(port)
		virtual_node_to_ports[dict_key] = _list
		dict_key = dict_key + 1

	virtual_port_mapping = {0: []}
	dict_key = 0
	for link in virtual_links:
		src_node = link[0]
		dst_node = link[1]
	
		src_port = node_to_ports[src_node].pop(1)
		dst_port = node_to_ports[dst_node].pop(2)

		try: 
			virtual_src_port = virtual_node_to_ports[src_node].pop(1)
			virtual_dst_port = virtual_node_to_ports[dst_node].pop(1)

			if src_node not in virtual_port_mapping.keys():
				virtual_port_mapping[src_node] = []
			virtual_port_mapping[src_node].append((src_port, virtual_src_port))
			if dst_node not in virtual_port_mapping.keys():
				virtual_port_mapping[dst_node] = []
			virtual_port_mapping[dst_node].append((dst_port, virtual_dst_port))
		except:
			print('=====================')
			print('Err: pop index out of range for link: ' + str(src_node) + " --- " + str(dst_node))
			print(virtual_node_to_ports[src_port])
			print(virtual_node_to_ports[dst_port])

		# Bidirectional link

		src_port = node_to_ports[dst_node].pop(1)
		dst_port = node_to_ports[src_node].pop(1)
		virtual_port_mapping[dst_node].append((src_port, virtual_dst_port))
		virtual_port_mapping[src_node].append((dst_port, virtual_src_port))

	i = 1
	for node in virtual_ports_per_node:
		ports_no = node*2
		virtual_port_mapping[i].append((1, 1))
		virtual_port_mapping[i].append((ports_no, 1))
		i = i + 1

	return virtual_port_mapping

if __name__=='__main__':
    sys.exit(main)
