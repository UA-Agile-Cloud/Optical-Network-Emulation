#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches

def aggregated_distances(var):
	aggr_distances = []
	span = 50
	for x in var:
		aggr_distances.append(x+span)
		span = span + 50
	return aggr_distances

# Considering noise figure of EDFA = 6 - RIPPLE = 0.99109244092

# abs_path_4_18_1500 = [333.56688907674965, 166.78344894702755, 111.18896694438565, 83.391725575677, 66.71338063688772]
# db_path_4_18_1500 = [10*math.log10(x) for x in abs_path_4_18_1500]

# abs_path_4_18_2000 = [293.3457495325755, 146.67287817585787, 97.78191954158751, 73.33643994032153, 58.66915208864005]
# db_path_4_18_2000 = [10*math.log10(x) for x in abs_path_4_18_2000]

# abs_path_4_18_2500 = [268.260611391059, 134.1303085469012, 89.42020633157234, 67.06515498629362, 53.65212410308978]
# db_path_4_18_2500 = [10*math.log10(x) for x in abs_path_4_18_2500]

# abs_path_4_18_3000 = [250.28631064881606, 125.14315780647912, 83.42877242255749, 62.57157952375739, 50.05726371828877]
# db_path_4_18_3000 = [10*math.log10(x) for x in abs_path_4_18_3000]

# abs_path_4_18_3500 = [237.71579894783898, 118.85790171292989, 79.23860163951113, 59.428951416217565, 47.543161222534486]
# db_path_4_18_3500 = [10*math.log10(x) for x in abs_path_4_18_3500]

# abs_path_4_18_4000 = [228.63225250402687, 114.31612832317994, 76.21075267571254, 57.15806467938163, 45.72645182635196]
# db_path_4_18_4000 = [10*math.log10(x) for x in abs_path_4_18_4000]

# Considering noise figure of EDFA = 6 - RIPPLE = 0.13102673816

# abs_path_4_18_1500 = [255.36724140110618, 127.68362328442151, 85.12241609714069, 63.84181228817787, 51.07344993389704]
# db_path_4_18_1500 = [10*math.log10(x) for x in abs_path_4_18_1500]

# abs_path_4_18_2000 = [207.65330731481117, 103.82665536591637, 69.2177706236133, 51.91332811008589, 41.530662556409155]
# db_path_4_18_2000 = [10*math.log10(x) for x in abs_path_4_18_2000]

# abs_path_4_18_2500 = [175.41804852418943, 87.70902548133296, 58.472683925163835, 43.85451304547606, 35.08361048515039]
# db_path_4_18_2500 = [10*math.log10(x) for x in abs_path_4_18_2500]

# abs_path_4_18_3000 = [152.48877427792326, 76.24438806029283, 50.82959224493547, 38.12219426047921, 30.497755445236614]
# db_path_4_18_3000 = [10*math.log10(x) for x in abs_path_4_18_3000]

# abs_path_4_18_3500 = [135.555640991662, 67.77782122390447, 45.18521431106377, 33.88891079397063, 27.111128664299454]
# db_path_4_18_3500 = [10*math.log10(x) for x in abs_path_4_18_3500]

# abs_path_4_18_4000 = [122.53376568860082, 61.26688343921086, 40.84458909167623, 30.633441868333044, 24.506753518462855]
# db_path_4_18_4000 = [10*math.log10(x) for x in abs_path_4_18_4000]

# Considering noise figure of EDFA = 6 - RIPPLE = -0.5082203864

abs_path_4_18_1500 = [203.36166424281888, 101.6808337600292, 67.78722287082388, 50.84041728966957, 40.67233389728045]
db_path_4_18_1500 = [10*math.log10(x) for x in abs_path_4_18_1500]

abs_path_4_18_2000 = [152.5813105022019, 76.29065617355064, 50.8604376540226, 38.14532831738777, 30.51626269080821]
db_path_4_18_2000 = [10*math.log10(x) for x in abs_path_4_18_2000]

