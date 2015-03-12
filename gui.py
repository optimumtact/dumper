import Tkinter as tk
import traceback
import sys
import tkMessageBox
import gui_widgets as gw
from collections import namedtuple
from Queue import Queue, Empty
from threading import Thread
from dumper_engine import do_post_job

fill = tk.N+tk.S+tk.E+tk.W

#A lightweight data type for sending data to a job thread
Job = namedtuple('Job', ['board', 'thread', 'image_list', 'comment_list', 'username', 'password', 'starting_image', 'subject', 'debug'])

class Catcher: 
    '''
    Wraps tk calls to provide error logging
    '''
    def __init__(self, func, subst, widget):
        self.func = func 
        self.subst = subst
        self.widget = widget
    def __call__(self, *args):
        try:
            if self.subst:
                args = apply(self.subst, args)
            return apply(self.func, args)
        except SystemExit, msg:
            raise SystemExit, msg
        except:
            traceback.print_exc(file=open('dumper.log', 'a'))
            print(traceback.print_exc())
            tkMessageBox.showerror("Fatal exception", "Please send your dumper.log to the developer")
            sys.exit()

class App(tk.Frame):
    def __init__(self, parent, **options):
        tk.Frame.__init__(self, parent, **options)
        #QUEUE for comms
        self.output = Queue()
        
        self.tv = gw.ThreadView(self, text='Step 1: Select a board or thread', padx=5, pady=5)
        self.tv.grid(row=0, column = 0, sticky=fill)
        self.fv = gw.FolderView(self, root, text='Step 2: Add image files', padx=5, pady=5)
        self.fv.grid(row=1, column = 0, sticky = fill)
        self.dv = gw.DetailView(self, text='Step 3: Optional extras', padx=5, pady=5)
        self.dv.grid(row=0, column = 1, sticky = fill)
        #row 1, column 1 grows
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        #self.rowconfigure(2, weight=1) - took this out
        #create a frame to hold all our buttons
        bframe = tk.LabelFrame(self, text='Step 4: Damn the torpedos', padx=5, pady=5)
        bframe.grid(row=1, column=1, sticky=fill)
        #dump button
        bframe.columnconfigure(0, weight=1) # grow within the button frame
        self.dumpb = tk.Button(bframe, text='Fire', command=self.dump)
        self.dumpb.grid(row=0, column=0, sticky=fill)
        
        #TextFrame for our status output!
        tframe = tk.LabelFrame(self, text='Step 5: Look at the output!', padx = 5, pady = 5)
        #grow column 1 as wide as possible!
        tframe.columnconfigure(0, weight=1)
        #put the text output at the bottom of dumper
        tframe.grid(row=2, column=0, columnspan=2, sticky=fill)
        #scrollbar for our text fram
        scroll = tk.Scrollbar(tframe)
        
        scroll.grid(row=0, column=1, sticky=fill)
        self.console = tk.Text(tframe, yscrollcommand=scroll.set, height=6, state=tk.DISABLED)
        self.console.grid(row=0, column=0, sticky=fill)
        scroll.config(command=self.console.yview)
        

    def dump(self):
        '''
        Pull the data from each of the views then
        send this to the dumper engine in a seperate thread
        as a post job, finally schedule a check of the output
        thread in 1000 milliseconds
        '''
        board, thread = self.tv.get_results()
        images, comments = self.fv.get_image_list()
        username, password, subject = self.dv.get_details()
        if not (board and thread and len(images)):
           tkMessageBox.showwarning("Missing fields", "You must at minimum have a board and some images selected", master=self)
           return        
        
        if (not username) and password:
            tkMessageBox.showwarning("Unfilled Field", "It makes no sense to have a password but no username", master=self)
            return

        #new job
        #board id, thread id, list of file paths to images, list of comments to images,
        #username, passsword, num of starting image, subject
        job = Job(board, thread, images, comments, username, password, 0, subject, False)
        #start a new thread to do job
        thread = Thread(target=do_post_job, args=(job, self.output))
        thread.start()
        self.dumpb['state']=tk.DISABLED
        #print('process started')
        #schedule a check of the output queue
        self.after(1000, self.check_output)


    def check_output(self):
        '''
        Check for output from the output queue and display
        it in the status area, if the status type is 1 we halt
        as we are finished (or broken from errors) and
        unlock the gui for use.

        Reschedules itself to run every 1000 milliseconds
        '''

        self.console['state']=tk.NORMAL
        try:
            status = self.output.get(block=False)
            if(status.type!=0):
                #we are done, unlock the dump button
                self.dumpb['state']=tk.NORMAL
                self.console.insert(tk.END, "{0} {1}\n".format(status.name, status.description))
                if(status.type==3):
                    #something unexpected has happened
                    tkMessageBox.showerror("Unhandled exception", "An unhandled exception occurred in the dumper engine\n Please send oranges your dumper.log")
                
                self.console['state']=tk.DISABLED
                return
            
            #image done but dump continues
            self.console.insert(tk.END, "{0} {1}\n".format(status.name, status.description))

        except Empty:
            #nothing in queue
            pass
            
        self.console['state']=tk.DISABLED
        self.after(1000, self.check_output)
        
if __name__ == '__main__':
    root = tk.Tk()
    tk.CallWrapper = Catcher
    main = App(root)
    main.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
    
    
