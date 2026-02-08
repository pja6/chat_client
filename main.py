import tkinter as tk
from tkinter import scrolledtext, messagebox
from socket import *
from threading import *
from networking import client_connect, server_connect

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
        self.secure_btn = tk.Button(self.gui_window, text="SECURE HANDSHAKE", command = self.start_handshake, fg="green")
        self.secure_btn.pack(pady=5)
        
        
        
        
        
    #TODO
        #self.disconnect_button = tk.Button(self.gui_window, text="DISCONNECT", command=self.disconnect)
        #self.disconnect_button.pack(pady=5)
        
    def connect_to_server(self):
       username = self.username_entry.get().strip()
       if not username:
           messagebox.showerror("Error", "Username can't be empty")
           return
       
       self.connection = client_connect('localhost', 5001, username, self.receive_msg)
       try:
           self.connection.start()
           self.connection.send(username)
           
           self.username_entry.config(state='disabled')
           self.connect_button.config(state='disabled')
           self.display(f"System: Connected as {username}")
        
       except Exception as e:
           messagebox.showerror("Connection Failed", f"Is server running?\n{e}")
    
    
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
        if target and msg:
            self.display(f"To {target}: {msg}")
            formatted_msg = f"{target}|{msg}"
            self.connection.send(formatted_msg)
            
            self.text_field.delete(0, tk.END)
            
    def receive_msg(self, msg):
        try:
            parts = msg.split('|')
            
            if len(parts) >= 2:
                sender = parts[0]
                
                #check if key exchange is happening
                if len(parts) >= 2 and parts[1] in ["DH_INIT", "DH_REQUEST", "DH_RESPONSE"]:
                    self.display(f"System: Security handshake update from {sender}...")
                    if parts[1] == "DH_REQUEST":
                        self.display(f"System: {sender} requesting secure connection, agree?")
                    return
                
                #TODO if encryption happens
                
                #system message
                if sender == "System":
                    self.display(f"*** {parts[1]} ***")
                else:
                    content = "|".join(parts[1:])
                    self.display(f"{sender}: {content}")
                    #self.display(f"{sender}: {'|'.join(parts[1:])}")
            else:
               self.display(f"Raw: {msg}")
        except Exception as e:
            self.display(f"Error parsing message: {msg}")
         
                
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