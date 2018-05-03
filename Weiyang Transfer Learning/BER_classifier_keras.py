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
from sklearn.svm import LinearSVR,NuSVR,SVR,SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression,Ridge,BayesianRidge,SGDRegressor
from sklearn.metrics import mean_squared_error,roc_auc_score
from sklearn.preprocessing import StandardScaler,MinMaxScaler,RobustScaler
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
downthresholdQ = 9.8
upthresholdQ = 9.8
db_to_dec = True
target = 'Q'
remove_lowQ = False
remove_badPoints = False
#train_ratios = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1
if True:
    normalized = True


    files_withlabel = [
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/leaf_4span_data_attenuation_=1.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/leaf_4span_data_attenuation_=2.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/leaf_4span_data_attenuation_=3.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/qpsk/leaf_4span_data_attenuation_=4.txt',

       
            ]
##        
 
#       
    tmp = []
    for filename in files_withlabel:
        X,Y,labels = parse(filename,startchannel=42,endchannel=52,label=True)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)               
        data = np.concatenate([X,Y,labels],axis=1)
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
#        if remove_badPoints: #Remove some super bad points, which might be due to experiment error
#            badPoint_list = [5370,5378]
#            data = np.delete(data,badPoint_list,axis=0)
#        if remove_lowQ:
#            data = data[data[:,11]>5]
#            data = data
    m_features = data.shape[1]-2
    X = data[:,0:m_features]
    Y = data[:,m_features]
    if downthresholdQ==upthresholdQ:
        Y[Y<=downthresholdQ] = 0
        Y[Y>=upthresholdQ] = 1
    else:        
        Y[Y<=downthresholdQ] = 0
        Y[Y>=upthresholdQ] = 1
        Y[np.logical_and(Y>downthresholdQ,Y<upthresholdQ)]=2
    train,val,test = split(data,shuffle=333,train_ratio=train_ratio,validation_ratio=val_ratio,test_ratio=test_ratio) #Use 454 for testing
    X_train = train[:,0:m_features]
    Y_train = train[:,m_features]
    label_train = train[:,m_features+1]
    X_val = val[:,0:m_features]
    Y_val = val[:,m_features]
    label_val = val[:,m_features+1]
    X_test = test[:,0:m_features]
    Y_test = test[:,m_features]
    label_test = test[:,m_features+1]
    
    Y_train = Y_train.reshape([-1,1])
    Y_val = Y_val.reshape([-1,1])
    Y_test = Y_test.reshape([-1,1])
    
#    Y_train = to_categorical(Y_train)
#    Y_val = to_categorical(Y_val)
#    Y_test = to_categorical(Y_test)
    
    if normalized and 1:
        X_train_origin = copy.copy(X_train)
        X_val_origin = copy.copy(X_val)
        X_test_origin = copy.copy(X_test)
#            scaler = MinMaxScaler()
        scaler = StandardScaler()
#            scaler = RobustScaler()  
        scaler.fit(X_train)  
        X_train = scaler.transform(X_train)  
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)  
    
    
#    svc = SVC(kernel='rbf',C=10,gamma=1.0/m_features)
#    svc.fit(X_train,Y_train)
#    NN = svc
#    Y_pred_train = NN.predict(X_train)
#    Y_pred_val = NN.predict(X_val)
#    Y_pred_test = NN.predict(X_test)
#    Y_pred_train = Y_pred_train.reshape([-1,1])
#    Y_pred_val = Y_pred_val.reshape([-1,1])
#    Y_pred_test = Y_pred_test.reshape([-1,1])
#    print ('Train accuracy:%.3f' % (1-np.count_nonzero(Y_train-Y_pred_train)/float(Y_train.size)))
#    print ('Validation accuracy:%.3f' % (1-np.count_nonzero(Y_val-Y_pred_val)/float(Y_val.size)))
#    print ('Test accuracy:%.3f' % (1-np.count_nonzero(Y_test-Y_pred_test)/float(Y_test.size)))
        

    Y_train = to_categorical(Y_train)
    Y_val = to_categorical(Y_val)
    Y_test = to_categorical(Y_test)
    #Compare to logistic regression
#    LR = Sequential()
#    if downthresholdQ==upthresholdQ:
#        output_dim = 2
#        LR.add(Dense(units=output_dim,input_dim=11))
#        LR.add(Activation('sigmoid'))
#        loss = 'binary_crossentropy'
#    else:
#        output_dim = 3
#        LR.add(Dense(units=output_dim,input_dim=11))   
#        LR.add(Activation('softmax'))
#        loss = 'categorical_entropy'
#    sgd = optimizers.SGD(lr=0.01,momentum=0.9)
#    LR.compile(loss=loss, optimizer=sgd,metrics=['accuracy'])
#    LR.fit(X_train,Y_train,epochs=200,batch_size=64,verbose=0)
#    eval_train = LR.evaluate(X_train,Y_train)
#    eval_val = LR.evaluate(X_val,Y_val)
#    eval_test = LR.evaluate(X_test,Y_test)
#    print ('Train accuracy:%.3f' % (eval_train[1]*100))
#    print ('Validation accuracy:%.3f' % (eval_val[1]*100))
#    print ('Test accuracy:%.3f' % (eval_test[1]*100))
    
    #Simple logistic regression accuracy downth=9.3,upth=10.3, 94.5%
    #Simple logsitic regression accuracy downth=upth=9.8, 96%
    

#    NN = Sequential()
#    units = 128
#    l2 = 1e-2
#    dr = 0.2 #Dropout rate
#    if downthresholdQ==upthresholdQ:
#        output_dim = 2
#        NN.add(Dense(units=output_dim))
#        NN.add(Activation('sigmoid'))
#        loss = 'binary_crossentropy'
#    else:
#        output_dim = 3
#        NN.add(Dense(units=output_dim))   
#        NN.add(Activation('softmax'))
#        loss = 'categorical_entropy'
#    sgd = optimizers.SGD(lr=0.005,momentum=0.9,decay=1e-6)
#    NN.compile(loss=loss, optimizer=sgd,metrics=['accuracy'])
#    NN.fit(X_train,Y_train,epochs=200,batch_size=64,verbose=0)
#    eval_train = NN.evaluate(X_train,Y_train)
#    eval_val = NN.evaluate(X_val,Y_val)
#    eval_test = NN.evaluate(X_test,Y_test)
#    print ('Train accuracy:%.3f' % (eval_train[1]*100))
#    print ('Validation accuracy:%.3f' % (eval_val[1]*100))
#    print ('Test accuracy:%.3f' % (eval_test[1]*100))
    #Can achieve 97.5
#    NN = Sequential()
#    NN.add(Dense(units=2,input_dim=11,kernel_regularizer=regularizers.l2(0.01)))
#    NN.add(Activation('linear'))
#    sgd = optimizers.SGD(lr=0.01,momentum=0,decay=0)
#    NN.compile(loss='hinge',optimizer=sgd,metrics=['accuracy'])
#    NN.fit(X_train,Y_train,epochs=1000,batch_size=Y_train.shape[0],verbose=0)
#    Y_pred_train = NN.predict(X_train)
#    Y_pred_val = NN.predict(X_val)
#    Y_pred_test = NN.predict(X_test)
#    eval_train = NN.evaluate(X_train,Y_train)
#    eval_val = NN.evaluate(X_val,Y_val)
#    eval_test = NN.evaluate(X_test,Y_test)
#    print ('Train accuracy:%.3f' % (eval_train[1]*100))
#    print ('Validation accuracy:%.3f' % (eval_val[1]*100))
#    print ('Test accuracy:%.3f' % (eval_test[1]*100))
#    
