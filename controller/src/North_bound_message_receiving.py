"""
Generate events after receiving north-bound messages 

Author:   Yao Li (yaoli@optics.arizona.edu.cn)
Created:  2017/01/16
Version:  1.0

Last modified by Yao: 2017/01/20

"""

from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from Common import *
#import Database
#from ryu.lib import Custom_events
import logging
#import MySQLdb
import SocketServer


import urllib
import urllib2
import httplib
import requests

import json
import yaml
import pycurl
from webob import Response

from ryu.base import app_manager
from ryu.controller import ofp_event, event
import Custom_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.lib import ofctl_v1_0
from ryu.lib import ofctl_v1_2
from ryu.lib import ofctl_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication
from ryu.lib.ip import ipv4_to_bin
from StringIO import StringIO 


LOG = logging.getLogger('ryu.app.NBMRrest')

RESTAPIobj = None

class North_bound_message_receive(ControllerBase):#app_manager.RyuApp): 
    
    _EVENTS =  [Custom_event.North_CrossDomainTrafficRequestEvent,
                Custom_event.North_IntraDomainTrafficRequestEvent,
                Custom_event.North_IntraDomainTrafficTeardownRequestEvent,
                Custom_event.North_CrossDomainTrafficTeardownRequestEvent]
                
   # def __init__(self,*args,**kwargs):
       # super(North_bound_message_receive,self).__init__(*args,**kwargs)
       # self.listening_thread = hub.spawn(self._listening)
        
 #   def _listening(self):
        #pass
        #while True:
            #receive a message
            #setup a timer in north_timer
            #send events to other modules based on message type
            #if there are items in north_timer to be timeout:
            #   send timeout reply
            #   delete these timers
            #hub.sleep(1)

    def __init__(self, req, link, data, **config):
        ControllerBase.__init__(self,req, link, data, **config)
        #self.listening_thread = hub.spawn(self._listening)

    def handle_empty_request(self,req,**_kwargs):
        print '=========================================================='
        #print req
        #print '----------------------------------'

    def handle_traffic_request(self, req, cmd, **_kwargs):
        json_str = req.body
        decoded = yaml.load(json_str)
        if cmd == 'add_device':
            print 'Add Device Successfully'
            return 'add device'
        #else:
            #return 'Try ADD'
        elif cmd == 'TrafficRequest':
            request_class = decoded['Request_Class']
            if request_class == 'TrafficRequestEvent':
                print req
                return 'TrafficRequestEvent'
            elif request_class == 'North_TrafficTeardownReplyEvent':
                print req
                return 'North_TrafficTeardownReplyEvent'
            elif request_class == 'North_TrafficStateUpdateEvent':
                print req
                return 'North_TrafficStateUpdateEvent'

            elif request_class == 'CrossDomainRequest':
                traffic_request = Custom_event.North_CrossDomainTrafficRequestEvent()
                traffic_request.src_node_ip = decoded['Source_Node_IP']
                traffic_request.dst_node_ip = decoded['Destination_Node_IP']
                traffic_request.traf_id = int(decoded['Msg_ID'])
                traffic_request.traf_stage = TRAFFIC_WORKING
                traffic_request.traf_state =TRAFFIC_RECEIVE_REQUEST         
                traffic_request.traf_type = TRAFFIC_CROSS_DOMAIN
                traffic_request.prot_type = TRAFFIC_REROUTING_RESTORATION
                traffic_request.up_time = None
                traffic_request.down_time = None
                traffic_request.bw_demand = 50
                traffic_request.OSNR_req = 0
                traffic_request.domain_num = decoded['Domain_Num']
                traffic_request.domain_sequence = decoded['Domain_Sequence']
                RESTAPIobj.send_event('Cross_domain_connection_ctrl', traffic_request)

                status_return = {'Result':'CrossDomainRequest Received',
                                 'Traf_ID': traffic_request.traf_id,
                                 'Source_Node':traffic_request.src_node_ip,
                                 'Destination_Node':traffic_request.dst_node_ip,
                                 'Traf_Stage': traffic_request.traf_stage,
                                 'Traf_State': traffic_request.traf_state,         
                                 'Traf_Type': traffic_request.traf_type,
                                 'Prot_Type': traffic_request.prot_type,
                                 'Up_Time': traffic_request.up_time,
                                 'Down_Time': traffic_request.down_time,
                                 'BW_Demand': traffic_request.bw_demand,
                                 'OSNR_Req': traffic_request.OSNR_req,
                                 'Domain_Num': traffic_request.domain_num,
                                 'Domain_Seq': traffic_request.domain_sequence,                        
                                }
                data_string = json.dumps(status_return)
                print '========================================================='
                print req
                print '.............................'
                print data_string
                return data_string
            elif request_class == 'IntraDomainRequest':
                traffic_request = Custom_event.North_IntraDomainTrafficRequestEvent()
                traffic_request.src_node_ip = decoded['Source_Node_IP']
                traffic_request.dst_node_ip = decoded['Destination_Node_IP']
                traffic_request.traf_id = int(decoded['Msg_ID'])
                traffic_request.traf_stage = TRAFFIC_WORKING
                traffic_request.traf_state = TRAFFIC_RECEIVE_REQUEST           
                traffic_request.traf_type = TRAFFIC_INTRA_DOMAIN
                traffic_request.prot_type = TRAFFIC_REROUTING_RESTORATION
                traffic_request.up_time = None
                traffic_request.down_time = None
                traffic_request.bw_demand = 50
                traffic_request.OSNR_req = 0
                traffic_request.domain_num = 1
                traffic_request.domain_sequence = decoded['Domain_Sequence']
                RESTAPIobj.send_event('Intra_domain_connection_ctrl', traffic_request)
                status_return = {'Result':'IntraDomainRequest Received',
                                 'Traf_ID': traffic_request.traf_id,
                                 'Source_Node':traffic_request.src_node_ip,
                                 'Destination_Node':traffic_request.dst_node_ip,
                                 'Traf_Stage': traffic_request.traf_stage,
                                 'Traf_State': traffic_request.traf_state,         
                                 'Traf_Type': traffic_request.traf_type,
                                 'Prot_Type': traffic_request.prot_type,
                                 'Up_Time': traffic_request.up_time,
                                 'Down_Time': traffic_request.down_time,
                                 'BW_Demand': traffic_request.bw_demand,
                                 'OSNR_Req': traffic_request.OSNR_req,
                                 'Domain_Num': traffic_request.domain_num,
                                 'Domain_Seq': traffic_request.domain_sequence,                        
                                }
                data_string = json.dumps(status_return)
                print '========================================================='
                print req
                print '.............................'
                print data_string
                return data_string
            elif request_class == 'IntraDomainTearDown':
                traffic_request = Custom_event.North_IntraDomainTrafficTeardownRequestEvent()
                traffic_request.traf_id = int(decoded['TearTraf'])
                RESTAPIobj.send_event('Intra_domain_connection_ctrl', traffic_request)
                status_return = {'Result':'IntraDomainTearDown Received',
                                 'TearTraf' : traffic_request.traf_id,
                                }
                data_string = json.dumps(status_return)
                print '========================================================='
                print req
                print '.............................'
                print data_string
                return data_string
            elif request_class == 'CrossDomainTearDown':
                traffic_request = Custom_event.North_CrossDomainTrafficTeardownRequestEvent()
                traffic_request.traf_id = int(decoded['TearTraf'])
                status_return = {'Result':'CrossDomainTearDown Received',
                                 'TearTraf' : traffic_request.traf_id,
                                }
                data_string = json.dumps(status_return)
                print '========================================================='
                print req
                print '.............................'
                print data_string
                return data_string
            else:
                print '========================================================='
                print req
                print '.............................'
                print 'Wrong Request'
                return 'Wrong Request'
        else:
            print 'Try Other command'
            return 'Try Other command'

class RestStatsApi(app_manager.RyuApp):
    _EVENTS =  [Custom_event.North_CrossDomainTrafficRequestEvent,
                Custom_event.North_IntraDomainTrafficRequestEvent,
                Custom_event.North_IntraDomainTrafficTeardownRequestEvent,
                Custom_event.North_CrossDomainTrafficTeardownRequestEvent]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(RestStatsApi, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        self.data = {}
        mapper = wsgi.mapper

        wsgi.registory['North_bound_message_receive'] = self.data
        newpath = ''
        uri = newpath +'/{cmd}'
        mapper.connect('stats','/',
                      controller=North_bound_message_receive, action='handle_empty_request',
                      conditions=dict(method=['POST','GET']))
        mapper.connect('stats',uri,
                      controller=North_bound_message_receive, action='handle_traffic_request',
                      conditions=dict(method=['POST','GET']))

        global RESTAPIobj
        RESTAPIobj = self
       

        
            
