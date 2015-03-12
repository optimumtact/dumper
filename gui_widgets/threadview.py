import Tkinter as tk
import ttk
import re

fill = tk.N+tk.S+tk.E+tk.W
    
class ThreadView(tk.LabelFrame):
    '''
    Display a dropdown box for the boards
    or let the user choose to enter a thread
    url
    '''
    def __init__(self, parent, **options):
        '''
        Set up ThreadView and layout components
        '''
        tk.LabelFrame.__init__(self, parent, **options)
        #3 rows 3 columns
        #board chooser
        tk.Label(self, text='Please choose the board').grid(row=0, column = 0, sticky=fill)
        
        board_list = ['1', 'diy', 'e', 'm', 'mu', 's', 't', 'to', 'tv', 'w', 'a',
                'ac', 'b', 'c', 'chat', 'd', 'f', 'g', 'hc', 'hd', 'itn',
                'k', 'mil', 'pa', 'r', 'r9k', 'so', 'u', 'v', 'x', 'gif']
        self.combo_var = tk.StringVar()
        self.combo=ttk.Combobox(self, values=board_list, state='readonly', 
                     textvariable = self.combo_var)
        self.combo.grid(row=0, column = 2, sticky=fill)
        
        #thread url
        tk.Label(self, text='OR').grid(row=1, column=0, columnspan=3, sticky=fill)
        tk.Label(self, text='Enter a thread url').grid(row=2, column=0, sticky=fill)
        self.thread_toggle = tk.IntVar()
        tk.Checkbutton(self, var=self.thread_toggle, 
                       command=self.toggle_threads).grid(row=2, column=1)
        self.url = tk.StringVar()
        self.thread_entry = tk.Entry(self, textvariable = self.url)
        self.thread_entry.config(state=tk.DISABLED)
        self.thread_entry.grid(row=2, column=2, sticky=fill)
        
        #regex for parsing all the possible urls we could get
        #use regex = 2 problems, yadeyadeya
        self.re_url = re.compile(r'''(?:http://)? #some browsers like to remove this because that is "User friendly"
                     (?:www.|direct.|beta.)? #A few different top levels
                     (?:example(?:.com|.net|.org)|example2.org|short.in) #all tld permutations
                     /(?P<Board>\w+) #board (any number of [A-Za-z0-9_])
                     /res/
                     (?P<Thread>\d+) #thread number (any number of [0-9])
                     (?:\#\d+)? #url may have a #post_id ending''', re.X)
    def get_results(self):
        '''
        Get the board and thread id user has selected
        '''
        if self.thread_toggle.get() == 1:
            #url entered
            return self.parse_url(self.url.get())
        
        else:
            #board selected, new thread so id = 0
            return (self.combo_var.get(), '0')
            
    def toggle_threads(self):
        '''
        Toggle between url entry disabled or board chooser disabled
        '''
        if self.thread_toggle.get() == 1:
            self.thread_entry.config(state='normal')
            self.combo.config(state=tk.DISABLED)
        else:
            self.thread_entry.config(state=tk.DISABLED)
            self.combo.config(state='readonly')
            
            
    def parse_url(self, url):
        '''
        parse the url and pull out the board and thread_id
        '''
        if not url:
            #blank url, return blank board and thread
            return ('', '')
        result = self.re_url.match(url)
        #if we got a result, and we have both expected matches present
        if result and result.group('Board') and result.group('Thread'):
            return (result.group('Board'), result.group('Thread'))
            
        else: #error, return blank board and thread
            return ('', '')

if __name__ == '__main__':
    root = tk.Tk()
    tv = ThreadView(root, text='Step 1:Choose a board or thread', padx=5, pady=5)
    tv.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
