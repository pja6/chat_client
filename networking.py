from socket import *
from threading import *
import security
import json

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
        self.secure = False
        # sender:data
        self.dh_pending={}

        self.sec_mgr = security.Security_Manager(username)
        
  
    def secure_connect(self, target):
        if self.dh_waiting and target in self.dh_pending:
            # DH_Pub, RSA_n, RSA_e, Sig (indices 3, 4, 5, 6)
           
            packet_data = self.dh_pending.pop(target)
            #unpack data
            response = self.sec_mgr.verify_respond(packet_data)
            #pending init to respond to
            if response: 
                self.send(response)
            self.dh_waiting=False
            #starting exchange
        else:
            packet = self.sec_mgr.create_dh_packet(target)
            self.send(packet)
        
    def _receive_loop(self):
        while self.running:
            try:
                data = self.socket.recv(8192).decode('utf-8')
                if not data:
                    break
                
                
                packet = json.loads(data)
                
                msg_type = packet["msg_type"]
                sender = packet.get("sender", "System")
                
                if msg_type == "DH_INIT":
                    print(f"[CLIENT] Recieved DH_INIT from {sender}")
                    self.dh_pending[sender] = packet
                    
                    self.on_msg_rcvd({
                        "msg_type": "DH_REQUEST",
                        "sender": sender
                    })
                    self.dh_waiting=True
                #need some confirmation to send back that it's established        
                        
                elif msg_type == "DH_RESPONSE":
                    print(f"[CLIENT] Received DH_RESPONSE from {sender}")
                    if self.sec_mgr.finalize_secret(packet):
                        print(f"[CLIENT] finalize_secret returned True!")
                        confirmation_packet={
                            "msg_type": "DH_CONFIRM",
                            "sender": self.username,
                            "target": sender 
                        }
                        self.send(json.dumps(confirmation_packet))

                        self.on_msg_rcvd({
                            "msg_type": "SECURE_LINK_ESTABLISHED",
                            "sender": sender
                        })
                        self.secure=True
                    else:
                        print(f"[CLIENT] finalize_secret returned False!")
                
                elif msg_type == "DH_CONFIRM":
                    self.on_msg_rcvd({
                            "msg_type": "SECURE_LINK_ESTABLISHED",
                            "sender": sender
                        })
                    self.secure=True
                
                elif msg_type == "SECURE_MSG":
                    if self.secure:
                        
                        return
                
                #just a normal message, no key exchange        

                elif msg_type == "MESSAGE":
                    self.on_msg_rcvd({
                        "msg_type": "MESSAGE",
                        "sender": sender,
                        "content": packet["content"],
                        "encrypted": False
                    })
                
                elif msg_type == "SYSTEM":
                    self.on_msg_rcvd({
                        "msg_type": "SYSTEM",
                        "content": packet["content"]
                    })
                
                
                #system messages e.g. Welcome to IM   
                else:
                    print(f"[CLIENT] Unknown message type: {msg_type}")
                
            except json.JSONDecodeError as e:
                print(f"[CLIENT] Failed to parse JSON: {e}")
                print(f"[CLIENT] Raw data: {data}")
            except Exception as e:
                print(f"[CLIENT] Receive Error: {e}")
                break
                        

            
    def start(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.running = True
        
        login_packet = {
            "msg_type": "LOGIN",
            "username": self.username
        }
        self.send(json.dumps(login_packet))
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
        try:
            packet = json.loads(msg)
            sender_name = getattr(sender_conn, "username", "UNKNOWN")
            print(f"[SERVER] Routing message from {sender_name}: {json.dumps(packet)}")
        except json.JSONDecodeError:
            sender_conn.send(json.dumps({
                "msg_type": "SYSTEM",
                "content": "Invalid message format (expected JSON)"
            }))
            return
        
        if sender_conn.username is None:
            if packet.get("msg_type") != "LOGIN":
                sender_conn.send(json.dumps({
                    "msg_type": "SYSTEM",
                    "content": "Please LOGIN first"
                }))
                return
            username = packet.get("username")
            if not username:
                sender_conn(json.dumps({
                    "msg_type": "SYSTEM",
                    "content": "LOGIN packet missing username"
                }))
                return
            if username in self.clients:
                error_msg = {
                "msg_type": "SYSTEM",
                    "content": "Username taken"
                }
                sender_conn.send(json.dumps(error_msg))
                return

            print(f"[SERVER] Routing message from {sender_conn.username or 'UNKNOWN'}: {msg}")

            sender_conn.username = username
            self.clients[username] = sender_conn
            print(f"User logged in: {username}")
            
            welcome_msg = {
                "msg_type": "SYSTEM",
                "content": "Welcome to Messenger"
            }
            sender_conn.send(json.dumps(welcome_msg))
            return
    
        try:
            packet = json.loads(msg)
            target_user = packet.get("target")
            msg_type = packet.get("msg_type")
            
            if not target_user:
                error_msg = {
                    "msg_type": "SYSTEM",
                    "content": "Message missing target"
                }
                sender_conn.send(json.dumps(error_msg))
                return
            
            #route ALL message types to user - json now parses type
            if target_user in self.clients:
                
                target_conn = self.clients[target_user]
                target_conn.send(msg)
            else:
                sender_conn.send(json.dumps({
                    "msg_type": "SYSTEM",
                    "content": f"USER {target_user} not online"
                }))
                return

        except json.JSONDecodeError:
            sender_conn.send(json.dumps({
                "msg_type": "SYSTEM",
                "content": "Invalid message format (expected JSON)"
            }))
        
    def close(self):
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()
        # was iterating over str before, now actual obj
        for conn in self.clients.values():
            conn.close()
    
