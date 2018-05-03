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
load_scaler = True
db_to_dec = True
target = 'Q'
remove_lowQ = False
remove_badPoints = False
#train_ratios = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
train_ratio = 0.008
val_ratio = 0.1
test_ratio = 0.1
if True:
    normalized = True
    
    files_withlabel = []
    files_nolabel = []


    files_withlabel = [
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=6.5.txt',  
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=7.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=7.5.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=8.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_4span/16qam/leaf_4span_data_attenuation_=8.5.txt',
            ]
#    files_withlabel = [                   
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=9.txt',
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=10.txt',
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=11.txt',
#                       ]
#    files_withlabel = [                   
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=9.txt',
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=10.txt',
#                       r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/11channel/data_attenuation=11.txt',
#                       ]
##        

    
#    files_withlabel = [
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=2.5.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.txt',
#                      r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/dsf_3span/qpsk/dsf_3span_data_attenuation_=3.5.txt',
#                      ]
 
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
    for filename in files_nolabel:
        X,Y,labels = parse(filename,startchannel=42,endchannel=52,label=None)
        if db_to_dec:
            X[X==0] = -float('inf')
            X = 10**(X/10)
        if target=='Q':
            Y = BER2Q(Y)
        data = np.concatenate([X,Y,labels],axis=1)
        tmp.append(data)
        
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
    X_train_origin = copy.copy(X_train)
    X_val_origin = copy.copy(X_val)
    X_test_origin = copy.copy(X_test)
    if load_scaler:
        scaler = joblib.load('scaler_2.pkl')
    else:
        scaler = StandardScaler()
        scaler.fit(X_train) 
    X_train = scaler.transform(X_train)  
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)  


    #Simple llnear regression RMSE: 0.19 for train,val,test (case 333)
    #Simple linear regression max error +/- 0.5dB, accuracy 93%
    loadmodel = True
    if loadmodel:
        NN = load_model('linear_regression_1.h5')
        for (i,layer) in enumerate(NN.layers):
            if i<len(NN.layers)-2:
                layer.trainable = False
        sgd = optimizers.SGD(lr=0.001,momentum=0.9,decay=1e-6)
        NN.compile(loss='mean_squared_error', optimizer=sgd)
        NN.fit(X_train,Y_train,epochs=200,batch_size=Y_train.size,verbose=0)
    else:
        NN = Sequential()
        units = 64
        l2 = 0
        dr = 0  #Dropout rate
