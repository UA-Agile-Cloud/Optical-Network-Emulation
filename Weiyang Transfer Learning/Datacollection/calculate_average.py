import time
import os
import sys

import serial
from nistica import Nistica

channel_num_list = ['45,46,47,48,49','46,47,48','46,47','47']
initial_num = 5
attenuation = '0dBattn'
samples = 100
case_num = 3

for channel_num in channel_num_list:
    dir_BERmeasurements = r'C:\Users\a-ytian\Desktop\code\0619\%schannel\channel%s_%s.txt' % (initial_num,channel_num,attenuation)
    with open(dir_BERmeasurements,'rb') as f:
        minBER = 1
        maxBER = 0
        count = 0
        total = 0
        for line in f:
            BER = float(line.split('=')[1])
            minBER = min(minBER,BER)
            maxBER = max(maxBER,BER)
            total += BER
            count += 1
            if count==samples:
                count = samples
                break
    print('Channel %s on' % channel_num)
    print('Average BER=%.5f' % (total/count))
    print('Maximum BER=%.5f' % maxBER)
    print('Minimum BER=%.5f' % minBER)
