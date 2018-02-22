#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches

# 7 ripples
dp_16_21 = [	49.929512591716005, 49.809645562868894, 49.613237786720966, 49.41752499525733, 49.14466997231976,
				48.81627163606805, 48.60238412803587, 48.49856309248948, 48.336951073999806, 48.08921332868881]
dp_16_21_dB = [10*math.log10(x) for x in dp_16_21]

cp_16_21 = [	49.36480504087084, 49.39033635954396, 49.41586767821684, 49.44139899688954, 49.466930315562045,
				49.49246163423431, 49.51799295290638, 49.54352427157828, 49.5690555902499, 49.59458690892137]
cp_16_21_dB = [10*math.log10(x) for x in cp_16_21]

# 7 ripples
dp_1_21 = [	33.26886492584013, 33.12811115166513, 32.90027553160612, 32.67109895079045, 32.35192274890785,
			31.96378253540517, 31.697920916927323, 31.54613109608946, 31.310262583148447, 30.959235157795153]
dp_1_21_dB = [10*math.log10(x) for x in dp_1_21]

cp_1_21 = [	32.9098701130739, 32.92689099227813, 32.94391187148224, 32.96093275068626, 32.9779536298902,
			32.99497450909404, 33.01199538829777, 33.02901626750145, 33.04603714670499, 33.063058025908454]
cp_1_21_dB = [10*math.log10(x) for x in cp_1_21]

# 7 ripples
dp_1_17 = [	43.38852772997198, 42.81064818647259, 42.13821274031957, 41.413230104743846, 40.42067100871072,
			39.243945801899756, 38.328700392534856, 37.550386496282314, 36.464959355132095, 35.16634178399568]
dp_1_17_dB = [10*math.log10(x) for x in dp_1_17]

cp_1_17 = [	41.13733758770071, 41.158613686650476, 41.179889785600075, 41.20116588454954, 41.22244198349889,
			41.24371808244806, 41.26499418139709, 41.28627028034602, 41.307546379294735, 41.32882247824336]
cp_1_17_dB = [10*math.log10(x) for x in cp_1_17]

cp_16_21_m01_dB = [(10*math.log10(x))-0.1 for x in cp_16_21]
cp_16_21_m02_dB = [(10*math.log10(x))-0.2 for x in cp_16_21]
cp_16_21_m03_dB = [(10*math.log10(x))-0.3 for x in cp_16_21]
cp_16_21_m04_dB = [(10*math.log10(x))-0.4 for x in cp_16_21]
cp_16_21_m05_dB = [(10*math.log10(x))-0.5 for x in cp_16_21]

cp_1_21_m01_dB = [(10*math.log10(x))-0.1 for x in cp_1_21]
cp_1_21_m02_dB = [(10*math.log10(x))-0.2 for x in cp_1_21]
cp_1_21_m03_dB = [(10*math.log10(x))-0.3 for x in cp_1_21]

cp_1_17_m01_dB = [(10*math.log10(x))-0.1 for x in cp_1_17]
cp_1_17_m02_dB = [(10*math.log10(x))-0.2 for x in cp_1_17]
cp_1_17_m03_dB = [(10*math.log10(x))-0.3 for x in cp_1_17]


wavelengths = [1546.8, 1547.6, 1548.4, 1549.2, 1550, 1550.8, 1551.6, 1552.4, 1553.2, 1554]

plt.plot(wavelengths, cp_16_21_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_16_21_m01_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_16_21_m02_dB, 'r--', marker='o')

plt.plot(wavelengths, cp_1_21_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_1_21_m01_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_1_21_m02_dB, 'r--', marker='o')

plt.plot(wavelengths, cp_1_17_m01_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_1_17_m02_dB, 'r--', marker='o')
plt.plot(wavelengths, cp_1_17_m03_dB, 'r--', marker='o')

plt.plot(wavelengths, dp_16_21_dB, 'b', marker='^')
plt.plot(wavelengths, dp_1_21_dB, 'g', marker='^')
plt.plot(wavelengths, dp_1_17_dB, 'm', marker='^')
# plt.plot(wavelengths, db_path_4_17_B, 'tab:gray', marker='^')
# plt.plot(wavelengths, db_path_4_17_FLAT, 'tab:gray', marker='+')
# plt.plot(wavelengths, db_path_4_18_A, 'b--', marker='o')
# plt.plot(wavelengths, db_path_16_21_VARIABLE, 'r--', marker='v')

plt.xticks(np.arange(1546.8,1554,0.8))
plt.yticks(np.arange(14,18,0.2))

#plt.title('OSNR performance in bidirectional links')
plt.xlabel('Wavelength (nm)')
plt.ylabel('OSNR (dB)')
plt.grid(True)


# blue_patch = mpatches.Patch(color='blue', label='Lightpath A')
# black_patch = mpatches.Patch(color='black', label='Lightpath B')
# green_patch = mpatches.Patch(color='green', label='Lightpath C')
# ripple_A_patch = mpatches.Patch(color='blue', label='--o-- Ripple 1')
# ripple_B_patch = mpatches.Patch(color='black', label='--^-- Ripple 2')
# ripple_C_patch = mpatches.Patch(color='green', label='--+-- Ripple Flat')
# ripple_D_patch = mpatches.Patch(color='red', label='--v-- Ripple Variable')


# #blue_patch, black_patch, green_patch, 
# plt.legend(handles=[ripple_A_patch, ripple_B_patch, ripple_C_patch, ripple_D_patch])

plt.show()