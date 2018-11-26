#!/usr/bin/env python
import math
from macros import *
#import cPickle
# Class definition of Optical Links considering the
# Mininet implementation.
PROP_TH = 0.01
class Link():
    def __init__(self, *args, **kwargs): 
        virtual_links = VIRTUAL_LINKS_DISTANCE
        # links = (src_node, dst_node, distance, EDFA_NO)
        self.links = {}
        # active_channels_per_link_original = {link_id: {span_id:  [{channel_id: power_level}, 
                                                                                    #{channel_id: noise_levels},
                                                                                    #{channel_id: amplifier_attenuation}]}}
        # Stores the values of each active channel without considering nonlinearities.
        self.active_channels_per_link_original = {}
        # Stores the values of each active channel considering nonlinearities.
        self.active_channels_per_link_nonlinear = {}
        dict_key = 0
        for link in virtual_links:
            src_node = link[0]
            dst_node = link[1]
            distance = link[2]
            
            try:
                span_no = math.ceil(distance/float(100))
                EDFA_NO = span_no + 1

                dict_key = dict_key + 1
                self.links[dict_key] = (src_node, dst_node, distance, EDFA_NO)
                self.active_channels_per_link_original[dict_key] = {}
                self.active_channels_per_link_nonlinear[dict_key] = {}
                for span_id in range(0, int(EDFA_NO+1)):
                    # Constructor of original active channels structure
                    self.active_channels_per_link_original[dict_key][span_id] = []
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # power levels
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # noise levels
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # amplifier attenuation
                    # Constructor of nonlinear active channels structure
                    self.active_channels_per_link_nonlinear[dict_key][span_id] = []
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # power levels
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # noise levels
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # amplifier attenuation
                dict_key = dict_key + 1
                self.links[dict_key] = (dst_node, src_node, distance, EDFA_NO)
                self.active_channels_per_link_original[dict_key] = {}
                self.active_channels_per_link_nonlinear[dict_key] = {}
                for span_id in range(0, int(EDFA_NO+1)):
                    # Constructor of original active channels structure (bi-directional link)
                    self.active_channels_per_link_original[dict_key][span_id] = []
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # power levels
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # noise levels
                    self.active_channels_per_link_original[dict_key][span_id].append({}) # amplifier attenuation
                    # Constructor of nonlinear active channels structure (bi-directional link)
                    self.active_channels_per_link_nonlinear[dict_key][span_id] = []
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # power levels
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # noise levels
                    self.active_channels_per_link_nonlinear[dict_key][span_id].append({}) # amplifier attenuation
            except:
                print("Class Link: Err: __init__: unable to allocate links_mapper!")
                
        print("Class Link: Instantiated Link object.")

    def get_link_distance(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    distance = link[2]
                    return distance
        except:
            print('Err: get_link_distance. Unable to compute link distance.')
            return -1
            
    
            
    def get_EDFA_NO(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    EDFA_NO = link[3]
                    return EDFA_NO
        except:
            print('Err: get_EDFA_NO. Unable to compute EDFA number.')
            return -1
            
    def get_link_ID(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    return link_id
        except:
            print('Err: get_link_ID. Unable to compute EDFA number.')
            return -1
            
    def get_active_channels_original(self, link_id, span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            return dict(self.active_channels_per_link_original[link_id][span_id][0])
        except:
            print('Err: get_active_channels_original: Unable to return active channels')
            return -1
            
    def get_active_channels_nonlinear(self, link_id, span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            return dict(self.active_channels_per_link_nonlinear[link_id][span_id][0])
        except:
            print('Err: get_active_channels_nonlinear: Unable to return active channels')
            return -1

    def get_count_active_channels(self,  link_id,  span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            return len(self.active_channels_per_link_original[link_id][span_id][0])
        except:
            print('Err: get_count_active_channels: Unable to return active channels')
            return -1

    def set_active_channel_original(self, link_id, span_id, channel, power_level,  noise_level,  amplifier_attenuation):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_original[link_id][span_id][0][channel] = power_level
            self.active_channels_per_link_original[link_id][span_id][1][channel] = noise_level
            self.active_channels_per_link_original[link_id][span_id][2][channel] = amplifier_attenuation
        except:
            print("Err: set_active_channel_original: Unable to insert active channel: %s" %channel)
            
    def set_active_channel_nonlinear(self, link_id, span_id, channel, power_level,  noise_level,  amplifier_attenuation):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_nonlinear[link_id][span_id][0][channel] = power_level
            self.active_channels_per_link_nonlinear[link_id][span_id][1][channel] = noise_level
            self.active_channels_per_link_nonlinear[link_id][span_id][2][channel] = amplifier_attenuation
        except:
            print("Err: set_active_channel_nonlinear: Unable to insert active channel: %s" %channel)
            
    def remove_active_channel_original(self,  link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_original[link_id][span_id][0].pop(channel)
            self.active_channels_per_link_original[link_id][span_id][1].pop(channel) 
            self.active_channels_per_link_original[link_id][span_id][2].pop(channel)
        except:
            print("Err: remove_active_channel_original: Unable to remove active channel: ", str(channel))
            
    def remove_active_channel_nonlinear(self,  link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_nonlinear[link_id][span_id][0].pop(channel)
            self.active_channels_per_link_nonlinear[link_id][span_id][1].pop(channel) 
            self.active_channels_per_link_nonlinear[link_id][span_id][2].pop(channel)
        except:
            print("Err: remove_active_channel_nonlinear: Unable to remove active channel: ", str(channel))
            
    def get_power_level_original(self, link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            return self.active_channels_per_link_original[link_id][span_id][0][channel]
        except:
            print("Err: get_power_level_original: Unable to retrieve power level channel: ", str(channel))
            
    def get_power_level_nonlinear(self, link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            return self.active_channels_per_link_nonlinear[link_id][span_id][0][channel]
        except:
            print("Err: get_power_level_nonlinear: Unable to retrieve power level channel: ", str(channel))
            
    def get_noise_level_original(self, link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            return self.active_channels_per_link_original[link_id][span_id][1][channel]
        except:
            print("Err: get_noise_level_original: Unable to retrieve noise level channel: ", str(channel))
            
    def get_noise_level_nonlinear(self, link_id, span_id, channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            return self.active_channels_per_link_nonlinear[link_id][span_id][1][channel]
        except:
            print("Err: get_noise_level_nonlinear: Unable to retrieve noise level channel: ", str(channel))
            
    def get_active_channels_power_noise_original(self,  link_id, span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            not_normalized_power = list(self.active_channels_per_link_original[link_id][span_id][0].values())
            not_normalized_noise = list(self.active_channels_per_link_original[link_id][span_id][1].values())
            return not_normalized_power,  not_normalized_noise
        except:
            print("Err: (Class Link) get_active_channels_power_noise_original: Unable to get power and noise levels: ")
            
    def get_active_channels_power_noise_nonlinear(self,  link_id, span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            elif span_id is -2:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-2] # get last amplifier span ID
            # first substract the amplifier attenuation of each channel (previously computed)
            not_normalized_power = []
            not_normalized_noise = []
            for channel_index in self.active_channels_per_link_nonlinear[link_id][span_id][0]:
                not_normalized_power.append(self.active_channels_per_link_nonlinear[link_id][span_id][0][channel_index]/self.active_channels_per_link_nonlinear[link_id][span_id][2][channel_index])
                not_normalized_noise.append(self.active_channels_per_link_nonlinear[link_id][span_id][1][channel_index]/self.active_channels_per_link_nonlinear[link_id][span_id][2][channel_index])
            return not_normalized_power,  not_normalized_noise
        except:
            print("Err: (Class Link) get_active_channels_power_noise_nonlinear: Unable to get power and noise levels: ")
            
    def get_channel_power_noise_nonlinear(self,  link_id, span_id,  channel):
        try:
            print("(Class Link) get_channel_power_noise_nonlinear: Received: %s - %s. Channel: %s" %(link_id, span_id,  channel))
            #print(self.active_channels_per_link_nonlinear)
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            elif span_id is -2:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-2] # get last amplifier span ID
            #print(self.active_channels_per_link_nonlinear[link_id][span_id][0].values())
            power = self.active_channels_per_link_nonlinear[link_id][span_id][0][channel]
            noise = self.active_channels_per_link_nonlinear[link_id][span_id][1][channel]
            return power,  noise
        except:
            print("Err: (Class Link) get_channel_power_noise_nonlinear: Unable to get power and noise levels: ")
            
    def get_channel_power_noise_original(self,  link_id, span_id,  channel):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            elif span_id is -2:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-2] # get last amplifier span ID
            power = self.active_channels_per_link_original[link_id][span_id][0][channel]
            noise = self.active_channels_per_link_original[link_id][span_id][1][channel]
            return power,  noise
        except:
            print("Err: (Class Link) get_channel_power_noise_original: Unable to get power and noise levels: ")
            
    def update_active_channels_original(self, link_id, span_id, active_channels_per_span):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_original[link_id][span_id][0] = active_channels_per_span
        except:
            print("Err: update_active_channels_original: Unable to update active channels at span: ", span_id)
            
    def update_active_channels_nonlinear(self, link_id, span_id, active_channels_per_span):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            self.active_channels_per_link_nonlinear[link_id][span_id][0] = active_channels_per_span
        except:
            print("Err: update_active_channels_nonlinear: Unable to update active channels at span: ", span_id)
            
    def update_active_channels_dict_original(self,  link_id, span_id, active_channels_per_span_list,  index):
        if span_id is -1:
            span_id = sorted(self.active_channels_per_link_original[link_id].keys())[-1] # get last span ID
        channels = [channel for channel in sorted(self.active_channels_per_link_original[link_id][span_id][0])]
        for i in range(0, len(channels)):
            channel_key = channels[i]
            self.active_channels_per_link_original[link_id][span_id][index][channel_key] = active_channels_per_span_list[i]
        return 0
        
    def update_active_channels_dict_nonlinear(self,  link_id, span_id, active_channels_per_span_list,  index):
        if span_id is -1:
            span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
        channels = [channel for channel in sorted(self.active_channels_per_link_nonlinear[link_id][span_id][0])]
        for i in range(0, len(channels)):
            channel_key = channels[i]
            self.active_channels_per_link_nonlinear[link_id][span_id][index][channel_key] = active_channels_per_span_list[i]
        return 0

    def zirngibl_srs (self, channel_powers, span_length):
		# Type channels_powers: dict - i.e. {2:-3.1, 85:-1.1}
		# Type span_length: float - i.e. 80.0
		# Return type:  dict - i.e. {2:-3.3, 85:-0.9}
        """This is a mathmatical model to estimate Stimulated Raman Scattering in SMF.
		wmo@optics.arizona.edu

		M. Zirngibl Analytical model of Raman gain effects in massive wavelength division multiplexed transmission systems, 1998.
		use Equation (10) for approximation
		Assumption 1: Raman gain shape as a triangle symmetric the central wavelength
		Assumption 2: Assume channel distribution symmetric to central wavelength
		Assumption 3: When calculating the SRS, assume equal power per-channel
		Assumption 4: SMF Aeff=80um^2, raman amplification band = 15THZ

		For more precise model, integrals need be calculated based on the input power spectrum using
		Equation (7)

		Args:
		channel_powers(dict): key->channel index, value: launch power in dBm
				       e.g., {2:-3.1, 85:-1.1}
				   
		span_length (float) - in kilometer, e.g., 80.0

		Return type:
		channel_powers(dict): -after SRS effect, key->channel index, value: launch power in dBm
				          e.g., {2:-3.3, 85:-0.9}
		"""
        c = 299792458.0 #Speed of light
        #m = 1.0
        nm = 1.0e-9 
        cm = 1.0e-2
        um = 1.0e-6
        km = 1.0e3
        THz = 1.0e12
        mW = 1.0e-3
        W = 1.0
        grid = 0.4*nm; #Assume 50GHz spacing DWDM
        min_wavelength_index = min(channel_powers.keys())
        max_wavelength_index = max(channel_powers.keys())
        wavelength_min = 1529.2*nm + min_wavelength_index*grid
        wavelength_max = 1529.2*nm + max_wavelength_index*grid
        frequency_min = c/(wavelength_max) #minimum frequency of longest wavelength
        frequency_max = c/(wavelength_min) #maximum frequency of shortest wavelength 
        Aeff = 80*um*um  #SMF effective area -> modified to 100 from 80  
        r = 7*10e-12*cm/float(W) #Raman Gain in SMF
        B = 15*THz; #Raman amplification band ~15THz
        beta = r/(2*Aeff*B)
        alpha_dB = -0.22/km; #SMF fiber attenuation in decibels/km
        alpha = 1-10**(alpha_dB/float(10)) #SMF fiber attenuation 
        Lspan = span_length*km #SMF span length 
        Leff = (1-math.e**(-alpha*Lspan))/alpha #SMF effective distance
        P0 = 0 #Total input power calculated by following loop
        
        for power_per_channel in channel_powers.values():
            P0 += power_per_channel*mW

#        For monitoring purposes (1/2)
#        counter = 0
#        raman_gain = {}

        #Calculate delta P for each channel
        for wavelength_index in channel_powers:  #Apply formula (10)
            wavelength = 1529.2*nm + wavelength_index*grid   
            frequency = c/wavelength #Frequency of the wavelength of interest
            R1 = beta*P0*Leff*(frequency_max-frequency_min)*math.e**(beta*P0*Leff*(frequency_max-frequency)) #term 1
            R2 = math.e**(beta*P0*Leff*(frequency_max-frequency_min))-1 #term 2
            delta_P = float(R1/R2) # Does the aritmetics in mW
            channel_powers[wavelength_index] *= delta_P
            
            # For monitoring purposes (2/2)
#            if len(channel_powers) is 90:
#                raman_gain[wavelength_index] = delta_P
#                counter += 1
#                if counter is 90:
#                    output_file = '/var/opt/Optical-Network-Emulation/agent-TCD-d2/logs/srs-gain/srs_gain_15THz.pkl'
#                    output = open(output_file,  'wb')
#                    cPickle.dump(raman_gain,  output)
#                    output.close()
        return channel_powers

    def normalize_channel_levels(self,  link_id,  span_id):
        try:
            if span_id is -1:
                span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
            # Calculate the main system gain of the loaded channels
            # (i.e. mean wavelength gain)
            loaded_gains_abs = self.active_channels_per_link_nonlinear[link_id][span_id][2].values()
            loaded_gains_dB = [self.abs_to_dB(x) for x in loaded_gains_abs]
            total_system_gain_dB = sum(loaded_gains_dB)
            channel_count = self.get_count_active_channels(link_id,  span_id)
            mean_system_gain_dB = total_system_gain_dB/float(channel_count)
            mean_system_gain_abs = self.dB_to_abs(mean_system_gain_dB)
            
            # Retrieve current power and noise levels
            power_levels = self.active_channels_per_link_nonlinear[link_id][span_id][0].values()
            noise_levels = self.active_channels_per_link_nonlinear[link_id][span_id][1].values()
            
            # Affect the power and noise with the mean of wavelength gain
            normalized_power = map(lambda x: abs(x[0]/float(mean_system_gain_abs)), zip(power_levels))
            normalized_noise = map(lambda x: abs(x[0]/float(mean_system_gain_abs)), zip(noise_levels))
            
            # Update the current power and noise levels with the "normalized" features.
            self.update_active_channels_dict_nonlinear(link_id,  span_id,  normalized_power,  0)
            self.update_active_channels_dict_nonlinear(link_id,  span_id,  normalized_noise,  1)
        except:
            print("Err: normalize_power_levels: Unable to normilize power levels channel: ", str(channel))
            
    def power_excursion_propagation(self, link_id,  span_id,  not_normalized_power,  not_normalized_noise):
        if span_id is -1:
            span_id = sorted(self.active_channels_per_link_nonlinear[link_id].keys())[-1] # get last span ID
        # Calculate total power values given by the form: P*N
        total_power = map(lambda x: abs(x[0]*x[1]+x[0]), zip(normalized_power, normalized_noise))
        total_power_old = map(lambda x: abs(x[0]*x[1]+x[0]), zip(not_normalized_power, not_normalized_noise))
        
        # Calculate excursion
        excursion = max(map(lambda x: x[0]/x[1], zip(total_power, total_power_old)))
        excursion_list = [excursion] * len(total_power)
        
        # Propagate power excursion
        power_excursion_prop = map(lambda x: x[0]*x[1], zip(total_power, excursion_list))
        
        # update current power levels with the excursion propagation
        self.update_active_channels_dict_nonlinear(link_id,  span_id,  power_excursion_prop,  0)
        
    def dB_to_abs(self, value):
        absolute_value = 10**(value/float(10))
        return absolute_value
        
    def abs_to_dB(self, value):
        dB_value = 10*np.log10(value)
        return dB_value