abs_path_4_18_2500 = [119.21075963600408, 59.60538038108309, 39.73692037918455, 29.802690331311833, 23.842152287572713]
db_path_4_18_2500 = [10*math.log10(x) for x in abs_path_4_18_2500]

abs_path_4_18_3000 = [95.71804013147978, 47.85902042875743, 31.90601369984219, 23.9295103051331, 19.14360825862718]
db_path_4_18_3000 = [10*math.log10(x) for x in abs_path_4_18_3000]

abs_path_4_18_3500 = [78.26734624452187, 39.13367336497851, 26.089115630589596, 19.566836743168658, 15.653469404243625]
db_path_4_18_3500 = [10*math.log10(x) for x in abs_path_4_18_3500]

abs_path_4_18_4000 = [65.02784090073546, 32.5139206179155, 21.67594711584318, 16.2569603508447, 13.00556828737768]
db_path_4_18_4000 = [10*math.log10(x) for x in abs_path_4_18_4000]

TH_QPSK = [10] * 80
TH_8QAM = [14] * 80
TH_16QAM = [17] * 80


# DISTANCES
d_path_4_18_1500 = [300, 600, 900, 1200, 1500]
d_path_4_18_2000 = [400, 800, 1200, 1600, 2000]
d_path_4_18_2500 = [500, 1000, 1500, 2000, 2500]
d_path_4_18_3000 = [600, 1200, 1800, 2400, 3000]
d_path_4_18_3500 = [700, 1400, 2100, 2800, 3500]
d_path_4_18_4000 = [800, 1600, 2400, 3200, 4000]

var = [100] * 80
d_th = aggregated_distances(var)

plt.annotate(
	"QPSK threshold",
	xy=(3000,10), xytext=(3000,11),
	bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3),
	arrowprops=dict(arrowstyle = '-', connectionstyle='arc3,rad=0'))
plt.annotate(
	"8QAM threshold",
	xy=(3000,14), xytext=(3000,15),
	bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3),
	arrowprops=dict(arrowstyle = '-', connectionstyle='arc3,rad=0'))
plt.annotate(
	"16QAM threshold",
	xy=(3000,17), xytext=(3000,18),
	bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3),
	arrowprops=dict(arrowstyle = '-', connectionstyle='arc3,rad=0'))

plt.plot(d_path_4_18_1500, db_path_4_18_1500, 'b', marker='o')
plt.plot(d_path_4_18_2000, db_path_4_18_2000, 'k', marker='o')
plt.plot(d_path_4_18_2500, db_path_4_18_2500, 'g', marker='o')
plt.plot(d_path_4_18_3000, db_path_4_18_3000, 'y', marker='o')
plt.plot(d_path_4_18_3500, db_path_4_18_3500, 'm', marker='o')
plt.plot(d_path_4_18_4000, db_path_4_18_4000, 'c', marker='o')

plt.plot(d_th, TH_QPSK, 'r*')
plt.plot(d_th, TH_8QAM, 'r--')
plt.plot(d_th, TH_16QAM, 'r')

plt.xticks(np.arange(200,4100,200))
plt.yticks(np.arange(9,26,0.5))

#plt.title('OSNR performance in bidirectional links')
plt.xlabel('Distance (km)')
plt.ylabel('OSNR (dB)')
plt.grid(True)

blue_patch = mpatches.Patch(color='blue', label='1500 km - 20 EDFA')
black_patch = mpatches.Patch(color='black', label='2000 km - 25 EDFA')
green_patch = mpatches.Patch(color='green', label='2500 km - 30 EDFA')
yellow_patch = mpatches.Patch(color='yellow', label='3000 km - 35 EDFA')
magenta_patch = mpatches.Patch(color='purple', label='3500 km - 40 EDFA')
cyan_patch = mpatches.Patch(color='cyan', label='4000 km - 45 EDFA')
red_patch = mpatches.Patch(color='red', label='** QPSK, -- 8QAM, __ 16QAM')


plt.legend(handles=[blue_patch, black_patch, green_patch, yellow_patch, magenta_patch, cyan_patch])

plt.show()