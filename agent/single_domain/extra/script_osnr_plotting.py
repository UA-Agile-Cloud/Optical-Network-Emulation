#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches

f1_abs_osnr_list = [2485.105623327059, 1178.1481501945937, 744.0547667878906, 528.1711820928421, 399.5645587780784, 314.5890313770088, 254.53791895947688, 210.05678472595605, 175.9477953474866, 149.09146978364637]
f1_db_osnr_list = [10*math.log10(x) for x in f1_abs_osnr_list]

f2_abs_osnr_list = [2493.122091081123, 1092.6190972433021, 635.2293573312866, 413.4051704723448, 285.57896128205067, 204.5207861983402, 149.9617697869159, 111.75033958320152, 84.2375882425461, 64.0310768516993]
f2_db_osnr_list = [10*math.log10(x) for x in f2_abs_osnr_list]

f3_abs_osnr_list = [2521.981374889333, 1450.2367488971036, 1103.6370206682395, 937.9717130174128, 844.3104531117812, 786.2869630999917, 748.2837336475901, 722.477979140532, 704.5224740422509, 691.8162563104464]
f3_db_osnr_list = [10*math.log10(x) for x in f3_abs_osnr_list]

x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
plt.plot(x, f1_db_osnr_list, 'r--', 
		 x, f2_db_osnr_list, 'bs', 
		 x, f3_db_osnr_list, 'g^')

red_patch = mpatches.Patch(color='red', label='rf=-1.07815362800000')
blue_patch = mpatches.Patch(color='blue', label='rf=-0.450616586000000')
green_patch = mpatches.Patch(color='green', label='rf=1.31347481872000')

plt.legend(handles=[red_patch, blue_patch, green_patch])

plt.title('OSNR performance through 10 hops with different ripple functions (rf)')
plt.xlabel('Nodes')
plt.ylabel('dB')
plt.axis([1,10, 10, 40])
plt.grid(True)

plt.show()
