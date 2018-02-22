""""
	Macros definition for Optical Agent

	Author: Alan A. Diaz Montiel
	Date: February 22nd, 2018
"""
import scipy.constants as sc

# Variables for noise computation
PLANCK_CONST = sc.h # 6.62607004e-34
SPEED_OF_LIGHT = sc.speed_of_light # 299792458.0
NOISE_FIGURE = 10**(6/float(10))
BANDWIDTH = 12.5*(10E9)

# Target/Launch signal power. Standard = -2dBm
TARGET_POWER = 10**(-2/float(10))
TARGET_GAIN = 20
IN_NOISE = 1e-10

# Link span between EDFAs
STANDARD_SPAN = int(100)