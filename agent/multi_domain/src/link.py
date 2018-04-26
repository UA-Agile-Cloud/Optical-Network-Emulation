#!/usr/bin/env python
import math
from macros import *
# Class definition of Optical Links considering the
# Mininet implementation.
class Link():
    # +300km
    def __init__(self, *args, **kwargs): 
        virtual_links = VIRTUAL_LINKS_DISTANCE
        # links = (node, dst_node, distance, EDFA_NO)
        self.links = {}
        # active_channels_per_link = {link_id: {span_id:  {channel_id: power_level}}}
        self.active_channels_per_link = {}
        dict_key = 0
        for link in virtual_links:
            src_node = link[0]
            dst_node = link[1]
            distance = link[2]
            
            try:
                span_no = math.ceil(distance/float(100))
                EDFA_NO = span_no + 1
                if EDFA_NO == 2:
                    EDFA_NO = 1
                dict_key = dict_key + 1
                self.links[dict_key] = (src_node, dst_node, distance, EDFA_NO)
                self.active_channels_per_link[dict_key] = {}
                for span_id in range(0, int(EDFA_NO)):
                    self.active_channels_per_link[dict_key][span_id] = {}
                dict_key = dict_key + 1
                self.links[dict_key] = (dst_node, src_node, distance, EDFA_NO)
                self.active_channels_per_link[dict_key] = {}
                for span_id in range(0, int(EDFA_NO)):
                    self.active_channels_per_link[dict_key][span_id] = {}
            except:
                print("Err: __init__: unable to allocate links_mapper!")
                
        print("Instantiated Link object.")

    def get_link_distance(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    distance = link[2]
                    return distance
        except:
            print('Err: get_link_distance. Unable to compute link distance.')
            return 1
            
    def get_EDFA_NO(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    EDFA_NO = link[3]
                    return EDFA_NO
        except:
            print('Err: get_EDFA_NO. Unable to compute EDFA number.')
            return 1
            
    def get_link_ID(self, src_node, dst_node):
        try:
            for link_id in self.links:
                link = self.links[link_id]
                if(link[0] == src_node) and (link[1] == dst_node):
                    return link_id
        except:
            print('Err: get_link_ID. Unable to compute EDFA number.')
            return 1
            
    def get_active_channels(self, link_id, span_id):
        try:
            return self.active_channels_per_link[link_id][span_id]
        except:
            print('Err: get_active_channels: Unable to return active channels')
            return 1
            
    def set_active_channel(self, link_id, span_id, channel, power_level):
        try:
            print("set_active_channel")
            print(self.active_channels_per_link[link_id])
            print(self.active_channels_per_link[link_id][span_id])
            print("power_level: ", power_level)
            self.active_channels_per_link[link_id][span_id][channel] = power_level
            print(self.active_channels_per_link[link_id][span_id][channel])
        except:
            print("Err: set_active_channel: Unable to insert active channel: ", str(channel))
            
    def get_power_level(self, link_id, span_id, channel):
        try:
            print("get_power_level")
            print(str(self.active_channels_per_link[link_id][span_id]))
            print("For _lambda: ", channel)
            return self.active_channels_per_link[link_id][span_id][channel]
        except:
            print("Err: get_power_level: Unable to retrieve power level channel: ", str(channel))
            
    def update_active_channels(self, link_id, span_id, active_channels_per_span):
        try:
            self.active_channels_per_link[link_id][span_id] = active_channels_per_span
        except:
            print("Err: update_active_channels: Unable to update active channels at span: ", span_id)
            
    def calculate_SRS (self, channel_powers, span_length):
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
        Aeff = 80*um*um  #SMF effective area  
        r = 7*1e-12*cm/W #Raman Gain
        B = 15*THz; #Raman amplification band ~15THz
        beta = r/(2*Aeff*B)
        alpha_dB = -0.2/km; #SMF fiber attenuation in decible
        alpha = 1-10**(alpha_dB/10) #SMF fiber attenuation 
        Lspan = span_length*km #SMF span length 
        Leff = (1-math.e**(-alpha*Lspan))/alpha #SMF effective distance
        P0 = 0 #Total input power calculated by following loop
        for power_per_channel in channel_powers.values():
            P0 += 10**(power_per_channel/10.0)*mW

        #Calculate delta P for each channel
        for wavelength_index in channel_powers:  #Apply formula (10)
            wavelength = 1529.2*nm + wavelength_index*grid   
            frequency = c/wavelength #Frequency of the wavelength of interest
            R1 = beta*P0*Leff*(frequency_max-frequency_min)*math.e**(beta*P0*Leff*(frequency_max-frequency)) #term 1
            R2 = math.e**(beta*P0*Leff*(frequency_max-frequency_min))-1 #term 2
            delta_P = 10*math.log10(R1/R2)
            channel_powers[wavelength_index] += round(delta_P,2)
        return channel_powers
