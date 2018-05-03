import time
import os
import random
import sys
from datetime import datetime
import copy

import serial
from nistica import Nistica




def generateSubsets(ls):
    path = []
    res = []
    generateSubsetsDFS(ls,path,res)
    return res

def generateSubsetsDFS(ls,path,res):
    res.append(path)
    for (index,val) in enumerate(ls):
        generateSubsetsDFS(ls[index+1:],path+[val],res)


attenuations = [4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5]
timenow = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
dir_Data = r'C:\Users\a-ytian\Desktop\code\data\leaf\%s_leaf_4span' % timenow
if not os.path.exists(dir_Data):
    os.makedirs(dir_Data)
f_Data = open( r'C:\Users\a-ytian\Desktop\code\data\leaf\%s_leaf_4span\16qam_customerdata.txt' % (timenow),'w')
nistica = Nistica('com6')
for attenuation in attenuations:
    #(a) Initially_configure WSS
    channelstart = 0
    channelend = 95
    attenuations = [attenuation]*(channelend-channelstart+1)
    nistica.group_attenuation(channelstart,channelend,attenuations,port=1,table=1)
    dir_BER = r'C:\Users\a-ytian\Desktop\data_RT\BER.dat'
    assert os.path.exists(dir_BER) == True
    dir_Flag = r'C:\Users\a-ytian\Desktop\data_RT\StopFlag.dat'
    assert os.path.exists(dir_Flag) == True
    
    
    delay = 7 #Meausrement time for each BER measurement
    n_sample = 4 #Measured samples for each case, average out
    #(b) Configure WSS and BER measurement
    case = [42,43,44,45,46,47,48,49,50,51,52]
    #Turn on channels
    input_power = {}
    total = 0
    time1 = time.time()
    for channel in case: 
        nistica.chan_port_switching(channel,port=1,table=1)
        time.sleep(0.05)
    print('Turn on channel:%s' % case)
    time.sleep(2) #Wait OCM response
    flatten = False
    iteration = 1      
    for channel in case:
        power=nistica.per_channel_monitor(channel,table=1)
        if not power or power<-30: #Measure again if failed
            time.sleep(0.1)
            nistica.chan_port_switching(channel,port=1,table=1)
            time.sleep(2)
            power=nistica.per_channel_monitor(channel,table=1)
        input_power[channel]=power
        time.sleep(0.05)
    OSNR = copy.copy(input_power)
    noise_channel = 55
    noise=nistica.per_channel_monitor(noise_channel,table=1)
    for channel in OSNR:
        OSNR[channel]=OSNR[channel]-noise+6
        OSNR[channel]=round(OSNR[channel],1)
    print('Input Powers:%s' % str(input_power))
    print('Noise level:%sdBm' % noise)
    print('OSNR:%s' % str(OSNR))
    f_Data.write('input=%s' % str(input_power))
    f_Data.write('\n')
    f_Data.write('OSNR=%s' % str(OSNR))
    f_Data.write('\n')

   # time.sleep(delay) #wait one period before making measurements
    for _ in range(n_sample):
        with open(dir_Flag,'w') as f:
            f.write('1')
        time.sleep(0.1)  #Some interval between two operations...
        with open(dir_Flag,'w') as f:
            f.write('0')
        time.sleep(delay)
        with open(dir_BER,'r') as f:
            if _: #Skip first measurement, cache...
                BER = f.readline()
                if BER == '':
                    BER = -1 #Fail
                else:
                    BER = float(BER)
                total += BER
                print('BER=%s' % BER)
    BER_avg = total/(n_sample-1)
    print('Average BER=%s' % BER_avg)
    print('\n')
    f_Data.write('BER=%s\n' % BER_avg)
    
#Turn off channels
nistica.close()
f_Data.close()
