from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.controller import event
from Common import *
import Database
import Custom_event

import logging

logging.basicConfig(level = log_level)

class RequestTest(app_manager.RyuApp):

	_EVENTS =  [Custom_event.North_CrossDomainTrafficRequestEvent]

	def __init__(self,*args,**kwargs):
        	super(RequestTest,self).__init__(*args,**kwargs)
		hub.sleep(15)
		new_north_traffic_request_ev = Custom_event.North_CrossDomainTrafficRequestEvent()
		new_north_traffic_request_ev.traf_id = 1
		new_north_traffic_request_ev.traf_stage = TRAFFIC_WORKING
		new_north_traffic_request_ev.traf_state = TRAFFIC_RECEIVE_REQUEST
		new_north_traffic_request_ev.src_node_ip = '192.168.1.1'
		new_north_traffic_request_ev.dst_node_ip = '192.168.2.1'
		new_north_traffic_request_ev.traf_type = TRAFFIC_CROSS_DOMAIN
		new_north_traffic_request_ev.prot_type = TRAFFIC_REROUTING_RESTORATION
		new_north_traffic_request_ev.bw_demand = 50
		new_north_traffic_request_ev.OSNR_req = 0
		new_north_traffic_request_ev.domain_num = 2
		new_north_traffic_request_ev.domain_sequence = [1,2]
		#hub.sleep(1)
		self.logger.debug('Attempting to send EVENT')
		self.send_event('Cross_domain_connection_ctrl', new_north_traffic_request_ev)
		self.logger.debug("\nFirst north traffic request event")

	#def start(self):
	#	super(RequestTest,self).start()
		
