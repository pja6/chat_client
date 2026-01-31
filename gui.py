#Paul Aguilar - Lab4 GUI
from tkinter import *


def GUI():
    
    #tk object
    gui = Tk()
    
    #window title
    gui.title("Chat")
    
    #window size
    gui.geometry("380x420")
    
    
    chatlog = Text(gui, bg='white', width='50', height='8')
    chatlog.config(state=DISABLED) 
    
    #button
    
    sendbutton= Button(gui, bg='white', fg='grey', text='Send', width=10, height= 8)
    
    #text field
    
    textbox = Text(gui, bg='white', width=30, height= 8)
    
    
    chatlog.place(x=6, y=6, )
    
    #program loop, keeps window open
    gui.mainloop()
    
    
def main():
    
    GUI()
    
    
if __name__ == '__main__':
    main()


