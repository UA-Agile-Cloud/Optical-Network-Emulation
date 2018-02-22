#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches


f1_abs_osnr_list = [9893.37635300491, 532.4253709669731, 259.76631309526147, 165.65699518790848, 150.4671563106466, 149.50760471949565, 116.48392412518766, 100.79684785373355, 92.06137647546377, 90.67065862114964]
f1_db_osnr_list = [10*math.log10(x) for x in f1_abs_osnr_list]

f2_abs_osnr_list = [9925.290438596978, 465.6500920931123, 209.59652203068703, 122.9425210724268, 108.49980515773413, 107.47866727155109, 69.11588112774311, 51.82539064930161, 42.003560306325866, 40.21416710729212]
f2_db_osnr_list = [10*math.log10(x) for x in f2_abs_osnr_list]

f3_abs_osnr_list = [10040.181145041774, 789.7839417992765, 469.86303126058823, 361.6124531649381, 346.78155489829936, 346.1196389612897, 302.03041868441085, 261.6346141406121, 225.13679301420146, 215.96427569278717]
f3_db_osnr_list = [10*math.log10(x) for x in f3_abs_osnr_list]

x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
plt.plot(x, f1_db_osnr_list, 'r--', 
		 x, f2_db_osnr_list, 'bs', 
		 x, f3_db_osnr_list, 'g^')

red_patch = mpatches.Patch(color='red', label='rf_d1=-1.07815362800000, rf_d2=1.52067134300000')
blue_patch = mpatches.Patch(color='blue', label='rf=-0.450616586000000, rf_d2=0.293231395800000')
green_patch = mpatches.Patch(color='green', label='rf=1.31347481872000, rf_d2=-0.835348854560000')

plt.legend(handles=[red_patch, blue_patch, green_patch])

plt.title('OSNR performance through 10 hops (5 per domain) with different ripple functions (rf)')
plt.xlabel('Nodes')
plt.ylabel('dB')
plt.axis([1,10, 10, 42])
plt.grid(True)

plt.show()
