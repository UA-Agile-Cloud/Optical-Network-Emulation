import time
import os
import random
import sys
from datetime import datetime

import serial
from nistica import Nistica





target = -17
flattened = False
iteration = 1
nistica = Nistica('com6')
all_channels = range(42,53)
ports = {42:2,43:1,44:2,45:1,46:1,47:1,48:2,49:2,50:2,51:2,52:2}
input_power={}
print('Target Power is %sdBm' % target)
while not flattened and iteration<=1:
    print ('Itertaion %s' % iteration)
    flattened = True
    for channel in all_channels:
        power=nistica.per_channel_monitor(channel,table=1)
        if not power or power<-30: #Measure again if failed
            time.sleep(0.1)
            nistica.chan_port_switching(channel,port=1,table=1)
            time.sleep(2)
            power=nistica.per_channel_monitor(channel,table=1)
        input_power[channel]=power
        time.sleep(0.05)

    for channel in all_channels:
        curpow = input_power[channel]             
        if abs(curpow-target)>0.2:
            flattened = False
            curatten = nistica.check_chan_port_attenuation(channel,port=ports[channel],table=0)
            time.sleep(0.05)
            addatten = curpow-target
            newatten = curatten+addatten
            if newatten<0:
                newatten = 0
            if newatten>15:
                newatten = 15
            nistica.chan_port_attenuation(channel,port=ports[channel],attenuation=newatten,table=0)
        time.sleep(0.05)

    iteration += 1
    if flattened:
        print ('Flattened')
        break

            
print('Input Powers:%s' % str(input_power))       
nistica.close()

