#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np

data = open('ripple_wyang.txt')
data2 = open('ripple_function_dB.txt')
ripple_values = [float(x.strip()) for x in data.readlines()]
ripple_values2 = [float(x.strip()) for x in data2.readlines()]
alphabet = list(map(chr, range(97, 123)))
index_alphabet = 0
file_ext = ".txt"
# Store different y sets
# with the multiple shifts.
y_sets = []

# For plotting purposes
x_set = range(0,90)
plt.xlabel('wavelength')
plt.ylabel('ripple function')

index_alphabet = 0
file_name = "ripple_wyang_"

# Shift to the left
# Shift to the right
for x in range(0,12):
	new_y_set = []
	new_y_range = 90 - x
	for i in range(x, 90):
		new_y_set.append(ripple_values[i])
	for i in range(new_y_range, 90):
		new_y_set.append(0)

	# Generate file with new_y_set
	new_file_name = file_name + alphabet[index_alphabet] + file_ext
	new_file = open(new_file_name, 'a')
	for value in new_y_set:
		new_file.write(str(value) + '\n')
	index_alphabet = index_alphabet + 1

	plt.plot(x_set, new_y_set)
	y_sets.append(new_y_set)

index_alphabet = 0
file_name = "ripple_function_"
# Shift to the right
for x in range(0,12):
	new_y_set = []
	new_y_range = 90
	if x > 0:
		# Ignore first values
		# apply a 0 point.
		for i in range(0,x):
			new_y_set.append(0)
		new_y_range = 90 - x
	# Append values from original ripple function.
	for i in range(0, new_y_range):
		new_y_set.append(ripple_values2[i])

	# Generate file with new_y_set
	new_file_name = file_name + alphabet[index_alphabet] + file_ext
	new_file = open(new_file_name, 'a')
	for value in new_y_set:
		new_file.write(str(value) + '\n')
	index_alphabet = index_alphabet + 1

	plt.plot(x_set, new_y_set)
	y_sets.append(new_y_set)




# i = 0
# for _set in y_sets:
# 	print("Set shifted " + str(i) + " points to the right:")
# 	print _set
# 	i = i + 1

plt.grid(True)
plt.show()