#!/usr/bin/env python
import virtual_port_mapping
import os
import sys

vpm = virtual_port_mapping.main()

def _virtual_port_mapping(node_id, port):
    node = vpm[node_id]
    for _map in node:
        if(_map[0] == port):
            return _map[1]

def build_datapath_id(node_id):
	zeros = "00000000000000"
	if node_id < 16:
		if node_id < 10:
			datapath_id = zeros + "0" + str(node_id)
		else:
			datapath_id = zeros + "0" + str(hex(node_id)[2])
	else:
		datapath_id = zeros + str(hex(node_id)[2:4])
	return datapath_id

def build_json(datapath_id, message_id, ITU_standards, node_id, input_port_id, output_port_id, start_channel, end_channel, experiment1, experiment2):
	start = "{"
	body = ""
	end = "}"

	body = body + start
	body = body + '"' + "datapath_id" + '"' + ":"  + '"' + datapath_id + '"' + ","
	body = body + '"' + "message_id" + '"' + ":" + str(message_id) + ","
	body = body + '"' + "ITU_standards" + '"' + ":" + str(ITU_standards) + ","
	body = body + '"' + "node_id" + '"' + ":" + str(node_id) + ","
	body = body + '"' + "input_port_id" + '"' + ":" + str(input_port_id) + ","
	body = body + '"' + "output_port_id" + '"' + ":" + str(output_port_id) + ","
	body = body + '"' + "start_channel" + '"' + ":" + str(start_channel) + ","
	body = body + '"' + "end_channel" + '"' + ":" + str(end_channel) + ","
	body = body + '"' + "experiment1" + '"' + ":" + str(experiment1) + ","
	body = body + '"' + "experiment2" + '"' + ":" + str(experiment2)
	body = body + end

	return body

def build_file_name(index, flow_id):
	if index < 10:
		index_node = "0" + str(index)
	else:
		index_node = str(index)
	file_name = "json_rules/" + str(flow_id) + "/" + index_node + "_" + str(flow_id) + ".json"
	file_name_teardown = "json_rules/teardown/" + str(flow_id) + "/" + index_node + "_" + str(flow_id) + ".json"

	return file_name, file_name_teardown

def generate_file(file_name, rule):
	f = open(file_name,"w+")
	f.write(rule)

# Receives path in the form: (node, in_port, out_port)
def main(path, wavelength, flow_id):
	index = 0
	os.makedirs('json_rules/'+str(flow_id))
	os.makedirs('json_rules/teardown/'+str(flow_id))
	for node in path:
		first, second, third, node_id = str(node[0]).split('.')
		in_port = node[1]
		out_port = node[2]

		datapath_id = build_datapath_id(int(node_id))
		message_id = 116
		ITU_standards = 50
		node_id = node_id
		input_port_id = _virtual_port_mapping(int(node_id), in_port)
		output_port_id = _virtual_port_mapping(int(node_id), out_port)
		start_channel = wavelength
		end_channel = wavelength
		experiment1 = flow_id
		experiment2 = 0

		rule = build_json(datapath_id, message_id, ITU_standards, node_id, input_port_id, output_port_id, start_channel, end_channel, experiment1, experiment2)
		rule_teardown = build_json(datapath_id, 118, ITU_standards, node_id, input_port_id, output_port_id, start_channel, end_channel, experiment1, experiment2)

		file_name, file_name_teardown = build_file_name(index, flow_id)

		index = index + 1

		generate_file(file_name, rule)
		generate_file(file_name_teardown, rule_teardown)

if __name__=='__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
