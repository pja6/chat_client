import tkinter as tk
from tkinter import scrolledtext, messagebox
from socket import *
from threading import *

class base_connection:
    def __init__(self, on_msg_rcvd):
        #call when message arrives
        self.on_msg_rcvd = on_msg_rcvd
        self.running = False
        self.socket = None
        
    def send(self, msg):
        #needs to be used by subclass
        raise NotImplementedError
    
    def start(self):
        raise NotImplementedError
    
    def close(self):
        raise NotImplementedError
    
class client_connect(base_connection):
    def __init__(self, host, port, on_msg_rcvd):
        super().__init__(on_msg_rcvd)
        self.host = host
        self.port = port
        
        
    def start(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.running = True
        
        #receive in background thread
        
        receive_thread = Thread(target=self._receive_loop)
        receive_thread.daemon = True
        receive_thread.start()
        
    def _receive_loop(self):
        while self.running:
            try:
               message = self.socket.recv(1024).decode('utf-8')
               if not message:
                   
                   break
            except Exception as e:
                ConnectionResetError
                pass
            
        
    def send(self):
        return
        

    
    def close(self):
        return
        
class server_connect(base_connection):
    def __init__(self, port, on_msg_rcvd):
        super().__init__(on_msg_rcvd)
        self.port = port
        
    def start(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.listen(5)
        while self.running:
            self.accept()
        
        
    def listen(num_req):
        return
    
    def accept(self):
        return
    
    def send(self):
        return

    def close():
        return