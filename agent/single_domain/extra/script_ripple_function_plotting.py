#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches

#ripple_function_file='/home/ubuntu1/Alan/ArizonaEx/single_domain/ryu_optical_agent/ripple_function_dB.txt'
ripple_function_file='/home/ubuntu1/Alan/ArizonaEx/single_domain/ryu_optical_agent/reversed_ripple_function_dB.txt'


data = open(ripple_function_file)
ripple_function_dB = [float(x.strip()) for x in data.readlines()]

x = []
i = 0
for rf in ripple_function_dB:
	i = i + 1
	x.append(i)

plt.plot(x, ripple_function_dB, 'b')

plt.title('Reversed ripple function for 90 wavelengths')
#plt.title('Ripple function for 90 wavelengths')
plt.xlabel('wavelength')
plt.ylabel('ripple function')
plt.axis([1,90, -2, 2])
plt.grid(True)

plt.show()
