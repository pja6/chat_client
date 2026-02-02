import tkinter as tk
from socket import *
from threading import *


class chat_gui:
    def __init__(self, connection=None):
        self. connection=connection
        self.gui_window = tk.TK()
        self.gui_window.title("Chat")
        
        # disabled makes the window read only
        self.chat_display = tk.Text(self.gui_window, state="disabled", height=10)
        
        #pack is used to determine formatting, no param means handles automatically
        self.chat_display.pack()
        
        #entry is the text box to write in
        self.text_field = tk.Entry(self.gui_window)
        #adding it to the window, fill the width of the window
        self.text_field.pack(fill='x')
        
        self.send_button = tk.Button(self.gui_window, text="SEND", command=self.send)
        self.send_button.pack()
        
        
        