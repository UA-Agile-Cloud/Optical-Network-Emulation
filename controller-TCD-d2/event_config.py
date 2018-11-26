from ryu.controller import event

# LIGHTPATH - RELATED EVENTS
class LightpathCreateEvent(event.EventBase):
    def __init__(self):
        super(LightpathCreateEvent, self).__init__()
        self.lightpath_id = 0
        self.tx_node = 0
        self.rx_node = 0
        
class LightpathActivateEvent(event.EventBase):
    def __init__(self):
        super(LightpathActivateEvent, self).__init__()
        self.lightpath_id = 0
        self.status = 0
        self.channel = 0
        
class LightpathCancelEvent(event.EventBase):
    def __init__(self):
        super(LightpathCancelEvent, self).__init__()
        self.lightpath_id = 0
        
class RouteAddEvent(event.EventBase):
    def __init__(self):
        super(RouteAddEvent, self).__init__()
        self.lightpath_id = 0
        self.sequence = 0
        self.link_id = 0
        self.channel = -1
        self.last_node_in_sequence = 0

# SOUTHBOUND INTERFACE - RELATED EVENTS
class RemoteMininetClientEvent(event.EventBase):
    def __init__(self):
        super(RemoteMininetClientEvent, self).__init__()
        self.lightpath_id = 0
        self.channel = 0
