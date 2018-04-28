"""
"	Ripple function class
	Maintains a register of ripple functions and links with EDFAs
"""
import link_distance_mapping
import os
import random
import numpy as np

directory = '/var/opt/Optical-Network-Emulation/agent/multi_domain/src/function-files/'

class AmplifierAttenuation():
	functions = {} # Function ID (Integer): Y points (List of Floats)
	amplifier_attenuation = {} # Link ID (Integer): Function IDs (List of Integers) 

	def __init__(self, *args, **kwargs):
		self.link_distance_mapping = link_distance_mapping.main()
		self.set_functions()
		self.set_amplifier_attenuation()
		print("Instantiated AmplifierAttenuation object.")

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
				func_id = func_id + 1
		except:
			print('Err: set_amplifier_attenuation. Unable to initialize functions.')

	def get_amplifier_attenuation(self, link_id):
		return self.amplifier_attenuation[link_id]
		# try:
		# 	return self.amplifier_attenuation[link_id]
		# except:
		# 	print('Err: set_functions. There is no amplifier_attenuation with that ID.')

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
			for link_id in self.link_distance_mapping:
				if link_id%2 is not 0:
					link = self.link_distance_mapping[link_id]
					amplifier_no = int(link[3])
					functions_ID = []
					for EDFA in range(1,amplifier_no + 1):
						functions_ID.append(random.randint(1,len(self.functions)))
					self.amplifier_attenuation[link_id] = functions_ID
					self.amplifier_attenuation[link_id+1] = functions_ID[::-1]
		except:
			print('Err: set_amplifier_attenuation. Unable to initialize amplifier_attenuation.')
			return 1

	def dB_to_abs(self, value):
		absolute_value = 10**(value/float(10))
		return absolute_value
