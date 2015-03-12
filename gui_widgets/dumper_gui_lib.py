#Python 2.7.3

'''
bunch of useful and nice lib gui widgets that aren't in
the default distro of python
'''
from Tkinter import *
from ttk import *
import os
from PIL import Image, ImageTk

class ToggledFrame(Frame):
    def __init__(self, parent, text='', callback=None, **options):
        Frame.__init__(self, parent, **options)
        self.callback=callback
        self.show=0
        self.titleFrame=Frame(self)
        self.titleFrame.pack(fill=X, expand=1)
        Label(self.titleFrame, text=text).pack(side=LEFT, fill=X, expand=1)
        self.toggleButton=Button(self.titleFrame, width=2,text='+', command=self.toggle, style='Toolbutton')
        self.toggleButton.pack(side=LEFT)
        self.hidden_area=Frame(self)
        
    def toggle(self):
        if not bool(self.show):
            self.show = 1
            self.hidden_area.pack(fill=X, expand=1)
            self.toggleButton.configure(text='-')
        else:
            self.show = 0
            self.hidden_area.forget()
            self.toggleButton.configure(text='+')
        if self.callback:
            self.callback(self.show)
        
#Example
if __name__ == '__main__':
    app=Tk()
    t=ToggledFrame(app, text='Rotate', relief=RAISED,borderwidth=1)
    t.pack(fill=X, expand=1, pady=2, padx=2, anchor=N)
    Label(t.hidden_area,text='Rotation [deg]:').pack(side=LEFT, fill=X, expand=1)
    Entry(t.hidden_area).pack(side=LEFT)

    t2=ToggledFrame(app, text='Resize', relief=RAISED,borderwidth=1)
    t2.pack(fill=X, expand=1, pady=2, padx=2,anchor=N)
    for i in range(10):
        Label(t2.hidden_area, text='Test'+str(i)).pack()

    t3=ToggledFrame(app, text='Fooo', relief=RAISED,borderwidth=1)
    t3.pack(fill=X, expand=1, pady=2, padx=2,anchor=N)
    for i in range(10):
        Label(t3.hidden_area, text='Bar'+str(i)).pack()

    mainloop()

class Dialog(Toplevel):
    fill = N+S+E+W #useful define
    def __init__(self, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("&lt;Return>", self.ok)
        self.bind("&lt;Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override

        
class CommentDialog(Dialog):
    '''
    Custom dialog that takes a list of image paths and a list of results
    It then allows the user to enter a comment for each image, advancing via
    enter each time, inserting each comment into the results list after each
    enter press
    '''
    
    #size of image thumbnail
    size = (400, 400)
    def __init__(self, parent, image_list, results, **options):
        #NB: this has to be above the Dialog init call, as dialog init
        #will call body, which uses self.image_list
        self.image_list = image_list
        self.results = results
        Dialog.__init__(self, parent, **options)
        
    
    def body(self, master):
        self.index = 0
        self.max_images = len(self.image_list)
        #open first image
        self.curr_image = Image.open(self.image_list[self.index])
        #we only really want a thumbnail
        self.curr_image.thumbnail(self.size, Image.ANTIALIAS)
        #turn into tk std image
        self.curr_image = ImageTk.PhotoImage(image=self.curr_image)
        
        self.label = Label(master, image=self.curr_image)
        self.comment = StringVar()
        c_entry = Entry(master, textvariable=self.comment)
        Label(master, 
        text="Enter the comment for an image\n and press enter to advance to\n the next image, or leave it blank\n for the default comment",
        ).grid(row=0, column=1, rowspan=2, sticky=N+E)
        #layout the label first, so the image defines the box size
        self.label.grid(row=0, column=0, sticky=self.fill)
        c_entry.grid(row=1, column=0, columnspan=2, sticky=self.fill)
        #Bind the enter command to our method that will advance to the next
        #image and record the saved image
        c_entry.bind('<Return>', self.next)
        return c_entry
    
    def next(self, event):
        #save result of comment box
        result = self.comment.get()
        if result == '':
            self.results.append('Default comment')
        else:
            self.results.append(result)
            
        self.comment.set('')
        
        if self.index+1 >= self.max_images:
            #reached end of images, just call apply to make the dialog box close
            self.apply()
            
        else:
            #load next image in line and update our label
            self.index += 1
            self.curr_image = Image.open(self.image_list[self.index])
            self.curr_image.thumbnail(self.size, Image.ANTIALIAS)
            self.curr_image=ImageTk.PhotoImage(image=self.curr_image)
            self.label.config(image=self.curr_image)
        
    def buttonbox(self):
        pass
    
    def apply(self):
        self.cancel()