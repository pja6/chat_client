import tkinter as tk
from socket import *
from threading import *


class chat_gui:
    def __init__(self, connection=None):
        self. connection=connection
        self.gui_window = tk.Tk()
        self.gui_window.title("Chat")
        
        # disabled makes the window read only
        self.chat_display = tk.Text(self.gui_window, state="disabled", width=50, height=10)
        
        #pack is used to determine formatting, no param means handles automatically
        self.chat_display.pack()
        
        #entry is the text box to write in
        self.text_field = tk.Entry(self.gui_window)
        #adding it to the window, fill the width of the window
        self.text_field.pack(fill='x')
        
        self.username_label = tk.Label(self.gui_window, text="Username: ")
        self.username_label.pack()
        
        #TODO
        #input field for username
        #self.username_entry = tk.Entry(self.gui_window)
        #self.username_entry.pack()
        
        #self.connect_button = tk.Button(self.gui_window, text="CONNECT", command=self.connect_to_server)
        #self.connect_button.pack(pady=5)
        
        #self.disconnect_button = tk.Button(self.gui_window, text="DISCONNECT", command=self.disconnect)
        #self.disconnect_button.pack(pady=5)
        
        self.send_button = tk.Button(self.gui_window, text="SEND", command=self.send)
        self.send_button.pack()
        
        
    def send(self):
        msg = self.text_field.get().strip()
        if msg:
            self.display(f"You: {msg}")
            self.text_field.delete(0, tk.END)
            
            #TODO
            if self.connection:
                self.connection.send(msg)
                
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
    gui=chat_gui()
    gui.run()