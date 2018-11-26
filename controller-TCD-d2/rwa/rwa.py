# Routing and Wavelength Assignment
from ryu.base import app_manager
import sys
sys.path.insert(0, '/var/opt/Optical-Network-Emulation/controller-TCD-d2')
from database import database_management as dbm
import event_config
from thread import *
import threading
exec_lock = threading.Lock()
# Input: TX-node, RX-node, Path
# Output: 
# 1) Find common available wavelengths among the links (Path)
# 2) Reserve common available channels
# 3) Insert route-sequences into database
# 4) Insert link_to_channel resources into database
# 5) Set lightpaths as established

class RoutingWavelengthAssignmentElement(app_manager.RyuApp):
    
    _EVENTS = [event_config.RouteAddEvent, 
                        event_config.LightpathCancelEvent]
    
    
    
    def __init__(self, *args, **kwargs):
        super(RoutingWavelengthAssignmentElement, self).__init__(*args, **kwargs)
        self.dbm = dbm.DatabaseManagement()
        self.temp_channel_count = 0
        self.CHANNELS = [40, 85, 31, 69, 61, 4, 48, 45, 72, 86, 88, 55, 82, 
                            63, 16, 22, 25, 67, 23, 18, 2, 77, 71, 14, 53, 51, 79, 32, 
                            9, 66, 5, 34, 35, 76, 24, 42, 36, 19, 52, 60, 81, 57, 20, 
                            47, 43, 68, 1, 11, 65, 78, 8, 56, 64, 21, 33, 62, 70, 10, 89, 
                            46, 44, 49, 7, 17, 38, 39, 13, 80, 58, 83, 26, 87, 90, 54, 3, 
                            12, 27, 28, 59, 75, 30, 74, 73, 84, 50, 15, 29, 41, 6, 37]
                            
        self.CHANNELS_REVERSE = [40, 37, 6, 41, 29, 15, 50, 84, 73, 74, 30, 75, 59, 28, 27, 
                    12, 3, 54, 90, 87, 26, 83, 58, 80, 13, 39, 38, 17, 7, 49, 44, 
                    46, 89, 10, 70, 62, 33, 21, 64, 56, 8, 78, 65, 11, 1, 68, 43, 
                    47, 20, 57, 81, 60, 52, 19, 36, 42, 24, 76, 35, 34, 5, 66, 9, 
                    32, 79, 51, 53, 14, 71, 77, 2, 18, 23, 67, 25, 22, 16, 63, 82, 
                    55, 88, 86, 72, 45, 48, 4, 61, 69, 31, 85]
        
     # functional method of threaded function:
    # call_remote_mininet_server(self, ev) below.
    def threaded(self, route, last_node_in_sequence):
        lightpath_id = route[0]
        try:
            link_id = route[2]
            available_channels = self.dbm.l_handle_get_available_channels(link_id)
            available_channels_no = len(available_channels)
            if available_channels_no > 0:
                channel = self.wavelength_assignment(available_channels)
                #insert route into database
                route_event = event_config.RouteAddEvent()
                route_event.lightpath_id = lightpath_id
                route_event.sequence = route[1]
                route_event.link_id = link_id
                route_event.channel = channel
                route_event.last_node_in_sequence = last_node_in_sequence
                self.send_event('DatabaseManagement',  route_event)
                self.send_event('SouthBoundInterface',  route_event)
            exec_lock.release()
        except:
            lightpath_cancel_event = event_config.LightpathCancelEvent()
            lightpath_cancel_event.lightpath_id = lightpath_id
            self.send_event("DatabaseManagement", lightpath_cancel_event)
        
    # 1) Find common available wavelengths among the links (Path)
    # input: route (tuple)
    # output: raises a RouteAddEvent --> DatabaseManagement to
   # insert a route 
    def route_evaluation(self,  route, last_node_in_sequence):
        exec_lock.acquire()
        start_new_thread(self.threaded, (route, last_node_in_sequence))
        
        
    # input: available_channels (list)
    # output: channel_id (int), which is the first available channel
    # in the given list
    def wavelength_assignment(self, available_channels):
        channel_id = self.CHANNELS_REVERSE[self.temp_channel_count]
        self.temp_channel_count += 1
        return channel_id
        # select first available channel
#        channel_element = available_channels[0]
#        channel_id = channel_element[1]
#        return channel_id
