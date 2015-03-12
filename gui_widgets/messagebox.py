import Tkinter as tki # Tkinter -> tkinter in Python 3

def tbox(master):
    class TBOX(object):
        def __init__(self, info):
            self.msgbox = tki.Toplevel(master)
            label0 = tki.Label(self.msgbox, text=info)
            label0.pack()
            self.entry0 = tki.Entry(self.msgbox)
            self.entry0.pack()
            button0 = tki.Button(self.msgbox, text='OK',
                                    command=self.b0_action)
            button0.pack()

        def b0_action(self):
            master.username = self.entry0.get()
            self.msgbox.destroy()
    return TBOX