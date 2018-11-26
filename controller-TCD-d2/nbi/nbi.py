# North Bound Interface
from ryu.app.wsgi import ControllerBase
from ryu.base import app_manager
from ryu.app.wsgi import WSGIApplication

import nbi_config as nbic
import event_config

import yaml

class NorthBoundInterface(ControllerBase):
    
    # Detect is a traffic request between tx_node and rx_node --> NBI
    # Insert into database new lightpath and set status to evaluating --> DB_MGMT
    # Calculate path between tx_node and rx_node --> PCE
    # Evaluate calculated path for tx_node and rx_node --> RWA
    # Insert resources into database --> DB_MGMT
    # Update database (if needed) --> DB_MGMT
    
    _EVENTS = [event_config.LightpathCreateEvent]
    
    def __init__(self, req, link, data, **config):
        ControllerBase.__init__(self, req, link, data, **config)
        
    # Input: 
    #   - req: http-post body message [json format].
    #   - cmd: uri passed in http command.
    # Output:
    #   - Retrieve lightpath data and insert into database
    #   - Calculate Path (delegate to PCE)
    def handle_create_lightpath(self, req, cmd, **_kwargs):
        if cmd == nbic.NBI_CREATE_LIGHTPATH:
            json_str = req.body
            decoded = yaml.load(json_str)
            lightpath_data = decoded['lightpath'][0]            
            lightpath_event = event_config.LightpathCreateEvent()
            lightpath_event.lightpath_id = nbic.NBI_LIGHTPATH_ID
            lightpath_event.tx_node = lightpath_data['tx_node']
            lightpath_event.rx_node = lightpath_data['rx_node']
            lightpath_event.status = 0 # status Reserve/To-be-processed
            RESTAPIobj.send_event('DatabaseManagement',  lightpath_event)
            nbic.NBI_LIGHTPATH_ID += 1
            return nbic.NBI_CREATE_LIGHTPATH_REPLY
        
class NorthBoundInterfaceConnection(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(NorthBoundInterfaceConnection, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        self.data = {}
        mapper = wsgi.mapper

        wsgi.registory['NorthBoundInterface'] = self.data
        newpath = ''
        uri = newpath +'/{cmd}'
        mapper.connect('nbi-conf',uri,
                      controller=NorthBoundInterface, action='handle_create_lightpath',
                      conditions=dict(method=['POST','GET']))
                      
        global RESTAPIobj
        RESTAPIobj = self
