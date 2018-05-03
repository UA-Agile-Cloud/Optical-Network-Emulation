import time
import os
import random
import sys

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

#attenuations = [11,10.5,10,9.5]
#targets = [-17.8,-17.2,-16.7,-16.1]

#16QAM 4span leaf
##attenuations = [1,2,3,4,5,0.5]
##targets = [-18.1,-19.1,-20,-20.8,-22,-17.6]

#qpsk 3span dsf
attenuations = [2,2.5,3,3.5,4,5,6]
targets = [-23.2,-24,-24.3,-25.1,-25.4,-26.6,-27.8]



for (target,attenuation) in zip(targets,attenuations):
    #(a) Initially_configure WSS
    nistica = Nistica('com6')
    channelstart = 0
    channelend = 95
    attenuations = [attenuation]*(channelend-channelstart+1)
    nistica.group_attenuation(channelstart,channelend,attenuations,port=1,table=1)

    from datetime import datetime

    timenow = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    dir_BER = r'C:\Users\a-ytian\Desktop\data_RT\BER.dat'
    assert os.path.exists(dir_BER) == True
    dir_Flag = r'C:\Users\a-ytian\Desktop\data_RT\StopFlag.dat'
    assert os.path.exists(dir_Flag) == True
    dir_Data = r'C:\Users\a-ytian\Desktop\code\data\smf+dsf\%s' % timenow
    if not os.path.exists(dir_Data):
        os.makedirs(dir_Data)
    f_Data = open( r'C:\Users\a-ytian\Desktop\code\data\smf+dsf\%s\smf+dsf_data_attenuation_=%s.txt' % (timenow,attenuation),'w')
    delay = 7 #Meausrement time for each BER measurement
    n_sample = 2 #Measured samples for each case, average out
        
    channels = range(42,53)
    measured_channel = 47
    channels.remove(measured_channel) #Channel 47 we look at, always on
    all_cases = generateSubsets(channels)
   # random.seed(20)
    random.shuffle(all_cases)
    all_cases.insert(0,[])
    start_case=0 #Each case spends ~15 seconds, so 4000 samepls ~16 hours
    end_case=-1
    all_cases = all_cases[start_case:end_case]

    #(b) Configure WSS and BER measurement
    count = start_case+1
    for case in all_cases:
        #Turn on channels
        print('case %s' % count)
        count += 1
        input_power = {}
        total = 0
        time1 = time.time()
        for channel in case: 
            nistica.chan_port_switching(channel,port=1,table=1)
            time.sleep(0.05)
        print('Turn on channel:%s' % case)
        time.sleep(2) #Wait OCM response
        all_channels = case+[measured_channel]
        flatten = False
        iteration = 1
        print('Target Power is %sdBm' % target)
        while not flatten and iteration<=5:      
            for channel in all_channels:
                power=nistica.per_channel_monitor(channel,table=1)
                if not power or power<-30: #Measure again if failed
                    time.sleep(0.1)
                    nistica.chan_port_switching(channel,port=1,table=1)
                    time.sleep(2)
                    power=nistica.per_channel_monitor(channel,table=1)
                input_power[channel]=power
                time.sleep(0.05)
            minpow = min(input_power.values())
            maxpow = max(input_power.values())
            if abs(maxpow-target)<0.5 and abs(minpow-target)<0.5:
                flatten = True
                print('Power is already flattened within 0.5 dB')
            else:
                print('Need flatten power')
                for channel in all_channels:
                    curpow = input_power[channel]
                    curatten = nistica.check_chan_port_attenuation(channel,port=1,table=1)
                    time.sleep(0.05)
                    addatten = curpow-target
                    newatten = curatten+addatten
                    nistica.chan_port_attenuation(channel,port=1,attenuation=newatten,table=1)
                print('%s iteration done for power flatten' % iteration)
                time.sleep(2)
                iteration += 1
        print('Input Powers:%s' % str(input_power))                                    
        f_Data.write('input=%s' % str(input_power))
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
        f_Data.write('BER=%s\n' % BER_avg)
        
        #Turn off channels
        for channel in case:
            nistica.chan_port_switching(channel,port=0,table=1)
            time.sleep(0.05)
        print('Turned off channel:%s' % case)
        print('Spend %.2f seconds to train one case' % (time.time()-time1))
        print('\n')

    f_Data.close()
    nistica.close()
