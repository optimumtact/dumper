import Tkinter as tk
import ttk
import re
fill = tk.N+tk.S+tk.E+tk.W

class DetailView(tk.LabelFrame):
    '''
    Takes care of letting user enter details
    user:
    password:
    subject:
    '''

    def __init__(self, parent, **options):
        tk.LabelFrame.__init__(self, parent, **options)
        #we have 5 rows and 3 columns
        #for now the first two rows are empty 
        #username
        tk.Label(self, text='Username:').grid(row=2, column=0, sticky=fill)
        self.uname_entry = tk.StringVar() 
        tk.Entry(self, textvariable=self.uname_entry).grid(row=2, column=1, 
                 sticky=fill)
        
        #password
        tk.Label(self, text='Password:').grid(row=3, column=0, sticky=fill)
        self.pass_entry = tk.StringVar()
        tk.Entry(self, textvariable=self.pass_entry, show='*').grid(row=3,
                 column=1, sticky=fill)
        
        #email
        tk.Label(self, text='Subject:').grid(row=4, column=0, sticky=fill)
        self.subj_entry = tk.StringVar()
        tk.Entry(self, textvariable=self.subj_entry).grid(row=4, column=1, sticky=fill)

    
    def get_details(self):
        '''
        Return a tuple of all the details in the format
        (username, password, subject)
        '''
        return (self.uname_entry.get(), self.pass_entry.get(), self.subj_entry.get())

if __name__ == '__main__':
    root = tk.Tk()
    fv = DetailView(root, text='Step 3:Optional Extras', padx=5, pady=5, highlightbackground='black')
    fv.pack(fill=tk.BOTH, expand=True)
    root.mainloop()