import os
import sys
from StringIO import StringIO
from random import randint
import gzip
import zlib
import urllib
import urllib2
from urllib2 import HTTPError, URLError
import mimetypes
import json
import time
import base64
import tkMessageBox
import Tkinter
from collections import namedtuple
import logging

if __name__ == '__main__':
    print("please run gui.py, not newdumper.py")
    #show a pop up for those who don't run out of a console !
    root = Tkinter.Tk()
    #hide the root window as we don't use it
    root.withdraw()
    tkMessageBox.showwarning("Wrong file", "Please run the gui.py file", master=root)
    sys.exit(0)

# create logger
lgr = logging.getLogger('Dumper')
lgr.setLevel(logging.DEBUG)
# add a file handler, XXX: now we are using 'a' look at rotating dump files
fh = logging.FileHandler('dumper.log', mode = 'a')
#starts out at info, can be set to debug if that setting is passed from gui.py
fh.setLevel(logging.DEBUG)

#add a handler that logs info and above to console
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

# create a formatter and set the formatter for the handlers
frmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(frmt)
ch.setFormatter(frmt)

# add the Handlers to the logger
lgr.addHandler(fh)
lgr.addHandler(ch)

#A lightweight data object for sending output to the GUI thread
#a quick note on types, 0 is normal and 1 indicates that the GUI should be unlocked
Status = namedtuple('Status', ['name', 'description', 'type'])

def do_post_job(job, output):
    '''
    Passed as a callable to a thread instance in python
    So you don't hang your GUI
    Output should be a python Queue object or something
    that implements the .put method and is thread safe
    '''
    try:
        if job.debug:
            fh.setLevel(logging.DEBUG)
            ch.setLevel(logging.DEBUG)
        total = len(job.image_list)
        thread_id = job.thread
        index = job.starting_image
        lgr.info("Starting new post job, num images ={0}, thread_id={1}, starting image={2}".format(total, thread_id, index))
        #if there is no job.thread id we have to make a new thread and
        #record the ID
        if job.thread == '0':
            try:
                if job.comment_list[index]!= 'Default comment':
                    comment = job.comment_list[index]
                else:
                    comment = 'Image '+str(index+1)+' of '+str(total)
                
                result, data = post(job.board, thread_id, job.image_list[index], job.username, job.password, comment, job.subject, output)
                success = result["success"]
                job = job._replace(thread=str(success["id"]))
                lgr.info("Made a new thread -> {0}".format(success["link"]))
                index+=1

            except (PostError, FatalPostError) as e:
                #no matter what error we get, we have to return as there is no thread for us to dump too!
                output.put(Status('Thread creation failed', str(e), 1))
                lgr.error("Thread creation failed, reason:{0}".format(str(e)))
                #note the 1 in the status type, unlocking the GUI interface
                return

            output.put(Status("Image 1 of {0}".format(index), 'Successful, thread is {0}'.format(success["link"]), 0))
            lgr.info("Image 1 of {0} sucessful".format(total))
            time.sleep(5)

        #Go through and post every image in the directory
        #starting from index and skipping ones that throw an post error
        #there are also fatal post errors which will end the post thread
        #these are things like server errors, bad connection and so forth
        for item in job.image_list[index:]:
            log =  'Image '+str(index+1)+' of '+str(total)
            
            if job.comment_list[index]!= 'Default comment':
                comment = job.comment_list[index]
            else:
                comment = 'Image '+str(index+1)+' of '+str(total)
                
            try:
                post(job.board, job.thread, job.image_list[index], job.username, job.password, comment, '', output)

            except PostError as e:
                output.put(Status(log, "Error:{0}".format(e), 0))
                lgr.warn("Posting error: {0}".format(str(e)))
                index+=1
                time.sleep(5)
                continue

            except FatalPostError as e:
                output.put(Status('Fatal Error', str(e), 1))
                lgr.error("Fatal posting error: {0}".format(str(e)))
                return
                
            output.put(Status(log, 'Success', 0))
            lgr.info("{0} sucessful".format(log))
            index+=1
            time.sleep(5)

        #note the type again - unlocking the GUI interface
        output.put(Status('Dump fully completed', '', 1))
        lgr.info("Dump completed")
    
    except SystemExit, msg:
            raise SystemExit, msg
                
    except Exception as e:
        lgr.exception('Unhandled exception {0}'.format(str(e)))
        output.put(Status('Unhandled Exception', "Please retry at some point", 3))
       

