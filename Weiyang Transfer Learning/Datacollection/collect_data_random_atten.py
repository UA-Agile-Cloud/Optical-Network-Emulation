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



#(a) Initially_configure WSS
nistica = Nistica('com6')


from datetime import datetime

timenow = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

dir_BER = r'C:\Users\a-ytian\Desktop\data_RT\BER.dat'
assert os.path.exists(dir_BER) == True
dir_Flag = r'C:\Users\a-ytian\Desktop\data_RT\StopFlag.dat'
assert os.path.exists(dir_Flag) == True
dir_Data = r'C:\Users\a-ytian\Desktop\code\data\smf+dsf\%s' % timenow
if not os.path.exists(dir_Data):
    os.makedirs(dir_Data)
f_Data = open( r'C:\Users\a-ytian\Desktop\code\data\smf+dsf\%s\randomattenuation.txt' % (timenow),'w')
delay = 7.5 #Meausrement time for each BER measurement
n_sample = 2 #Measured samples for each case, average out, must>=2
    
channels = range(42,53)
measured_channel = 47
channels.remove(measured_channel) #Channel 47 we look at, always on
all_cases = generateSubsets(channels)
all_cases.insert(0,[])
random.shuffle(all_cases)
start_case=0 #Each case spends ~15 seconds, so 4000 samepls ~16 hours
end_case=-1
all_cases = all_cases[start_case:end_case]


base_power = -7.3

attenuation_list = [13.5,13,12.5,12,11.5,11]
#(b) Configure WSS and BER measurement
cycles = 10
for _ in range(cycles):
    random.shuffle(all_cases)
    count = start_case+1
    for case in all_cases:
        #Turn on channels
        print('case %s' % count)
        count += 1
        input_power = {}
        target_power = {}
        attenuation_chls = {}
        total = 0
        time1 = time.time()
        for channel in case: 
            nistica.chan_port_switching(channel,port=1,table=1)
            time.sleep(0.05)
        print('Turn on channel:%s' % case)
        time.sleep(2) #Wait OCM response
        all_channels = case+[measured_channel]        
        for channel in all_channels:
            attenuation = random.choice(attenuation_list)
            attenuation_chls[channel]=round(attenuation,1)
            target_power[channel] = base_power-attenuation
            nistica.chan_port_attenuation(channel,port=1,attenuation=attenuation,table=1)
            
        tuning = True
        count_iteration = 0
        while tuning and count_iteration<5:
            tuning = False
            count_iteration += 1
            for channel in all_channels:
                power=nistica.per_channel_monitor(channel,table=1)
                if not power or power<-30: #Measure again if failed
                    time.sleep(0.1)
                    nistica.chan_port_switching(channel,port=1,table=1)
                    time.sleep(2)
                    power=nistica.per_channel_monitor(channel,table=1)
                input_power[channel] = power
                target = target_power[channel]               
                if abs(power-target)>0.5:
                    tuning = True                  
                time.sleep(0.05)

            if tuning:
                print('Tuning is required')
                for channel in all_channels:
                    curpower = input_power[channel]
                    curatten = attenuation_chls[channel]
                    target = target_power[channel]
                    addatten = curpower-target
                    newatten = curatten+addatten
                    attenuation_chls[channel]=round(newatten,1)
                    nistica.chan_port_attenuation(channel,port=1,attenuation=newatten,table=1)
                    time.sleep(0.02)
                print('tuning is attempted:%s iteration' % count_iteration)
                time.sleep(2)
                print('Input Powers after tuning:%s' % str(input_power))
            else:
                print('Power is already within the required level')
            
            
        print('Final Input Powers:%s' % str(input_power))
        f_Data.write('attenuation=%s' % str(attenuation_chls))
        f_Data.write('\n')
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
                        BER = -1
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
