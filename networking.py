from socket import *
from threading import *
import encrypt
import security

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
    def __init__(self, host, port, username, on_msg_rcvd):
        super().__init__(on_msg_rcvd)
        self.host = host
        self.port = port
        self.username=username
        self.dh_waiting = False
        # sender:data
        self.dh_pending={}

        self.sec_mgr = security.Security_Manager(username)
        
  
    def secure_connect(self, target):
        if self.dh_waiting and self.dh_pending:
            # DH_Pub, RSA_n, RSA_e, Sig (indices 3, 4, 5, 6)
           
            data = self.dh_pending.pop(self.username)
            #unpack data
            response = self.sec_mgr.verify_respond(target, *data)
            if response: 
                self.send(response)
            self.dh_waiting=False
        else:
            packet = self.sec_mgr.create_dh_packet(target)
            self.send(packet)
        
    def _receive_loop(self):
        while self.running:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                parts = data.split("|")
                msg_type = None
                
                # Minimum parts: Sender | Target | Type | DH_Pub | n | e | Sig = 7 parts
                if len(parts) >= 6:
                    sender = parts[0]
                    msg_type = parts[1]
                
                    
                    if msg_type == "DH_INIT":
                    
                        self.dh_pending[sender] = parts[2:]
                        self.on_msg_rcvd(f"{sender}|DH_REQUEST")
                        self.dh_waiting=True
                        
                    

                        
                        """"
                      
                            """
                        
                    elif msg_type == "DH_RESPONSE":
                        print(f"[CLIENT] Received DH_RESPONSE from {sender}")
                        if self.sec_mgr.finalize_secret(sender, *parts[2:]):
                            print(f"[CLIENT] finalize_secret returned True!")
                            self.on_msg_rcvd(f"Secure Link with {sender} ready...")
                        else:
                            print(f"[CLIENT] finalize_secret returned False!")
                    
                    #just a normal message, no key exchange        
                    else:
                        self.on_msg_rcvd(data)
                
                #TODO elif msg_type == "SECURE_MSG" for encryption
                
                    #system messages e.g. Welcome to IM   
                else:
                    self.on_msg_rcvd(data)
                    
            except Exception as e:
                print(f"Receive Error: {e}")
                break
                        

            
    def start(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.running = True
        
        #receive in background thread
        
        receive_thread = Thread(target=self._receive_loop)
        receive_thread.daemon = True
        receive_thread.start()
      

    def close(self):
        print("Closing connection and clearing session keys...")
        self.running = False
        
        #wipe shared secrets from memory
        if hasattr(self, 'sec_mgr'):
            self.sec_mgr.shared_secrets.clear()
        
        #now shut down socket
        if self.socket:
            try:
                #clear username when logging out
                self.send("EXIT")
                self.socket.close()
            except:
                pass

# class represents a connection the server accepted
class client_handler(base_connection):
    def __init__(self, client_socket, on_msg_rcvd):
        super().__init__(on_msg_rcvd)
        self.socket = client_socket
        self.username = None
        
    def start(self):
        self.running = True
        
        receive_thread = Thread(target=self._receive_loop)
        receive_thread.daemon=True
        receive_thread.start()
    
    # overrides base class  
    def _receive_loop(self):
        while self.running:
            try:
                message = self.socket.recv(8192).decode('utf-8')
                if message == "" or message == "EXIT":
                    break

                if message:
                    # Pass sender
                    self.on_msg_rcvd(message, self)  
                """"
                else:
                break
                except Exception as e:
                print(f"Error receiving: {e}")
                self.running = False
                break
                """
            except:
                break

        self.running = False
        self.close()
   
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
        #username : client_ip
        self.clients ={}
        
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
            
            conn= client_handler(client_socket, self.route_message)
            conn.start()


    def route_message(self,msg, sender_conn):
        if sender_conn.username is None:
            if msg in self.clients:
                sender_conn.send("System|username taken")
                return

            print(f"[SERVER] Routing message from {sender_conn.username or 'UNKNOWN'}: {msg}")

            sender_conn.username = msg
            self.clients[msg] = sender_conn
            print(f"User logged in: {msg}")
            sender_conn.send("System|Welcome to IM")
            return
    
        try:
            parts = msg.split('|')
            target_user= parts[0]
            msg_type = parts[1] if len(parts) > 1 else None
            
            if msg_type in ["DH_INIT", "DH_RESPONSE"]:
            
                if target_user in self.clients:
                    target_conn = self.clients[target_user]
                    target_conn.send(msg)
                else:
                    sender_conn.send(f"System|User {target_user} not online.")
                return
            
            #then normal message routing
            content = msg.split('|', 1)[1]
            if target_user in self.clients:
                target_conn = self.clients[target_user]
                target_conn.send(f"{sender_conn.username}|{content}")
            else:
                sender_conn.send(f"System|User {target_user} not found.")
        except:
            sender_conn.send("System|Invalid format. Use: Recipient|Message")
        
    def close(self):
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()
        # was iterating over str before, now actual obj
        for conn in self.clients.values():
            conn.close()
    