def post(board, thread, image, user, password, comment, subject, output):
    '''
    Fields we need, most left empty
    ('parent', thread),
    ('user', username),
    ('pass', password), -this doesn't seem to work
    ('email', email), -empty, has to be there and empty because coder
    ('subject', subject), -empty, can be set
    ('message', comment), -normally image count
    ('asdfasdf', 'hello') - this is the secret api field that allows dumping without rate limits (e.t.c)
    ('file64', file encoded in base 64) - this is the field that holds the file data enc in base64, we do not do it this way
    as it's a hack to get around some js restrictions about uploading local files
    ('file', file as utf-8 binary string) - this is the field we use
         
    '''

    #first thing I ever do is turn everything passed in into a utf-8 string, just in case
    #because some Tk widgets (GUI) return ascii and that gave me a few hours of debugging stress
    lgr.debug("Encoding fields into utf-8 strings")
    board = board.encode('utf-8')
    thread = thread.encode('utf-8')
    image = image.encode('utf-8')
    comment = comment.encode('utf-8')
    #get a tuple containing filename, base64 encoded file string
    filename, b64file = get_filedata(image)

    json_fields = {'parent' : thread,
              'user' : user,
              'pass': password,
              'email': '',
              'subject': subject,
              'message': comment,
              'asdfasdf': 'hello',
              'file64': b64file,
              'filena': filename,
              }
    
    body = {'json' : json.dumps(json_fields)}

    #EXPERT HEADER CONSTRUCTION
    headers = dict()
    headers['User-Agent'] = 'dumper'
    #we only accept json, give us anything else and we'll be sad
    headers['Accept'] = 'application/json'
    #english language only
    headers['Accept-Language'] = 'en'
    #gzip + deflated responses only - currently 1eden doesn't compress anything
    headers['Accept-Encoding'] = 'gzip,deflate'
    #all charset in utf-8
    headers['Accept-Charset'] = 'utf-8'
    headers['Keep-Alive'] = '300'
    headers['Connection'] = 'keep-alive'
    #headers['Content-Type'] = content_type
    #headers['Content-Length'] = str(len(body))
	
    header_list = list()
    for header in headers:
        header_list.append(str(header) + str(headers[header]))
    lgr.debug("Header are {0}".format(", ".join(header_list)))
    
    #build url
    url = "http://example.com/api/?formid=NEWPOST&parent={0}&board={1}".format(thread, board)
    
    #make the request
    lgr.debug('Making request to {0}'.format(url))
    try:
        r = urllib2.Request(url, urllib.urlencode(body), headers)
        res=urllib2.urlopen(r)

    except HTTPError as e:
        if e.code == 413:
            #too large for server, move to next image
            raise PostError('413, request too large, size:{0} bytes - ask to increase size limits for the board'.format(headers['Content-Length']))
        else:
            raise FatalPostError(str(e.code)+' Http Error')

    except URLError as e:
        raise FatalPostError('Server Unreachable, reason:'+e.reason)
    
    
    #we may need to reinflate the response it if was compressed
    lgr.debug("Decompressing response")
    data=decompress_response(res)

    try:
        data = json.loads(data)
        #lgr.debug("Json Response:{0}".format(data))

    except ValueError as e:
        raise FatalPostError('Bad JSON response:'+ str(e))

    post = data["post"]
    if 'errors' in post:
        errors = post["errors"]
        str_errors = []
        for error in errors:
            str_errors.append("{0}:{1}".format(error["code"], error["message"]))
        raise PostError(", ".join(str_errors))
        
    return post, data

def decompress_response(response):
    '''
    Checks the responses content-encoding and attempts to
    decode it, currently supports only gzip and deflate so
    make sure your headers are set to accept only that
    '''
    data=None
    enc = response.info().get('Content-Encoding')
    if not enc:
        lgr.debug("No content encoding specified")
    else:
        lgr.debug("Content-Encoding was:{0}".format(enc))
        
    if enc == 'gzip' :
        #print 'gzip'
        buf = StringIO( response.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()

    elif enc == 'deflate' :
        #print 'deflate'
        data = zlib.decompress(data)

    elif not enc:
        #print 'none, default?'
        data = response.read()
        

    else:
        raise FatalPostError('Unknown content-encoding:'+response.info().get('Content-Encoding'))
    
    lgr.debug("Uncompressed response")
    lgr.debug(data)
    return data

def get_filedata(filepath, ulname = None):
    '''
    Given the filepath go and read in the file at that location
    returning a tuple containing('file', filename, filepath)
    '''
    if filepath:
        #ulname is the actual filename of the item
        if ulname == None:
            ulname = os.path.basename(filepath)
        #loads an entire file as a byte string
        #todo catch errors and log!
        lgr.debug('Reading file path:{0}, filename:{1}'.format(filepath, ulname))
        f = file(filepath, 'rb')
        data = f.read()
        f.close()
        return (ulname, base64.b64encode(data))
    else:
        #We couldn't load a file, raise a fatal error
        raise FatalPostError('File not found:'+filepath)

class FatalPostError(Exception):
    pass

class PostError(Exception):
    pass
