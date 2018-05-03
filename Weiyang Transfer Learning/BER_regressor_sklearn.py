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

from ParseData_BER import parse,split

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
db_to_dec = True
target = 'Q'
remove_lowQ = False
remove_badPoints = False
#train_ratios = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
train_ratios = [0.9]
for train_ratio in train_ratios:
    if True:
        normalized = True
#        files_withlabel = [
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=11.5.txt',
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=12.0.txt',
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=12.5.txt',
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=13.0.txt',
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=13.5.txt',  
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/smf4span+dsf3span/11channel/data_attenuation=14.0.txt',
#                ]


        files_withlabel = [
                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/leaf_2span_data_attenuation_=1.txt',
#                 r'/home/onsi/wmo/forIntern/modules/NonlinearTestbed/data/leaf_2span/leaf_2span_data_attenuation_=2.txt',
           
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
        train_ratio= 0.9
        test_ratio = 0.1
        train,test = split(data,shuffle=333,validation=False,train_ratio=train_ratio,test_ratio=test_ratio) #Use 454 for testing
        X_train = train[:,0:m_features]
        Y_train = train[:,m_features]
        label_train = train[:,m_features+1]
        X_test = test[:,0:m_features]
        Y_test = test[:,m_features]
        label_test = test[:,m_features+1]

        
        if normalized and 1:
            X_train_origin = copy.copy(X_train)
            X_test_origin = copy.copy(X_test)
#            scaler = MinMaxScaler()
            scaler = StandardScaler()
#            scaler = RobustScaler()  
            scaler.fit(X_train)  
            X_train = scaler.transform(X_train)  
            X_test = scaler.transform(X_test)  
        #1a Linear Regression 
        linReg = LinearRegression()
        linReg.fit(X_train,Y_train)  
        Y_pred_train = linReg.predict(X_train)
        Y_pred_test = linReg.predict(X_test)
        print('Linear Regression RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
        print('Linear Regression RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
        #1b Ridge Regression
#        ridgeReg = Ridge(alpha=1e-4)
#        ridgeReg.fit(X_train,Y_train)  
#        Y_pred_train = ridgeReg.predict(X_train)
#        Y_pred_test = ridgeReg.predict(X_test)
#        print('Ridge RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
#        print('Ridge RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#        #1c SGD
#        XGReg = XGBRegressor(n_estimators=200)
#        XGReg.fit(X_train,Y_train)  
#        Y_pred_train = XGReg.predict(X_train)
#        Y_pred_test = XGReg.predict(X_test)
#        print('XGB RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
#        print('XGB RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#        #1d RF regressor
        RFReg = RandomForestRegressor(n_estimators=40,max_features='auto')
        RFReg.fit(X_train,Y_train)
        Y_pred_train = RFReg.predict(X_train)
        Y_pred_test = RFReg.predict(X_test)
        print('RF-Regressor RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
        print('RF-Regressor RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#    ##    #2 Neural Network
#        neurons = (256,256,256)
        neurons = (700,300)
#        neurons = (4096)
##        neurons = (14,)
#        monitor = 0
#        max_iterations = 300
#    #    if monitor: #warm_start seems to have some bug, check later
#    #        rmse_test =[]
#    #        mlpReg = MLPRegressor(hidden_layer_sizes=neurons,alpha=1e-2,batch_size=60,tol=1e-2,solver='sgd',learning_rate='adaptive',max_iter=1,learning_rate_init=0.005,activation='linear',random_state=None,warm_start=True,verbose=True,shuffle=False)
#    #        for i in range(1,max_iterations):
#    #            mlpReg.fit(X_train,Y_train)  
#    #            if (i%10==0):              
#    #                Y_pred_train = mlpReg.predict(X_train)
#    #                Y_pred_test = mlpReg.predict(X_test)
#    #                print('RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
#    #                print('RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#    #                rmse_test.append(np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
#    
#                #(2) Plot training y and yhat   
#    #                if True:
#    #                    plt.figure()
#    #                    pred_train = plt.scatter(range(len(Y_pred_train)),Y_pred_train, color='blue',
#    #                         linewidth=0.01,label='Train Prediction')
#    #                    actual_train = plt.scatter(range(len(Y_train)),Y_train, color='red',
#    #                         linewidth=0.01,label='Train Actual')
#    #                    plt.legend(handles=[pred_train,actual_train])
#    #                    plt.grid()
#    #                    plt.ylim([-0.002,0.006])
#    #                    plt.ylabel('BER')
#    #                    plt.xlabel('case number')
#    #        
#    #                    plt.xticks(())
#    #                    plt.yticks(())
#    #                    plt.show()
#    #                    
#    #                    plt.figure()
#    #                    train_error=plt.scatter(Y_train,Y_pred_train, color='red',
#    #                         linewidth=0.01,label='train error')
#    #                    plt.plot(np.linspace(0,0.006,100),np.linspace(0,0.006,100))
#    #                    plt.grid()
#    #                    plt.legend(handles=[train_error])
#    #                    plt.xlim([0,0.006])
#    #                    plt.ylim([-0.001,0.006])
#    #                    plt.ylabel('Actual BER')
#    #                    plt.xlabel('Predicted BER') 
#    #        sys.exit()
#    ##
        mlpReg = MLPRegressor(hidden_layer_sizes=neurons,alpha=1e-2,batch_size=100,tol=1e-4,learning_rate_init=0.005,solver='sgd',learning_rate='adaptive',activation='relu',early_stopping=False,verbose=True)
#        mlpReg = RandomForestRegressor(n_estimators=100)
#        mlpReg = XGBRegressor(n_estimators=200)
#        mlpReg = Ridge()
#        mlpReg = AdaBoostRegressor(n_estimators=200,learning_rate=0.05,loss='square')
#        mlpReg = AdaBoostRegressor(n_estimators=200,learning_rate=0.05,loss='square')
#        mlpReg = Regressor(
#                layers=[
#                        Layer("Rectifier",units=700),
#                        Layer("Rectifier",units=300),
#                        Layer("Linear")],
#                batch_size = 60,
#                learning_rate=0.005,
#                n_iter=100,
#                n_stable=10,
#                regularize='L2',
#                weight_decay=1e-3,
#                        )
        mlpReg.fit(X_train,Y_train)
        Y_pred_train = mlpReg.predict(X_train)
        Y_pred_test = mlpReg.predict(X_test)
        print('NN-MLP RMSE of train:%.8f' % np.sqrt(mean_squared_error(Y_train,Y_pred_train)))
        print('NN-MLP RMSE of testing:%.8f' % np.sqrt(mean_squared_error(Y_test,Y_pred_test)))
        
    if 1:
        plt.figure()
#        pred_train = plt.scatter(range(len(Y_pred_train)),Y_pred_train, color='blue',
#             linewidth=0.01,label='Train Prediction')
        actual_train = plt.scatter(range(len(Y_train)),Y_train, color='red',
             linewidth=0.01,label='Train Actual')
        plt.legend(handles=[actual_train])
        plt.grid()
    #    plt.ylim([-0.002,0.006])
        plt.ylabel('Q')
        plt.xlabel('case number')
        plt.show()
        
        plt.figure()
        train_error=plt.scatter(Y_train,Y_pred_train, color='red',
             linewidth=0.01,s=4,label='train True vs. Prediction')
        plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
        plt.grid()
        plt.legend(handles=[train_error])
    #    plt.xlim([0,0.006])
    #    plt.ylim([-0.001,0.006])
        plt.ylabel('Actual Q')
        plt.xlabel('Predicted Q') 
    ##(3) Plot prediction y and yhat
    if 1:
        plt.figure()
#        pred_test = plt.scatter(range(len(Y_pred_test)),Y_pred_test, color='blue',
#             linewidth=0.002,label='Test Prediction')
        actual_test = plt.scatter(range(len(Y_test)),Y_test, color='red',
             linewidth=0.002,label='Test Actual')
        plt.legend(handles=[actual_test])
        plt.grid()
    #    plt.ylim([-0.002,0.006])
        plt.ylabel('Q')
        plt.xlabel('case number')
        
    #    plt.xticks(())
    #    plt.yticks(())
        plt.show()
        
        plt.figure()
        test_error=plt.scatter(Y_test,Y_pred_test, color='red',
             linewidth=0.002,label='Test True vs. Prediction')
        plt.plot(np.linspace(minQ-0.5,maxQ+0.5,100),np.linspace(minQ-0.5,maxQ+0.5,100))
        plt.grid()
        plt.legend(handles=[test_error])
    #    plt.xlim([0,0.006])
    #    plt.ylim([-0.001,0.006])
        plt.ylabel('Actual Q')
        plt.xlabel('Predicted Q')
        
    if 1:
        Y_diff = Y_pred_test - Y_test
        print('Maximum Prediction Q Error:%s dB,%s dB' % (np.max(Y_diff),np.min(Y_diff)))
        locs = np.argwhere(abs(Y_diff)>0.3)
        label_has_big_error = label_test[locs]
        
    #if 1:
    #    plt.figure()
    #    Y_error = Y_pred_test-Y_test
    #    plt.imshow(np.atleast_2d(Y_error),extent=(min(Y_error),max(Y_error),min(Y_error),max(Y_error)),cmap=cm.hot)
    #    plt.colorbar()
    #    plt.show()
    #    
    if 1:
        ###(4) Show classification accuracy
        Q_threshold = 11 #Correspond to BER=1e-3
        Y_pred_test_cls = copy.copy(Y_pred_test)
        Y_test_cls = copy.copy(Y_test)
        Y_pred_test_cls[Y_pred_test_cls<=Q_threshold]=0
        Y_pred_test_cls[Y_pred_test_cls>Q_threshold]=1
        Y_test_cls[Y_test_cls<=Q_threshold]=0
        Y_test_cls[Y_test_cls>Q_threshold]=1
        accuracy = accuracy_score(Y_pred_test_cls,Y_test_cls)
        print('Accuracy of classification is %s' % accuracy)
        print('\n')
    
    if 0:
        ###(5) ROC curve
        FPR,TPR,threshold=roc_curve(Y_test_cls,Y_pred_test)
        auc=roc_auc_score(Y_test_cls,Y_pred_test)
        print('Area under ROC curve:%s' % auc)
    
    if 0:
        threshold = 0.2
        accuracy = numericalAccuracy(Y_pred_test,Y_test,threshold=threshold)
        print('Accuracy with 0.2 dB threshold is %s' % accuracy) 