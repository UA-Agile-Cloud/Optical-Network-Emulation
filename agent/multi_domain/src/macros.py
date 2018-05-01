""""
	Macros definition for Optical Agent

	Author: Alan A. Diaz Montiel
	Date: February 22nd, 2018
"""
import scipy.constants as sc

CHANNEL_NUMBER = 90

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

# For remote mininet client
MININET_SERVER_PORT = 20001
MININET_SERVER_IP = '134.226.55.100'
#MININET_SERVER_IP = '127.0.0.1'

telefonica_links_distance = [	(1, 2, 590),
			(1, 3, 660),			
			(2, 3, 550),
			(2, 4, 490),
			(3, 5, 450),
			(3, 7, 660),
			(4, 5, 490),
			(4, 10, 410),
			(5, 6, 460),
			(5, 8, 650),
			(6, 9, 480),
			(7, 9, 690),
			(7, 14, 660),
			(7, 15, 640),
			(8, 9, 460),
			(8, 11, 660),
			(8, 12, 645), 
			(9, 13, 650),
			(10, 11, 610),
			(10, 21, 890),
			(11, 20, 610),
			(11, 21, 605),
			(12, 13, 530),
			(12, 19, 445),
			(12, 20, 730),
			(13, 14, 660),
			(13, 18, 545),
			(14, 15, 540),
			(14, 17, 640),
			(15, 16, 510),
			(16, 17, 730),
			(17, 18, 520),
			(18, 19, 530),
			(19, 20, 650),
			(20, 21, 410)]
            
telefonica_virtual_ports_per_node = [	3,
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
                
telefonica_virtual_links = [	(1, 2),
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
            
small_linear_links_distance = [	(1, 2, 300),
			(2, 3, 300),			
			(3, 4, 300),
			(4, 5, 300)]
            
small_linear_virtual_ports_per_node = [	2,
				3,
				3,
				3,
				2]
                
small_linear_virtual_links= [	(1, 2),
			(2, 3),			
			(3, 4),
			(4, 5)]

VIRTUAL_LINKS_DISTANCE = small_linear_links_distance
VIRTUAL_PORTS_PER_NODE = small_linear_virtual_ports_per_node
VIRTUAL_LINKS = small_linear_virtual_links
#VIRTUAL_LINKS_DISTANCE = telefonica_links_distance
#VIRTUAL_PORTS_PER_NODE = telefonica_virtual_ports_per_node
#VIRTUAL_LINKS = telefonica_virtual_links
