#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 10:19:56 2017

@author: wmo
"""

import logging
import math
import time
import os
import sys
import copy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor, AdaBoostRegressor
from sklearn.linear_model import SGDRegressor,Ridge,RidgeCV,Lasso
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier,MLPRegressor
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVR,NuSVR,SVR
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression,Ridge,BayesianRidge,SGDRegressor
from sklearn.metrics import mean_squared_error,roc_auc_score
from sklearn.preprocessing import StandardScaler,MinMaxScaler,RobustScaler,scale
from scipy.special import  erfcinv
from sklearn.metrics import accuracy_score,roc_curve
from sklearn.externals import joblib
from xgboost import XGBRegressor
from sknn.mlp import Regressor,Layer
from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Input, Dropout
from keras.layers.normalization import BatchNormalization
from keras import optimizers
from keras.utils.np_utils import to_categorical
from keras import regularizers
from keras.models import load_model

from ParseData_BER import parse,split

#TUning tricks, (1) Activation function, Optimizer (2) Leaning Rate (3) Momemtum, hidden units, batch size, learning rate decay, layers.
def BER2Q(BER):
    if type(BER) == float:
        BER = np.asarray(BER)
    q = np.zeros(BER.shape)
    idx2Cal = BER < 0.5
    tmpQ =  20*np.log10((np.sqrt(2)*erfcinv(BER[idx2Cal]/.5)))
    q[idx2Cal] = tmpQ
    return q

def numericalAccuracy(y_hat,y,threshold=0.2):
    diff = abs(y_hat,y)
    locs = np.argwhere(diff>=threshold)
    accuracy = float(len(locs))/float(len(diff))
    return accuracy
#(1) Train and Predictions
consider_noise = False
db_to_dec = True
target = 'Q'
remove_lowQ = False
remove_badPoints = False
#train_ratios = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1
if 0:
    normalized = True


    files_withlabel = [
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=1.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=2.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=3.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=4.txt',  
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=5.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=6.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=7.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=8.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=9.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=10.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=11.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=12.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=13.txt',
            ]
#    files_withlabel = [                   
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=5.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=6.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=7.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=8.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=9.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=10.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=11.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=12.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=13.txt',
#            ]
#    files_withlabel = [                   
#                   r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=9.txt',
#                   r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=10.txt',
#                   r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=11.txt',
#                   ]
#    files_withlabel = [
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.5.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.5.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=4.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=5.txt',
#                      ]
#    files_withlabel = [
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=6.5.txt',  
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=7.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=7.5.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=8.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=8.5.txt',
#            ]

###        
 
#       
    tmp = []
    for filename in files_withlabel:
        X,OSNR,N,Y,labels = parse(filename,startchannel=42,endchannel=52,label=True)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)
        if N.any():
            data = np.concatenate([X,Y,N],axis=1)
        else:
            data = np.concatenate([X,Y],axis=1)
        tmp.append(data)
#            
#        for filename in files_nolabel:
#            X,Y,labels = parse(filename,startchannel=42,endchannel=52,label=None)
#            if db_to_dec:
#                X[X==0] = -float('inf')
#                X = 10**(X/10)
#            if target=='Q':
#                Y = BER2Q(Y)
#            data = np.concatenate([X,Y,labels],axis=1)s
#            tmp.append(data)
        
    data = np.concatenate(tmp)
    minQ = np.min(data[:,-2])
    maxQ = np.max(data[:,-2])
    if remove_badPoints: #Remove some super bad points, which might be due to experiment error
        badPoint_list = [1902,1905]
        data = np.delete(data,badPoint_list,axis=0)
#        if remove_lowQ:
#            data = data[data[:,11]>5]
#            data = data
    m_features = 11
#    X = data[:,0:m_features]
#    Y = data[:,m_features]
#    N = data[:,m_features+1]
    used_features = 11
    train,val,test = split(data,shuffle=11,train_ratio=train_ratio,validation_ratio=val_ratio,test_ratio=test_ratio) #Use 454 for testing
    X_train = train[:,(m_features-used_features)/2:(m_features+used_features)/2]
    Y_train = train[:,m_features]
    X_val = val[:,(m_features-used_features)/2:(m_features+used_features)/2]
    Y_val = val[:,m_features]
    X_test = test[:,(m_features-used_features)/2:(m_features+used_features)/2]
    Y_test = test[:,m_features]
    if N.any():
        N_train = train[:,m_features+1]
        N_val = val[:,m_features+1]
        N_test = test[:,m_features+1]
    
    if consider_noise:
        N_train = N_train.reshape([-1,1])
        N_val = N_val.reshape([-1,1])
        N_test = N_test.reshape([-1,1])
        X_train = np.concatenate([X_train,N_train],axis=1)
        X_val = np.concatenate([X_val,N_val],axis=1)
        X_test = np.concatenate([X_test,N_test],axis=1)
    
    Y_train = Y_train.reshape([-1,1])
    Y_val = Y_val.reshape([-1,1])
    Y_test = Y_test.reshape([-1,1])
    
    if normalized and 1:
        X_train_origin = copy.copy(X_train)
        X_val_origin = copy.copy(X_val)
        X_test_origin = copy.copy(X_test)
#            scaler = MinMaxScaler()
        scaler = StandardScaler()
#            scaler = RobustScaler()  
        scaler.fit(X_train)  
#        X_train = scale(X_train)  
#        X_val = scale(X_val)
#        X_test = scale(X_test)  
        X_train = scaler.transform(X_train)  
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)  


    #Simple llnear regression RMSE: 0.12, +/- 0.4dB, 98% accuracy
    #Simple llnear SVR RMSE: 0.12, +/- 0.4dB, 98% accuracy
    ###############################################################
#    svr = LinearRegression()
##    svr = SVR(kernel='rbf',C=10,gamma=1.0/m_features)
#    svr.fit(X_train,Y_train)
#    NN = svr
###########################################################################################
    NN = Sequential()
    units = 256
    l2 = 1e-3
    dr = 0.1 #Dropout rate
    if consider_noise:
        NN.add(Dense(units=units,input_dim=m_features+1,kernel_regularizer=regularizers.l2(l2)))
    else:
        NN.add(Dense(units=units,input_dim=11,kernel_regularizer=regularizers.l2(l2)))
    NN.add(Activation('relu'))
    NN.add(Dropout(dr))
#    NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
#    NN.add(Activation('relu'))
#    NN.add(Dropout(dr))
##    NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
##    NN.add(Activation('relu'))
##    NN.add(Dropout(dr))
##    NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
##    NN.add(Activation('relu'))
#    NN.add(Dropout(dr))
    NN.add(Dense(units=1))
    NN.add(Activation('linear'))
    sgd = optimizers.SGD(lr=0.01,momentum=0.9,decay=1e-5)
#    sgd = optimizers.Adam(lr=0.01,decay=1e-2)
    NN.compile(loss='mean_squared_error', optimizer=sgd)
    NN.fit(X_train,Y_train,epochs=300,batch_size=64,verbose=0)
##    #######################################################################
#     NN = Sequential()
#    NN.add(Dense(units=1,input_dim=11))
#    NN.add(Activation('linear'))
###########################################################################
#    NN = Sequential()
#    NN.add(Dense(units=1,input_dim=11,kernel_regularizer=regularizers.l2(0.01)))
#    NN.add(Activation('linear'))
#    NN.compile(loss='hinge',optimizer='sgd')
#    NN.fit(X_train,Y_train,epochs=2000,batch_size=Y_train.size,verbose=0)
#    c0 = copy.deepcopy(NN.layers[0].get_weights())
#    c1 = copy.deepcopy(NN.layers[3].get_weights())
#    c2 = copy.deepcopy(NN.layers[6].get_weights())
###########################################################################
    Y_pred_train = NN.predict(X_train)
    Y_pred_val = NN.predict(X_val)
    Y_pred_test = NN.predict(X_test)
    Y_pred_train = Y_pred_train.reshape([-1,1])
    Y_pred_val = Y_pred_val.reshape([-1,1])
    Y_pred_test = Y_pred_test.reshape([-1,1])
    print('NN-MLP RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
    print('NN-MLP RMSE of val:%.8f' % np.sqrt(mean_squared_error(Y_val,Y_pred_val)))
    print('NN-MLP RMSE of test:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
    
    
if 0: #Evaluate some special cases 
#    NN = load_model('4leaf_16qam_neuralnetwork.h5')
    files = [
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/qpsk_customerdata_11channel.txt',
            ]
#    files = [                   
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/16qam_customerdata_11channel.txt',
#            ]
    tmp = []
    for filename in files:
        X,OSNR,N,Y,labels = parse(filename,startchannel=42,endchannel=52,label=False)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)
        data = np.concatenate([X,Y,N],axis=1)
        tmp.append(data)
    data = np.concatenate(tmp)
    X = data[:,:used_features]
    Y = data[:,m_features]
    Y = Y.reshape([-1,1])
    N = data[:,m_features+1]
    if consider_noise:
        N = N.reshape([-1,1])
        X = np.concatenate([X,N],axis=1)
    X = scaler.transform(X) 
    Y_pred = NN.predict(X)
    Y_pred = Y_pred.reshape([-1,1])
    Y_diff = Y_pred - Y
    print('Maximum Prediction Q Error(customer data):%s dB,%s dB' % (np.max(Y_diff),np.min(Y_diff)))
    plt.figure()
    error = plt.scatter(Y,Y_pred, color='red',
            linewidth=0.01,s=20,label='test customer data True vs. Prediction')
    plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
    plt.grid()
    plt.legend(handles=[error])

if 1: #retrain
    load_trained_model = True
    add_new_layer = False
#    files = [
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/qpsk_customerdata_11channel.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/qpsk_customerdata_singlechannel.txt'
#            ]
    files = [                   
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/16qam_customerdata_11channel.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/16qam_customerdata_singlechannel.txt',
            ]
#    files = [                   
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/qpsk_customerdata_singlechannel.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/qpsk_customerdata_11channel.txt',
##            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=4.txt',
#            ]
#    files = [                   
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/16qam_customerdata_singlechannel.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/16qam_customerdata_11channel.txt',
#            ]
    tmp = []
    for filename in files:
        X,OSNR,N,Y,labels = parse(filename,startchannel=42,endchannel=52,label=False)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)
        data = np.concatenate([X,Y,labels],axis=1)
        tmp.append(data)
    data_train = np.concatenate(tmp)
    np.random.seed(311)
    np.random.shuffle(data_train)
    n_train = 111
    data_train = data_train[:n_train,:]
    X_train = data_train[:,:used_features]
    X_train = scaler.transform(X_train)
    Y_train = data_train[:,m_features]
#    args = np.argwhere(Y_train<6)[:,0]
#    Y_train = Y_train[args]
#    X_train = X_train[args]
#    Y_train[Y_train>5.0] += 0.4 #System fluctuation met during testing
#    Y_train[Y_train>5.5] += 0.2 #System fluctuation met during testing
    Y_train = Y_train.reshape([-1,1])
    if load_trained_model:
        if not add_new_layer:
            print ('Use a trained model from the qpsk system (fine tune)')
            NN = load_model('4leaf_qpsk_neuralnetwork.h5')
#            NN = load_model('4leaf_16qam_neuralnetwork.h5')
            for (i,layer) in enumerate(NN.layers):
                if i==0:
                    layer.trainable = False
            sgd = optimizers.SGD(lr=0.003,momentum=0.9,decay=1e-5)
            NN.compile(loss='mean_squared_error', optimizer=sgd)
            NN.fit(X_train,Y_train,epochs=1000,batch_size=Y_train.size,verbose=False)
        else:
            config = 'dense'
            if config == 'dense':
                print ('Use a trained model from the qpsk system (transfer)')
                NN = load_model('4leaf_qpsk_neuralnetwork.h5')
#                NN = load_model('4leaf_16qam_neuralnetwork.h5')
                NN.pop()
                NN.pop()
                NN.add(Dense(units=16,kernel_regularizer=regularizers.l2(l2)))
                NN.add(Activation('relu'))
                NN.add(Dropout(dr))
                NN.add(Dense(units=1))
                NN.add(Activation('linear'))
                sgd = optimizers.SGD(lr=0.003,momentum=0.9,decay=1e-5)
                NN.compile(loss='mean_squared_error', optimizer=sgd)
                NN.fit(X_train,Y_train,epochs=1000,batch_size=Y_train.size,verbose=0)
            elif config == 'SVR':
                pass
    else:
        print('Train a model from the scratch')
#        NN = SVR(kernel='rbf',C=10,gamma=1.0/m_features)
#        NN.fit(X_train,Y_train)
        NN = Sequential()
        units = 256
        l2 = 1e-3
        dr = 0.1 #Dropout rate
        NN.add(Dense(units=units,input_dim=m_features,kernel_regularizer=regularizers.l2(l2)))
        NN.add(Activation('relu'))
        NN.add(Dropout(dr))
        NN.add(Dense(units=1))
        NN.add(Activation('linear'))
        sgd = optimizers.SGD(lr=0.003,momentum=0.9,decay=1e-6)
        NN.compile(loss='mean_squared_error', optimizer=sgd)
        NN.fit(X_train,Y_train,epochs=1000,batch_size=Y_train.size,verbose=1)
#    files = [
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=1.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=2.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=3.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=4.txt',  
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=5.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=6.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=7.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=8.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=9.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=10.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=11.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=12.txt',
#             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/0824/leaf_4span_data_attenuation_=13.txt',
#            ]
    files = [                   
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=5.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=6.txt',
#            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=7.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=8.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=9.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=10.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=11.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=12.txt',
            r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/0824/leaf_4span_data_attenuation_=13.txt',
            ]
#    files = [
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.txt',
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.5.txt',
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.5.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=4.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=5.txt',
#              ]
#    files = [
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=4.txt',
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=5.txt',
##              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=6.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=7.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=8.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=9.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=10.txt',
#              r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/16qam/leaf_2span_data_attenuation_=11.txt',
#              ]
    tmp = []
    for filename in files:
        X,OSNR,N,Y,labels = parse(filename,startchannel=42,endchannel=52,label=False)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)
        data = np.concatenate([X,Y,labels],axis=1)
        tmp.append(data)
    data_test = np.concatenate(tmp)
    X_test = data_test[:,:used_features]
    X_test = scaler.transform(X_test)
    Y_test = data_test[:,m_features]
    Y_test = Y_test.reshape([-1,1])
    Y_pred_test = NN.predict(X_test)
    Y_pred_train = NN.predict(X_train)
    Y_diff_train = Y_pred_train - Y_train
    Y_pred_test = Y_pred_test.reshape([-1,1])
    Y_diff_test = Y_pred_test - Y_test
    print('RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
    print('RMSE of test:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
    print('Maximum Prediction Q Error:%s dB,%s dB' % (np.max(Y_diff_train),np.min(Y_diff_train)))
    print('Maximum Prediction Q Error:%s dB,%s dB' % (np.max(Y_diff_test),np.min(Y_diff_test)))
    minQ = np.min(Y_train)
    maxQ = np.max(Y_train)
    plt.figure()
    train_error=plt.scatter(Y_train,Y_pred_train, color='red',
         linewidth=0.01,s=20,label='train True vs. Prediction')
    plt.plot(np.linspace(minQ,maxQ,100),np.linspace(minQ,maxQ,100))
    plt.grid()
    plt.legend(handles=[train_error])
#    plt.xlim([0,0.006])
#    plt.ylim([-0.001,0.006])
    plt.xlabel('Actual Q')
    plt.ylabel('Predicted Q')
    minQ = np.min(Y_test)
    maxQ = np.max(Y_test)
    plt.figure()
    test_error=plt.scatter(Y_test,Y_pred_test, color='red',
         linewidth=0.01,s=20,label='test True vs. Prediction')
    plt.plot(np.linspace(minQ,maxQ,100),np.linspace(minQ,maxQ,100))
    plt.grid()
    plt.legend(handles=[test_error])
#    plt.xlim([0,0.006])
#    plt.ylim([-0.001,0.006])
    plt.xlabel('Actual Q')
    plt.ylabel('Predicted Q') 


    
#    n_train = 10
#    np.random.seed(11)
#    np.random.shuffle(data)
#    data_train = data[:n_train,]
#    data_test = data[2756:,]
#    X_train = data_train[:,:used_features]
#    Y_train = data_train[:,m_features]
#    X_test = data_test[:,:used_features]
#    Y_test = data_test[:,m_features]
#    X_train = scaler.transform(X_train)
#    X_test = scaler.transform(X_test)
#    Y_train = Y_train.reshape([-1,1])
#    Y_test = Y_test.reshape([-1,1])
#    for (i,layer) in enumerate(NN.layers):
#        if  i==0:
#            layer.trainable = False
#    sgd = optimizers.SGD(lr=0.005,momentum=0.9,decay=1e-6)
#    NN.compile(loss='mean_squared_error', optimizer=sgd)
#    NN.fit(X_train,Y_train,epochs=200,batch_size=Y_train.size,verbose=0)
#    Y_pred_test = NN.predict(X_test)
#    Y_pred_test = Y_pred_test.reshape([-1,1])
#    Y_diff_test = Y_pred_test - Y_test
#    print('RMSE of test:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#    print('Maximum Prediction Q Error:%s dB,%s dB' % (np.max(Y_diff_test),np.min(Y_diff_test)))
#    plt.figure()
#    test_error=plt.scatter(Y_test,Y_pred_test, color='red',
#         linewidth=0.01,s=4,label='test True vs. Prediction')
#    plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
#    plt.grid()
#    plt.legend(handles=[test_error])
##    plt.xlim([0,0.006])
##    plt.ylim([-0.001,0.006])
#    plt.xlabel('Actual Q')
#    plt.ylabel('Predicted Q') 
#    d0 = NN.layers[0].get_weights()
#    d1 = NN.layers[3].get_weights()
#    d2 = NN.layers[6].get_weights()
    
    
    
    
    
#if 1:
##    plt.figure()
###        pred_train = plt.scatter(range(len(Y_pred_train)),Y_pred_train, color='blue',
###             linewidth=0.01,label='Train Prediction')
##    actual_train = plt.scatter(range(len(Y_train)),Y_train, color='red',
##         linewidth=0.01,label='Train Actual')
##    plt.legend(handles=[actual_train])
##    plt.grid()
###    plt.ylim([-0.002,0.006])
##    plt.ylabel('Q')
##    plt.xlabel('case number')
##    plt.show()
#    
#    plt.figure()
#    train_error=plt.scatter(Y_train,Y_pred_train, color='red',
#         linewidth=0.01,s=4,label='train True vs. Prediction')
#    plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
#    plt.grid()
#    plt.legend(handles=[train_error])
##    plt.xlim([0,0.006])
##    plt.ylim([-0.001,0.006])
#    plt.xlabel('Actual Q')
#    plt.ylabel('Predicted Q') 
###(3) Plot prediction y and yhat
#if 1:
##    plt.figure()
###        pred_test = plt.scatter(range(len(Y_pred_test)),Y_pred_test, color='blue',
###             linewidth=0.002,label='Test Prediction')
##    actual_test = plt.scatter(range(len(Y_test)),Y_test, color='red',
##         linewidth=0.002,label='Test Actual')
##    plt.legend(handles=[actual_test])
##    plt.grid()
###    plt.ylim([-0.002,0.006])
##    plt.ylabel('Q')
##    plt.xlabel('case number')
#    
##    plt.xticks(())
##    plt.yticks(())
#    plt.show()
#    
#    plt.figure()
#    test_error=plt.scatter(Y_test,Y_pred_test, color='red',
#         linewidth=0.002,label='Test True vs. Prediction')
#    plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
#    plt.grid()
#    plt.legend(handles=[test_error])
##    plt.xlim([0,0.006])
##    plt.ylim([-0.001,0.006])
#    plt.ylabel('Actual Q')
#    plt.xlabel('Predicted Q')
#    
#if 1:
#    Y_diff_train = Y_pred_train - Y_train
#    Y_diff_val = Y_pred_val - Y_val
#    Y_diff_test = Y_pred_test - Y_test
#    print('Maximum Prediction Q Error (train):%s dB,%s dB' % (np.max(Y_diff_train),np.min(Y_diff_train)))
#    print('Maximum Prediction Q Error (val):%s dB,%s dB' % (np.max(Y_diff_val),np.min(Y_diff_val)))
#    print('Maximum Prediction Q Error (test):%s dB,%s dB' % (np.max(Y_diff_test),np.min(Y_diff_test)))
##    locs = np.argwhere(abs(Y_diff_test)>0.3)
##    label_has_big_error = label_test[locs]
#    
##if 1:
##    plt.figure()
##    Y_error = Y_pred_test-Y_test
##    plt.imshow(np.atleast_2d(Y_error),extent=(min(Y_error),max(Y_error),min(Y_error),max(Y_error)),cmap=cm.hot)
##    plt.colorbar()
##    plt.show()
###    
#if 1:
#    ###(4) Show classification accuracy
#    Q_threshold = 9.8 #Correspond to BER=1e-3
#    Y_pred_train_cls = copy.copy(Y_pred_train)
#    Y_train_cls = copy.copy(Y_train)
#    Y_pred_train_cls[Y_pred_train_cls<=Q_threshold]=0
#    Y_pred_train_cls[Y_pred_train_cls>Q_threshold]=1
#    Y_train_cls[Y_train_cls<=Q_threshold]=0
#    Y_train_cls[Y_train_cls>Q_threshold]=1
#    accuracy = accuracy_score(Y_pred_train_cls,Y_train_cls)
#    print('Accuracy of classification is %s (train)' % accuracy)
#    Y_pred_val_cls = copy.copy(Y_pred_val)
#    Y_val_cls = copy.copy(Y_val)
#    Y_pred_val_cls[Y_pred_val_cls<=Q_threshold]=0
#    Y_pred_val_cls[Y_pred_val_cls>Q_threshold]=1
#    Y_val_cls[Y_val_cls<=Q_threshold]=0
#    Y_val_cls[Y_val_cls>Q_threshold]=1
#    accuracy = accuracy_score(Y_pred_train_cls,Y_train_cls)
#    print('Accuracy of classification is %s (train)' % accuracy)
#    Y_pred_test_cls = copy.copy(Y_pred_test)
#    Y_test_cls = copy.copy(Y_test)
#    Y_pred_test_cls[Y_pred_test_cls<=Q_threshold]=0
#    Y_pred_test_cls[Y_pred_test_cls>Q_threshold]=1
#    Y_test_cls[Y_test_cls<=Q_threshold]=0
#    Y_test_cls[Y_test_cls>Q_threshold]=1
#    accuracy = accuracy_score(Y_pred_test_cls,Y_test_cls)
#    print('Accuracy of classification is %s (test)' % accuracy)
#    print('\n')
#
#if 0:
#    ###(5) ROC curve
#    FPR,TPR,threshold=roc_curve(Y_test_cls,Y_pred_test)
#    auc=roc_auc_score(Y_test_cls,Y_pred_test)
#    print('Area under ROC curve:%s' % auc)
#
#if 0:
#    threshold = 0.2
#    accuracy = numericalAccuracy(Y_pred_test,Y_test,threshold=threshold)
#    print('Accuracy with 0.2 dB threshold is %s' % accuracy) 