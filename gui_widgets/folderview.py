
import Tkinter as tk
import tkMessageBox
import ttk
import tkFileDialog
import os
from dumper_gui_lib import CommentDialog

fill = tk.N+tk.S+tk.E+tk.W

            
class FolderView(tk.LabelFrame):
    '''
    Frame that contains a treeview over the files you are dumping
    and buttons to add/remove from the treeview
    '''
        
    def __init__(self, parent, root,debug=False, **options):
        '''
        Set up the folderview with the given parent
        Notice the extra parameter root - this should be the 
        original tk.Tk() instance, this is related to a bug in python
        see the choose_directory method for more explanation
        '''
        tk.LabelFrame.__init__(self, parent, **options)
        
        self.root = root
        #set up two scrollbars for our treeview
        xscroll = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        yscroll = tk.Scrollbar(self, orient=tk.VERTICAL)
        xscroll.grid(row=1, column=0, columnspan=2, sticky=fill)
        yscroll.grid(row=0, column=1, sticky=fill)
        
        #set up a treeview
        self.tree = ttk.Treeview(self, columns=('filename', 'fullpath', 'comment'), 
               displaycolumns=('filename', 'comment'), selectmode='extended',
               xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column =0, sticky=fill)
        #icon column shouldn't resize or be too big man
        self.tree.column('#0', stretch=False, width=20)
        #make the other visible ones a reasonable size
        self.tree.column('filename', stretch=True, width=300, minwidth=300)
        self.tree.column('comment', stretch=True, width=300, minwidth=300)
        #set up treeview headings
        self.tree.heading('filename', text='Filename')
        self.tree.heading('comment', text='Comment')
        
        #register callbacks for the scrollbars
        xscroll.config(command=self.tree.xview)
        yscroll.config(command=self.tree.yview)
        
        #make the treeview row and col expand
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight=1)
        
        #frame for our buttons!
        bframe = tk.Frame(self)
        bframe.grid(row=0, column = 2, rowspan=2, sticky=fill)
        
        #add some buttons for adding/removing folders
        addb = tk.Button(bframe, text = 'Add files', command=self.choose_directory)
        removeb = tk.Button(bframe, text='Remove folder/file', command=self.remove_selection)
        addb.grid(row = 0, column = 0, sticky=fill)
        removeb.grid(row=1, column=0, sticky=fill)
        
        #button for customising comments
        commentb = tk.Button(bframe, text='Edit comments', command=self.add_comments)
        commentb.grid(row=2, column=0, sticky=fill)
        
        #if debug specified, we add on a debug button that does dangerous
        #debugging things
        if debug:
            printb = tk.Button(bframe, text='Print selection', command=self.print_selection)
            printb.grid(row=3, column=0, sticky=fill)
            printa = tk.Button(bframe, text='Print image paths', command=self.print_paths)
            printa.grid(row=4, column=0, sticky=fill)
        
        self.allfiles=('*.gif', '*.png', '*.jpg', '*.swf', '*.bmp')
        self.filetypes = [('gif', '*.gif'), ('png', '*.png'), 
                          ('jpg', '*.jpg'), ('bmp', '*.bmp'), 
                          ('swf', '*.swf'), ('Images', self.allfiles)]

        #dictionary of id to full image paths
        #for non top level items
        self.images = {}
        #dictionary of toplevel paths to ids
        self.paths = {}
        self.id_to_path = {}
        #count of images
        self.num_images = 0
        
    def print_selection(self):
        '''
        print the names of whatever items
        treeview thinks are selected - this may differ from reality
        if there are bugs
        '''
        
        name_list = []
        for item in self.tree.selection():
            name_list.append(self.tree.set(item)['filename'])
            
        print('What treeview thinks is selected\nIf this differs from reality, there is a bug')
        for item in name_list:
            print(item)
    
    def print_paths(self):
        print('Printing list of full paths to the images treeview thinks exist')
        for item in self.get_image_list():
            print(item)
    

    def add_comments(self):
        '''
        Pop up a dialog allowing the user to add
        comments for each one of his selected images
        '''
        paths = self.get_selected_image_paths()
        results = []
        if not len(paths) <= 0:
           c = CommentDialog(self, paths, results, title="Enter Comments")
        
        else:
            tkMessageBox.showwarning("Error", "Please select some images first", master=self)
        
        #comments are now stored in results, we need to assign them to their files
        i = 0
        for item in self.tree.selection():
            #ignore items at top level
            if item in self.tree.get_children():
                continue
            else:
                self.tree.set(item, column='comment', value = results[i])
                i+=1
                
    def remove_selection(self):
        '''
        Remove the selected items from the treeview
        Notice how it updates the internal data structures
        to make sure dupe checking works correctly
        '''
        items = self.tree.selection()
        for item in items:
            #if it was a toplevel path
            #we need to update our internal data structures
            if item in self.id_to_path:
                del(self.paths[self.id_to_path[item]])
                del(self.id_to_path[item])
                #now remove all it's children!
                child_items = self.tree.get_children(item)
                for citem in child_items:
                    del(self.images[citem])
                
            else:
                # if it wasn't a top level item
                #remove it from the images dict
                if item in self.images:
                    del(self.images[item])
                
        self.tree.delete(*self.tree.selection())
        
    def choose_directory(self):
        '''
        Pop up a box asking the user to choose a set of files
        that will be displayed in the treeview, takes care of
        eliminating duplicates and creating appropriate toplevel
        labels for each set of files to exist under
        '''       
        image_list = tkFileDialog.askopenfilenames(filetypes=self.filetypes)
        #BUG in python http://bugs.python.org/issue5712
        #tkFileDialog returns a unicode tk list, instead of a tuple of 
        #filenames like you would expect
        if isinstance(image_list, unicode):
            image_list = self.root.tk.splitlist(image_list)
        
        if len(image_list) <= 0:
            return
            
        path = os.path.dirname(image_list[0])
        #check if the top level path exists already
        if path in self.paths:
            id = self.paths[path]

        #otherwise create a new toplevel
        else:
            id = self.tree.insert('', 'end', values=(path, path, 'Top Level folder'))
            self.paths[path] = id
            self.id_to_path[id] = path
        
        dupes = 0 #count of duplicate files
        for image in image_list:
            #check for dupes
            if image in self.images.values():
                dupes += 1
                continue
            
            self.num_images+=1
            iid = self.tree.insert(id, 'end', 
                  values=(os.path.basename(image), image,
                  'Default comment'))
            self.images[iid] = image
    
    def get_image_list(self):
        '''
        return a list of full paths to all the images
        that the user has currently added to the treeview
        '''
        images = []
        comments = []
        # we build the list so it is in order
        for folder in self.tree.get_children():
            for file in self.tree.get_children(folder):
                images.append(self.tree.set(file)['fullpath'])
                comments.append(self.tree.set(file)['comment'])
        return images, comments
        
    def get_selected_image_paths(self):
        '''
        Return a list of image paths for the currently selected images
        '''
        paths = []
        items = self.tree.selection()
        for item in items:
            #ignore items at top level
            if item in self.tree.get_children():
                continue
            else:
                paths.append(self.tree.set(item)['fullpath'])
        
        return paths
        
if __name__ == '__main__':
    root = tk.Tk()
    fv = FolderView(root, root, debug=True, text='Step 2: Add image files', padx=5, pady=5)
    fv.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
    

