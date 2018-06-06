import math
import numpy as np

def abs_to_dB(value):
        dB_value = 10*np.log10(value)
        return dB_value

def calculate_SRS (channel_powers, span_length):
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
    
##test case
if __name__ == "__main__":
    channel_powers = {}
    #for channel_index in range(0,90,5):
    #    channel_powers[channel_index] = -2.0
    channel_powers = {0: 0.4210845044496888, 1: 0.42628593482763394, 2: 0.5294042118158662, 3: 0.6026210167221147, 4: 0.9375659638792795, 5: 0.6285915004893756, 6: 0.5362242601966705, 7: 0.9153279042649272, 8: 0.9410504146911375, 9: 0.685968953542166, 10: 0.9321327171281036, 11: 0.42416641272112976, 12: 0.3866707596149439, 13: 0.2893173187606887, 14: 0.7932594017043094, 15: 1.21620774444789, 16: 0.9554614237800422, 17: 0.8115138358678698, 18: 0.7656003163978915, 19: 0.32877014957162426, 20: 0.9776207571780182, 21: 0.6022114272099104, 22: 0.8764996953237844, 23: 0.927428103216074, 24: 0.139054242044582, 25: 0.40675263494959496}
    db_ch_pow = {}
    for key in channel_powers.keys():
        db_ch_pow[key] = abs_to_dB(channel_powers[key])
    #print(channel_powers)
    
    #print(db_ch_pow)
    span_length = 100.0
    a = calculate_SRS(channel_powers,span_length)
    db_ch = {}
    for key in a.keys():
        db_ch[key] = abs_to_dB(a[key])
    print(db_ch)
    print("#################################################")
    print("#################################################")
    print("#################################################")
    b = calculate_SRS(db_ch_pow,span_length)
    print(b)
