#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 09:11:08 2017

@author: wmo
"""

import ast
import math
import sys
import logging

import numpy as np
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)

def parse(filename,startchannel=40,endchannel=54,label=True):
    P = []
    OSNR = []
    N = []
    Q = []
    with open(filename,'r') as f:
        if label:
            label = filename.split('=')[1]
            label = label.rsplit('.',1)[0]
        else:
            label = None
        for line in f:
            if line.startswith('input'):
                power_dict = ast.literal_eval(line.split('=',1)[1])
                tmp_P = [0]*(endchannel-startchannel+1)
                for (channel,power) in power_dict.items():
                    tmp_P[channel-startchannel] = power
                P.append(tmp_P)
            if line.startswith('OSNR'):
                power_dict = ast.literal_eval(line.split('=',1)[1])
                tmp_OSNR = [0]*(endchannel-startchannel+1)
                for (channel,osnr) in power_dict.items():
                    tmp_OSNR[channel-startchannel] = osnr
                OSNR.append(tmp_OSNR)
                for i in range(len(tmp_OSNR)):
                    if tmp_OSNR[i]:
                        noise = tmp_P[i] - tmp_OSNR[i] + 6
                        N.append(noise)
                        break
            if line.startswith('BER'):
                BER = float(line.split('=',1)[1])
                Q.append(BER)
                if BER<0 or BER>0.05: #High BER which cannot measure by transponder,ignore
                    del P[-1]
                    if OSNR:
                        del OSNR[-1]
                    if N:
                        del N[-1]
                    del Q[-1]
            
                
    P = np.asarray(P)
    OSNR = np.asarray(OSNR)
    N = np.asarray(N)
    N = N.reshape([-1,1])
    Q = np.asarray(Q)
    Q = Q.reshape([-1,1])
    labels = np.zeros(Q.shape)
    labels[:] = label
    return P,OSNR,N,Q,labels

def split(data,shuffle=0,train_ratio=0.2,validation_ratio=0,test_ratio=0.8):
    if shuffle:
        if shuffle == True:
            np.random.shuffle(data)
        else:
            np.random.seed(shuffle)
            np.random.shuffle(data)
    length = len(data)
    logging.debug('train_data,test_data,validation_data:%s,%s,%s' % (train_ratio,test_ratio,validation_ratio))
    logging.debug('data size=%s' % str(np.shape(data)))
    if validation_ratio==0:
        train_data = data[0:int(length*train_ratio)]
        test_data = data[int(length*(1-test_ratio)):]
        return (train_data,test_data)
    else:
        train_data = data[0:int(length*train_ratio)]
        validation_data = data[int(length*(1-validation_ratio-test_ratio)):int(length*(1-test_ratio))]
        test_data = data[int(length*(1-test_ratio)):]
        return (train_data,validation_data,test_data)
                
if __name__== '__main__':
    testfile = r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=11.5.txt'
    X,Y,labels = parse(testfile)
    data = np.concatenate([X,Y],axis=1)
           
                    