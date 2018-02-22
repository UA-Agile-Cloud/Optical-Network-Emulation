#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.patches as mpatches

osnr_log_file = 'osnr_log.log'
file = open(osnr_log_file, 'r')
for line in file.readlines():
	osnr_list = line
	list_len = len(osnr_list)
	x = []
	x = [x.append(i+1) for i in range(0,list_len+1)]
	plt.plot(x, osnr_list)

plt.legend(handles=[red_patch, blue_patch, green_patch])

plt.title('OSNR plotting test')
plt.xlabel('Nodes')
plt.ylabel('dB')
plt.axis([1,10, 10, 42])
plt.grid(True)
