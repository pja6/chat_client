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
        if msg:
            try:
                self.socket.send((msg).encode('utf-8'))
            except Exception as e:
                print(f"No message: {e}")
    
    def start(self):
        raise NotImplementedError
    
    def close(self):
        raise NotImplementedError
    
    def _receive_loop(self):
        while self.running:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                
                if message: 
                    self.on_msg_rcvd(message)
                else:
                    break
            except Exception as e:
                print(f"Error receiving: {e}")
                self.running = False
                break
            
#Actively connects to a server (has host/port, calls connect())   
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
      

    def close(self):
        self.running = False
        if self.socket:
            self.socket.close()

# class represents a connection the server accepted
class client_handler(base_connection):
    def __init__(self, client_socket, on_msg_rcvd):
        super().__init__(on_msg_rcvd)
        self.socket = client_socket
        
    def start(self):
        self.running = True
        
        receive_thread = Thread(target=self._receive_loop)
        receive_thread.daemon=True
        receive_thread.start()
    
    # overrides base class  
    def _receive_loop(self):
         while self.running:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if message:
                    # Pass sender
                    self.on_msg_rcvd(message, self)  
                else:
                    break
            except Exception as e:
                print(f"Error receiving: {e}")
                self.running = False
                break
   
    def close(self):
        if self.socket:
            self.running = False
            self.socket.close()
            
            
#Listens and creates client_handler objects   
class server_connect:
    def __init__(self, port):
        self.port = port
        self.running= False
        self.listen_socket= None
        self.connections =[]
        
    def start(self):
        #listening socket - bound by listen()
        self.listen_socket = socket(AF_INET, SOCK_STREAM)
        self.listen_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.listen_socket.bind(('', self.port))
        self.listen_socket.listen(2)
        self.running = True
        
        print("Server listening...")
        
       
        accept_thread = Thread(target=self._accept_loop)
        accept_thread.daemon=True
        accept_thread.start()

      
    def _accept_loop(self):
         while self.running:
            #connected client socket - created by accept
            client_socket, address = self.listen_socket.accept()
            print(f"Accepted connection from {address}")
            
            conn= client_handler(client_socket, self.broadcast)
            self.connections.append(conn)
            conn.start()


    def broadcast(self, msg, sender=None):
        print(f"Broadcasting: {msg}")
        
        #send msg to all clients except sender
        for conn in self.connections:
            if conn != sender:
                conn.send(msg)
        
    def close(self):
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()
        for conn in self.connections:
            conn.close()
    
