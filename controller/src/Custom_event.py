"""
Custom event definitions

Author:   Yao Li (yaoli@optics.arizona.edu)
Created:  2017/01/09
Version:  1.0

Last modified by Yao: 2017/05/19

"""

from ryu.controller import event

# North-bound communication events

class North_CrossDomainTrafficRequestEvent(event.EventBase):
#generate: North_bound_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(North_CrossDomainTrafficRequestEvent, self).__init__()
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        self.src_node_ip = ''
        self.dst_node_ip = ''
        self.traf_type = 0
        self.prot_type = 0
        self.up_time = None
        self.down_time = None
        self.bw_demand = 0
        self.OSNR_req = 0
        self.domain_num = 0
        self.domain_sequence = []
        
class North_IntraDomainTrafficRequestEvent(event.EventBase):
#generate: North_bound_message_receive
#listening: Intra_domain_connection_ctrl
    def __init__(self):
        super(North_IntraDomainTrafficRequestEvent, self).__init__()
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        self.src_node_ip = ''
        self.dst_node_ip = ''
        self.traf_type = 0
        self.prot_type = 0
        self.up_time = None
        self.down_time = None
        self.bw_demand = 0
        self.OSNR_req = 0
        self.domain_num = 0
        self.domain_sequence = []
        
class North_TrafficReplyEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: North_bound_message_send
    def __init__(self):
        super(North_TrafficReplyEvent, self).__init__()
        self.traf_id = 0
        self.result = 0
        self.traf_stage = 0
        self.traf_state = 0
        
class North_IntraDomainTrafficTeardownRequestEvent(event.EventBase):
#generate: North_bound_message_receive
#listening: Intra_domain_connection_ctrl
    def __init__(self):
        super(North_IntraDomainTrafficTeardownRequestEvent, self).__init__()
        self.traf_id = 0
        
class North_CrossDomainTrafficTeardownRequestEvent(event.EventBase):
#generate: North_bound_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(North_CrossDomainTrafficTeardownRequestEvent, self).__init__()
        self.traf_id = 0
        
class North_TrafficTeardownReplyEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: North_bound_message_send
    def __init__(self):
        super(North_TrafficTeardownReplyEvent, self).__init__()
        self.traf_id = 0
        self.result = 0
        self.traf_stage = 0
        self.traf_state = 0
       
class North_TrafficStateUpdateEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: North_bound_message_send
    def __init__(self):
        super(North_TrafficStateUpdateEvent, self).__init__()
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        
# North-bound communication events end
 
# South-bound communication events       

class South_LSPSetupRequestEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: Intra_domain_connection_ctrl
   def __init__(self):
        super(South_LSPSetupRequestEvent, self).__init__() 
        self.traf_id = 0
        
class South_LSPSetupReplyEvent(event.EventBase):
#generate: South_bound_message_receive
#listening: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl 
   def __init__(self):
        super(South_LSPSetupReplyEvent, self).__init__() 
        self.traf_id = 0
        self.result = None
        
class South_LSPTeardownRequestEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: Intra_domain_connection_ctrl
   def __init__(self):
        super(South_LSPTeardownRequestEvent, self).__init__() 
        self.traf_id = 0
      
class South_LSPTeardownReplyEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl
#listening: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
   def __init__(self):
        super(South_LSPTeardownReplyEvent, self).__init__() 
        self.traf_id = 0
        self.result = None
 
class South_OSNRMonitoringRequestEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: Monitoring
   def __init__(self):
        super(South_OSNRMonitoringRequestEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None
        
class South_OSNRMonitoringReplyEvent(event.EventBase):
#generate: Monitoring
#listening: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl 
   def __init__(self):
        super(South_OSNRMonitoringReplyEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None
        self.result = None
        self.is_OSNR_all_good = None    #True or False
        self.is_impairtment_at_this_domain = None   #True or False

# South-bound communication events end

# EastWest-bound communication events

class EastWest_SendPathCompRequestEvent(event.EventBase):
#generate: Path_computation
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendPathCompRequestEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = 0
        self.entry_of_next_domain = []  #a list of [node_ip, node_port_id, route_type, cost, [common_avai_chnls]]
        
class EastWest_ReceivePathCompRequestEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Path_computation
    def __init__(self):
        super(EastWest_ReceivePathCompRequestEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = 0
        self.entry_of_next_domain = []  #a list of [node_ip, node_port_id, route_type, cost, [common_avai_chnls]]
        
class EastWest_SendPathCompReplyEvent(event.EventBase):
    def __init__(self):
#generate: Path_computation
#listening: EastWest_message_send
        super(EastWest_SendPathCompReplyEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = 0
        self.result = None  #SUCCESS or FAIL
        #self.resource_allocation = []   # a list of [occupied chnl IDs]
        self.exit_of_previous_domain = []   # a list of [node_ip, node_port_id, route_type, [chnls]]
        
class EastWest_ReceivePathCompReplyEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Path_computation
    def __init__(self):
        super(EastWest_ReceivePathCompReplyEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = 0
        self.result = None  #SUCCESS or FAIL
        #self.resource_allocation = []   # a list of [occupied chnl IDs]
        self.exit_of_this_domain = []   # a list of [node_ip, node_port_id, route_type, [chnls]]
        
class EastWest_SendTrafSetupRequestEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendTrafSetupRequestEvent, self).__init__() 
        self.traf_id = 0
        self.traf_stage = 0
        
class EastWest_ReceiveTrafSetupRequestEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveTrafSetupRequestEvent, self).__init__()
        self.traf_id = 0
        self.traf_stage = 0
        
class EastWest_SendTrafSetupReplyEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendTrafSetupReplyEvent, self).__init__() 
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        self.result = None
        
class EastWest_ReceiveTrafSetupReplyEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveTrafSetupReplyEvent, self).__init__()
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        self.result = None
 
class EastWest_SendTrafTeardownRequest(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendTrafTeardownRequest, self).__init__() 
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        
class EastWest_ReceiveTrafTeardownRequest(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveTrafTeardownRequest, self).__init__() 
        self.traf_id = 0
        self.traf_stage = 0
        self.traf_state = 0
        
class EastWest_SendTrafTeardownReply(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendTrafTeardownReply, self).__init__() 
        self.traf_id = 0
        self.result = 0
        
class EastWest_ReceiveTrafTeardownReply(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveTrafTeardownReply, self).__init__() 
        self.traf_id = 0
        self.result = 0
        
class EastWest_SendTearDownPath(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendTearDownPath, self).__init__() 
        self.traf_id = 0
        self.route_type = 0
     
class EastWest_ReceiveTearDownPath(event.EventBase):
#generate: EastWest_message_receive, Cross_domain_connection_ctrl
#listening: Cross_domain_connection_ctrl, Intra_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveTearDownPath, self).__init__() 
        self.traf_id = 0
        self.route_type = 0

class EastWest_SendOSNRMonitoringRequestEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendOSNRMonitoringRequestEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None

class EastWest_ReceiveOSNRMonitoringRequestEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveOSNRMonitoringRequestEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None
        #self.result = None

class EastWest_SendOSNRMonitoringReplyEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: EastWest_message_send
    def __init__(self):
        super(EastWest_SendOSNRMonitoringReplyEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None
        self.result = None
        self.is_inter_domain_impairment = None  #True or False
        self.traf_stage = 0
        self.traf_state = 0

class EastWest_ReceiveOSNRMonitoringReplyEvent(event.EventBase):
#generate: EastWest_message_receive
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(EastWest_ReceiveOSNRMonitoringReplyEvent, self).__init__() 
        self.traf_id = 0
        self.route_type = None
        self.result = None
        self.is_inter_domain_impairment = None  #True or False
        self.traf_stage = 0
        self.traf_state = 0

# EastWest-bound communication events end

# Intra-domain FSM state transition events

#class TrafSetupRequestEvent(event.EventBase)):
#   """generate: Nouth_bound_message_receiving.py
#      listening: Path_computation.py
#   """ 
#    def __init__(self):
 #       super(TrafSetupRequestEvent, self).__init__() 
 #       self.traf_id = 0
        
class IntraDomainPathCompRequestEvent(event.EventBase):
#generate: Intra_domain_connection_ctrl
#listening: Path_computation
    def __init__(self):
        super(IntraDomainPathCompRequestEvent, self).__init__() 
        self.traf_id = 0
        
class IntraDomainPathCompReplyEvent(event.EventBase):
#generate: Path_computation
#listening: Intra_domain_connection_ctrl
    def __init__(self):
        super(IntraDomainPathCompReplyEvent, self).__init__() 
        self.traf_id = 0
        self.result = None  # SUCCESS or FAIL (please see Common.py)
        
class CrossDomainPathCompRequestEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: Path_computation 
    def __init__(self):
        super(CrossDomainPathCompRequestEvent, self).__init__() 
        self.traf_id = 0

class CrossDomainPathCompReplyEvent(event.EventBase):
#generate: Path_computation
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(CrossDomainPathCompReplyEvent, self).__init__() 
        self.traf_id = 0
        self.result = None # SUCCESS or FAIL (please see Common.py)
        
class CrossDomainReroutingRequestEvent(event.EventBase):
#generate: Cross_domain_connection_ctrl
#listening: Path_computation 
    def __init__(self):
        super(CrossDomainReroutingRequestEvent, self).__init__() 
        self.traf_id = 0

class CrossDomainReroutingReplyEvent(event.EventBase):
#generate: Path_computation
#listening: Cross_domain_connection_ctrl
    def __init__(self):
        super(CrossDomainReroutingReplyEvent, self).__init__() 
        self.traf_id = 0
        self.result = None # SUCCESS or FAIL (please see Common.py)
        
class IntraDomainReroutingRequest(event.EventBase):
#generate: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl
#listening: Path_computation 
   def __init__(self):
        super(IntraDomainReroutingRequest, self).__init__() 
        self.traf_id = 0
        
class IntraDomainReroutingReply(event.EventBase):
#generate: Path_computation
#listening: Intra_domain_connection_ctrl, Cross_domain_connection_ctrl 
   def __init__(self):
        super(IntraDomainReroutingReply, self).__init__() 
        self.traf_id = 0
        self.result = None  #SUCCESS or FAIL

# Intra-domain FSM state transition events end