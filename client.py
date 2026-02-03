from connection import client_connect
from gui import chat_gui

port = 5001
gui = chat_gui()

def handle_received(msg):
    gui.display(f"Other: {msg}")
    
    
client = client_connect('localhost', port, handle_received)
gui.connection = client
client.start()


gui.run()

