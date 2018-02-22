#!/usr/bin/env python
import math

# ORIGINAL
# virtual_links = [	(1, 2, 500),
# 			(1, 3, 500),			
# 			(2, 3, 500),
# 			(2, 4, 500),
# 			(3, 5, 500),
# 			(3, 7, 500),
# 			(4, 5, 500),
# 			(4, 10, 500),
# 			(5, 6, 500),
# 			(5, 8, 500),
# 			(6, 9, 500),
# 			(7, 9, 500),
# 			(7, 14, 500),
# 			(7, 15, 500),
# 			(8, 9, 500),
# 			(8, 11, 500),
# 			(8, 12, 500), 
# 			(9, 13, 500),
# 			(10, 11, 500),
# 			(10, 21, 500),
# 			(11, 20, 500),
# 			(11, 21, 500),
# 			(12, 13, 500),
# 			(12, 19, 500),
# 			(12, 20, 500),
# 			(13, 14, 500),
# 			(13, 18, 500),
# 			(14, 15, 500),
# 			(14, 17, 500),
# 			(15, 16, 500),
# 			(16, 17, 500),
# 			(17, 18, 500),
# 			(18, 19, 500),
# 			(19, 20, 500),
# 			(20, 21, 500)]

# +300km
virtual_links = [	(1, 2, 590),
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


def main():

	link_distance_mapping = {}
	dict_key = 0
	for link in virtual_links:
		src_node = link[0]
		dst_node = link[1]
		distance = link[2]

		try:
			EDFA_NO = math.ceil(distance/float(100)) + 1
			if EDFA_NO == 2:
				EDFA_NO = 1
			dict_key = dict_key + 1
			link_distance_mapping[dict_key] = (src_node, dst_node, distance, EDFA_NO)
			dict_key = dict_key + 1
			link_distance_mapping[dict_key] = (dst_node, src_node, distance, EDFA_NO)
		except:
			print('Err: unable to allocate link_distance_mapper!')

	return link_distance_mapping

if __name__=='__main__':
    sys.exit(main)
