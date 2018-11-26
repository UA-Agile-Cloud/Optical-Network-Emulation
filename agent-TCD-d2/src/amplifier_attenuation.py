"""
"	Ripple function class
	Maintains a register of ripple functions and links with EDFAs
"""
import os
import random
import numpy as np
import macros
import math

directory = '/var/opt/Optical-Network-Emulation/agent-TCD-d2/src/function-files/'

class AmplifierAttenuation():
    functions = {} # Function ID (Integer): Y points (List of Floats)
    amplifier_attenuation = {} # Link ID (Integer): Function IDs (List of Integers) 
    
    def __init__(self, *args, **kwargs):
        self.link_distance_mapper = self.set_link_distance()
        self.set_functions()
        self.set_amplifier_attenuation()
        print("Class AmplifierAttenuation: Instantiated AmplifierAttenuation object.")
        
    def get_function(self, func_id):
        try:
            return self.functions[func_id]
        except:
            print('Err: get_function. There is no function with that ID.')
            
    def set_functions(self):
        try:
			# Read file
            func_id = 1
            for _file in os.listdir(directory):
                data = open(directory + _file)
                data_dB = [float(x.strip()) for x in data.readlines()]
                data_abs = [self.dB_to_abs(float(value)) for value in data_dB]
                self.functions[func_id] = data_abs
                func_id += 1
        except:
            print('Err: set_amplifier_attenuation. Unable to initialize functions.')
            
    def get_amplifier_attenuation(self, link_id):
        return self.amplifier_attenuation[link_id]
        
    def get_mean_amplifier_attenuation(self, link_id, _lambda):
        try:
            functions = []
            amplifier_attenuation = self.amplifier_attenuation[link_id]
            for function_ID in amplifier_attenuation:
                functions.append(self.functions[function_ID][_lambda])
            return np.mean(functions)
        except:
            print('Err: set_functions. Unable to get_mean_amplifier_attenuation with that ID.')
    
    # Retrieves the number of EDFAs per link in the network.
	# Assigns a random function (1, 21) to each of the EDFAs
	# in each link.        
    def set_amplifier_attenuation(self):
        try:
            for link_id in self.link_distance_mapper:
                if link_id%2 is not 0:
                    link = self.link_distance_mapper[link_id]
                    amplifier_no = int(link[3])
                    functions_ID = []
                    for EDFA in range(0,amplifier_no):
                        functions_ID.append(random.randint(1,len(self.functions)))
                    self.amplifier_attenuation[link_id] = functions_ID
                    self.amplifier_attenuation[link_id+1] = functions_ID[::-1]
        except:
            print('Err: set_amplifier_attenuation. Unable to initialize amplifier_attenuation.')
            return 1
            
    def set_link_distance(self):
        link_distance_mapper = {}
        dict_key = 0
        for link in macros.VIRTUAL_LINKS_DISTANCE:
            src_node = link[0]
            dst_node = link[1]
            distance = link[2]
            try:
                EDFA_NO = math.ceil(distance/float(100)) + 1
                dict_key = dict_key + 1
                link_distance_mapper[dict_key] = (src_node, dst_node, distance, EDFA_NO)
                dict_key = dict_key + 1
                link_distance_mapper[dict_key] = (dst_node, src_node, distance, EDFA_NO)
            except:
                print('Class AmplifierAttenuation: Err: set_link_distance: unable to allocate link_distance_mapper!')
        return link_distance_mapper
            
    def dB_to_abs(self, value):
        absolute_value = 10**(value/float(10))
        return absolute_value
