import socket
from thread import *
import threading

print_lock = threading.Lock()

class MySocketServer():
    def format_error(self):
        print(nbic.NBI_ID_MSG + 'Data receive from server in wrong format. Releasing socket lock.')
        # lock released on exit
        print_lock.release()
        
    # thread fuction
    def threaded(self,  c):
        while True:
     
            # data received from client
            data = c.recv(1024)
            if not data:
                format_error()
                break
     
            # reverse the given string from client
            data = data.split()
            if len(data) is not 3:
                format_error()
                break
            
            action = int(data[0])
            # Insert request == 0
            if action is 0:
                tx_node = int(data[1])
                rx_node = int(data[2])
                lightpath_event = event_config.AddLightpathEvent()
                lightpath_event.lightpath_id = nbic.NBI_LIGHTPATH_ID
                lightpath_event.tx_node = tx_node
                lightpath_event.rx_node = rx_node
                lightpath_event.status = 1
                self.send_event('database_management',  lightpath_event)
                #print(nbic.NBI_ID_MSG + 'Received TX-node: %s and RX-node: %s' %(tx_node, rx_node))
                print_lock.release()
                break
#db_mgmt.add_lightpath(lightpath_tuple)
            
            

        # connection closed
        c.close()

    def main(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((nbic.NBI_HOST, nbic.NBI_PORT))
        print(nbic.NBI_ID_MSG + 'socket binded to port %s' %nbic.NBI_PORT)
     
        # put the socket into listening mode
        s.listen(5)
        print(nbic.NBI_ID_MSG + 'listening')
     
        # a forever loop until client wants to exit
        while True:
            # establish connection with client
            c, addr = s.accept()
            # lock acquired by client
            print_lock.acquire()
            print(nbic.NBI_ID_MSG + 'connected to : %s : %s' %(addr[0], addr[1]))
     
            # Start a new thread and return its identifier
            start_new_thread(self.threaded, (c,))
        s.close()
