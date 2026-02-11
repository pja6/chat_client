import tkinter as tk
from tkinter import scrolledtext, messagebox
from socket import *
from threading import *
from networking import client_connect, server_connect
import json

class chat_gui:
    def __init__(self, connection=None):
        self. connection=connection
        self.gui_window = tk.Tk()
        self.gui_window.title("Chat")
        
        frame_top = tk.Frame(self.gui_window)
        frame_top.pack(pady=5)
        
        tk.Label(frame_top, text= "username:").pack(side=tk.LEFT)
        #input field for username
        self.username_entry = tk.Entry(self.gui_window)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = tk.Button(self.gui_window, text="CONNECT", command=self.connect_to_server)
        self.connect_button.pack(side=tk.LEFT)
        
        # disabled makes the window read only
        self.chat_display = tk.Text(self.gui_window, state="disabled", width=50, height=10)
        
        #pack is used to determine formatting, no param means handles automatically
        self.chat_display.pack(padx=10, pady=5)
        
        #Choose recipient 
        tk.Label(self.gui_window, text="Send to (username):").pack()
        self.target_entry = tk.Entry(self.gui_window)
        self.target_entry.pack(fill='x', padx=10)
        
        #write message
        tk.Label(self.gui_window, text="Message:").pack()
        self.text_field = tk.Entry(self.gui_window)
        self.text_field.pack(fill='x', padx=10, pady=5)
        self.text_field.bind('<Return>', lambda event: self.send()) 
        
        #send it
        self.send_button = tk.Button(self.gui_window, text="SEND", command=self.send)
        self.send_button.pack(pady=5)
        
        #exchange it
        self.secure_btn = tk.Button(self.gui_window, text="START HANDSHAKE", command = self.decide_handshake, fg="green")
        self.secure_btn.pack(pady=5)
        
        
        
        
        
    #TODO
        #self.disconnect_button = tk.Button(self.gui_window, text="DISCONNECT", command=self.disconnect)
        #self.disconnect_button.pack(pady=5)

# =====================================  GUI FX ================================================
#   
    def connect_to_server(self):
       username = self.username_entry.get().strip()
       if not username:
           messagebox.showerror("Error", "Username can't be empty")
           return
       
       self.connection = client_connect('localhost', 5001, username, self.receive_msg)
       try:
           self.connection.start()           
           self.username_entry.config(state='disabled')
           self.connect_button.config(state='disabled')
           self.display(f"System: Connected as {username}")
        
       except Exception as e:
           messagebox.showerror("Connection Failed", f"Is server running?\n{e}")
    
    def decide_handshake(self):
        if self.connection.secure:
            self.connection.secure = False
            target = self.target_entry.get().strip()
            self.display(f"System: Secure Handshake with {target} terminated")
            print("[SYSTEM] Encrypted conversation terminated")
            self.receive_msg("SECURE_LINK_TERMINATED")
        else:
            self.start_handshake()
            
        
    def start_handshake(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter a target username first!")
            return
        if self.connection:
            self.display(f"System: Initiating Secure handshake with {target}...")
            self.connection.secure_connect(target)
        
    def send(self):
        target=self.target_entry.get().strip()
        msg = self.text_field.get().strip()
        if not self.connection:
            messagebox.showerror("Error", "Not connected")
            return
        if not target or not msg:
            return
        self.display(f"To {target}: {msg}")
        self.connection.send_message(target, msg)
        #stays out of the if/else block
        self.text_field.delete(0, tk.END)      
            
    def receive_msg(self, msg_data):
        try:
            
            if isinstance(msg_data, dict):
                msg_type = msg_data.get("msg_type")
                sender = msg_data.get("sender", "System")
                
                if msg_type == "DH_RESPONSE":
                    print("[SYSTEM] New DH Exchange beginning")
                    
                elif msg_type == "DH_REQUEST":
                    self.display(f"System: Security handshake update from {sender}...")

                    self.display(f"System: {sender} requesting secure connection, agree?")
                
                elif msg_type == "SECURE_LINK_ESTABLISHED":
                    self.display(f" System: secure link with {sender} established")  
                    self.secure_btn.config(fg="green", text = "END HANDSHAKE")  
                                
                elif msg_type == "TERMINATE_LINK":
                    self.display(f" System: secure link with {sender} terminated")
                    self.secure_btn.config(fg="green", text = "START HANDSHAKE")              
  
                elif msg_type == "MESSAGE":
                    content = msg_data.get("content", "")
                    encrypted = msg_data.get("encrypted", False)
                    prefix = "SEC" if encrypted else ""
                    self.display(f"{prefix}{sender}: {content}")
                
                #system message
                elif msg_type == "SYSTEM":
                    content = msg_data.get("content", "")
                    self.display(f"*** {content} ***")
            
                else:
                    self.display(f"Unknown message type: {msg_type}")
        except Exception as e:
            self.display(f"Error parsing message: {e}")
            import traceback
            traceback.print_exc()
         
                
    def display(self, msg):
        #need to schedule display
        self.gui_window.after(0, self._do_display, msg)
        
    def _do_display(self, msg):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, msg +"\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)
        
    def run(self):
        self.gui_window.mainloop()
        

        
if __name__ == "__main__":
    mode = input("Run as (s)erver or (c)lient?").lower()
    if mode == 's':
        s = server_connect(5001)
        s.start()
        while True: pass
    else:
        
        gui=chat_gui()
        gui.run()