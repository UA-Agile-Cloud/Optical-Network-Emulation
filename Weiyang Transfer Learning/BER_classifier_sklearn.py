#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 12:00:58 2017

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
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor
from sklearn.linear_model import SGDRegressor,Ridge,RidgeCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier,MLPRegressor
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression,Ridge,BayesianRidge,SGDRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler 
from scipy.special import  erfcinv
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC

from ParseData_BER import parse,split

def BER2Q(BER):
    if type(BER) == float:
        BER = np.asarray(BER)
    q = np.zeros(BER.shape)
    idx2Cal = BER < 0.5
    tmpQ =  20*np.log10((np.sqrt(2)*erfcinv(BER[idx2Cal]/.5)))
    q[idx2Cal] = tmpQ
    return q

#(1) Train and Predictions
target = 'Q'
classifier = 'True'
if True:
    normalized = True
    files = [r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=7.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=8.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=9.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=10.txt',
             r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf_4span/11channel/data_attenuation=11.txt',
            ]
    tmp = []
    for filename in files:
        X,Y,labels = parse(filename,startchannel=42,endchannel=52)
        if target=='Q':
            Y = BER2Q(Y)
        if classifier:
            Q_threshold = 9.8 #Correspond to BER=1e-3
            Y[Y<=Q_threshold]=0
            Y[Y>Q_threshold]=1
        data = np.concatenate([X,Y,labels],axis=1)
        tmp.append(data)
    data = np.concatenate(tmp)
    m_features = data.shape[1]-2
    train_ratio= 0.9
    test_ratio = 0.1
    train,test = split(data,shuffle=10000,validation=False,train_ratio=train_ratio,test_ratio=test_ratio)
    X_train = train[:,0:m_features]
    Y_train = train[:,m_features]
    label_train = train[:,m_features+1]
    X_test = test[:,0:m_features]
    Y_test = test[:,m_features]
    label_test = train[:,m_features+1]
    if normalized:
        scaler = StandardScaler()  
        scaler.fit(X_train)  
        X_train = scaler.transform(X_train)  
        X_test = scaler.transform(X_test)  
    #1a Random Forest
    RFclf = RandomForestClassifier(n_estimators=100,criterion='gini')
    RFclf.fit(X_train,Y_train)  
    Y_pred_test = RFclf.predict(X_test)
    accuracy = accuracy_score(Y_pred_test,Y_test)
    print('Accuracy of Random Forest classification is %s' % accuracy)
    #1b KNeighborsClassifier
    KNclf = KNeighborsClassifier(n_neighbors=15,weights='uniform',p=1)
    KNclf.fit(X_train,Y_train)
    Y_pred_test = KNclf.predict(X_test)
    accuracy = accuracy_score(Y_pred_test,Y_test)
    print('Accuracy of K-neighbour classification is %s' % accuracy)
    #1C SVM
    SVMclf = SVC(kernel='rbf')
    SVMclf.fit(X_train,Y_train)  
    Y_pred_test =SVMclf.predict(X_test)
    accuracy = accuracy_score(Y_pred_test,Y_test)
    print('Accuracy of SVM is %s' % accuracy)
    #1c NN
#    neurons = (180,120,60,15)
#    mlpclf = MLPClassifier(hidden_layer_sizes=neurons,alpha=1e-2,batch_size=60,solver='sgd',learning_rate='adaptive',max_iter=1000,activation='relu',early_stopping=False,verbose=True,random_state=None,shuffle=True)
#    mlpclf.fit(X_train,Y_train)
#    Y_pred_test = KNclf.predict(X_test)
#    accuracy = accuracy_score(Y_pred_test,Y_test)
#    print('Accuracy of NNMLP classification is %s' % accuracy)
#    
   