#        NN.add(Dense(units=units,input_dim=11,kernel_regularizer=regularizers.l2(l2)))
#        NN.add(Activation('relu'))
#        NN.add(Dropout(dr))
##        NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
##        NN.add(Activation('relu'))
##        NN.add(Dropout(dr))
##        NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
##        NN.add(Activation('relu'))
##        NN.add(Dropout(dr))
##        NN.add(Dense(units=units,kernel_regularizer=regularizers.l2(l2)))
##        NN.add(Activation('relu'))
##        NN.add(Dropout(dr))     
#        NN.add(Dense(units=1))
#        NN.add(Activation('linear'))
        NN.add(Dense(units=1,input_dim=11))
        NN.add(Activation('linear'))
        sgd = optimizers.SGD(lr=0.01,momentum=0.9,decay=1e-6)
        NN.compile(loss='mean_squared_error', optimizer=sgd)
        NN.fit(X_train,Y_train,epochs=200,batch_size=Y_train.size,verbose=0)
        
    Y_pred_train = NN.predict(X_train)
    Y_pred_val = NN.predict(X_val)
    Y_pred_test = NN.predict(X_test)
    print('NN-MLP RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
    print('NN-MLP RMSE of val:%.8f' % np.sqrt(mean_squared_error(Y_val,Y_pred_val)))
    print('NN-MLP RMSE of test:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#    
#if 1:
#    plt.figure()
##        pred_train = plt.scatter(range(len(Y_pred_train)),Y_pred_train, color='blue',
##             linewidth=0.01,label='Train Prediction')
#    actual_train = plt.scatter(range(len(Y_train)),Y_train, color='red',
#         linewidth=0.01,label='Train Actual')
#    plt.legend(handles=[actual_train])
#    plt.grid()
##    plt.ylim([-0.002,0.006])
#    plt.ylabel('Q')
#    plt.xlabel('case number')
#    plt.show()
#    
#    plt.figure()
#    train_error=plt.scatter(Y_train,Y_pred_train, color='red',
#         linewidth=0.01,s=4,label='train True vs. Prediction')
#    plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
#    plt.grid()
#    plt.legend(handles=[train_error])
##    plt.xlim([0,0.006])
##    plt.ylim([-0.001,0.006])
#    plt.ylabel('Actual Q')
#    plt.xlabel('Predicted Q') 
###(3) Plot prediction y and yhat
if 1:
#    plt.figure()
##        pred_test = plt.scatter(range(len(Y_pred_test)),Y_pred_test, color='blue',
##             linewidth=0.002,label='Test Prediction')
#    actual_test = plt.scatter(range(len(Y_test)),Y_test, color='red',
#         linewidth=0.002,label='Test Actual')
#    plt.legend(handles=[actual_test])
#    plt.grid()
##    plt.ylim([-0.002,0.006])
#    plt.ylabel('Q')
#    plt.xlabel('case number')
#    
##    plt.xticks(())
##    plt.yticks(())
#    plt.show()
    
    plt.figure()
    test_error=plt.scatter(Y_test,Y_pred_test, color='red',
         linewidth=0.002,label='Test True vs. Prediction')
#    plt.plot(np.linspace(4,6,100),np.linspace(4,6,100))
    plt.grid()
    plt.legend(handles=[test_error])
#    plt.xlim([0,0.006])
#    plt.ylim([-0.001,0.006])
    plt.xlabel('Actual Q')
    plt.ylabel('Predicted Q')
##    
if 1:
    Y_diff_train = Y_pred_train - Y_train
    Y_diff_val = Y_pred_val - Y_val
    Y_diff_test = Y_pred_test - Y_test
    print('Maximum Prediction Q Error (train):%s dB,%s dB' % (np.max(Y_diff_train),np.min(Y_diff_train)))
    print('Maximum Prediction Q Error (val):%s dB,%s dB' % (np.max(Y_diff_val),np.min(Y_diff_val)))
    print('Maximum Prediction Q Error (test):%s dB,%s dB' % (np.max(Y_diff_test),np.min(Y_diff_test)))
#    locs = np.argwhere(abs(Y_diff)>0.3)
#    label_has_big_error = label_test[locs]
##    
###if 1:
###    plt.figure()
###    Y_error = Y_pred_test-Y_test
###    plt.imshow(np.atleast_2d(Y_error),extent=(min(Y_error),max(Y_error),min(Y_error),max(Y_error)),cmap=cm.hot)
###    plt.colorbar()
###    plt.show()
###    
#if 1:
#    ###(4) Show classification accuracy
#    Q_threshold = 9.8 #Correspond to BER=1e-3
#    Y_pred_test_cls = copy.copy(Y_pred_test)
#    Y_test_cls = copy.copy(Y_test)
#    Y_pred_test_cls[Y_pred_test_cls<=Q_threshold]=0
#    Y_pred_test_cls[Y_pred_test_cls>Q_threshold]=1
#    Y_test_cls[Y_test_cls<=Q_threshold]=0
#    Y_test_cls[Y_test_cls>Q_threshold]=1
#    accuracy = accuracy_score(Y_pred_test_cls,Y_test_cls)
#    print('Accuracy of classification is %s' % accuracy)
#    print('\n')
#
##if 0:
##    ###(5) ROC curve
##    FPR,TPR,threshold=roc_curve(Y_test_cls,Y_pred_test)
##    auc=roc_auc_score(Y_test_cls,Y_pred_test)
##    print('Area under ROC curve:%s' % auc)
##
##if 0:
##    threshold = 0.2
##    accuracy = numericalAccuracy(Y_pred_test,Y_test,threshold=threshold)
##    print('Accuracy with 0.2 dB threshold is %s' % accuracy) 