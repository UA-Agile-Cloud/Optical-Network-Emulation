import time
import os
import random
import sys
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

#qpsk 4span leaf
##attenuations = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
##targets = [-14.4,-15.4,-16.6,-17.5,-18.4,-19.4,-20.2,-21.3,-22,-23.2,-23.6,-24.2,-24.6,-25]

#16qam 4span leaf
attenuations = [4,5,6,7,8,9,10,11,12,13,14]
targets = [-18,-19,-20,-21,-22,-23,-24,-25,-26,-27,-28]



#16QAM 4span leaf
##attenuations = [1,2,3,4,5]
##targets = [-15.2,-16.2,-17.2,-18.2,-19.2]
#attenuations = [7,7.5,8,8.5,6.5]
#targets = [-18,-18.5,-19,-19.5,-17.5]

#qpsk 3span dsf
#attenuations = [2,2.5,3,3.5,4,5,6]
#targets = [-23.2,-24,-24.3,-25.1,-25.4,-26.6,-27.8]

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
    dir_Data = r'C:\Users\a-ytian\Desktop\code\data\leaf\%s_leaf_2span' % timenow
    if not os.path.exists(dir_Data):
        os.makedirs(dir_Data)
    f_Data = open( r'C:\Users\a-ytian\Desktop\code\data\leaf\%s_leaf_2span\leaf_2span_data_attenuation_=%s.txt' % (timenow,attenuation),'w')
    delay = 7 #Meausrement time for each BER measurement
    n_sample = 2 #Measured samples for each case, average out
        
    channels = range(42,53)
    measured_channel = 47
    channels.remove(measured_channel) #Channel 47 we look at, always on
    all_cases = generateSubsets(channels)
    all_cases.insert(0,[])
  #  random.seed(20)
    random.shuffle(all_cases)
    start_case=0 #Each case spends ~15 seconds, so 4000 samepls ~16 hours
    end_case=256
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
                    if newatten<0:
                        newatten = 0
                    if newatten>15:
                        newatten = 15
                    nistica.chan_port_attenuation(channel,port=1,attenuation=newatten,table=1)
                print('%s iteration done for power flatten' % iteration)
                time.sleep(2)
                iteration += 1

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
        f_Data.write('noise=%s' % noise)
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
