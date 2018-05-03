import time
import os
import sys

import serial
from nistica import Nistica



dir_BER = r'C:\Users\a-ytian\Desktop\data_RT\BER.dat'

assert os.path.exists(dir_BER) == True

dir_Flag = r'C:\Users\a-ytian\Desktop\data_RT\StopFlag.dat'

assert os.path.exists(dir_Flag) == True

n_samples=100
while 1:
    with open(dir_Flag,'wb') as f:
        f.write('1')
    time.sleep(0.1)  #Some interval between two operations...
    with open(dir_Flag,'wb') as f:
        f.write('0')
        
    delay = 7 #Measurment delay after flag changed

    time.sleep(delay)
    with open(dir_BER,'rb') as f:
        print('BER=%s' % f.readline())
