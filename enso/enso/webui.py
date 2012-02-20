from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading, Queue, cgi, urllib, re, os, random, string
import enso.messages
from enso.contrib.scriptotron import cmdretriever

class myhandler(BaseHTTPRequestHandler):
  def __init__(self, request, client_address, server, queue, nonce_dict):
    self.queue = queue
    self.nonce_dict = nonce_dict
    BaseHTTPRequestHandler.__init__(self, request, client_address, server)

  def get_random_nonce(self):
    return ''.join([random.choice(string.lowercase) for x in range(10)])
  
  def get_webui_file(self, fn):
    path = os.path.join(os.path.split(__file__)[0], "webui", fn)
    fp = open(path)
    data = fp.read()
    fp.close()
    return data

  def do_GET(self):
    if self.path == "/install.js":
      js = self.get_webui_file("install.js")
      self.send_response(200)
      self.send_header("Content-Type", "text/javascript")
      self.end_headers()
      self.wfile.write(js)
    else:
      self.send_response(404)
      self.end_headers()
      self.wfile.write("404 Not Found")
      

  def do_POST(self):
    form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
    url = form.getfirst("url", None)
    ref = form.getfirst("ref", None)
    if url and ref:
      nonce = form.getfirst("nonce", None)
      if nonce:
        # check it's the right nonce
        if nonce == self.nonce_dict.get(url, None):
          install = form.getfirst("install", None)
          cancel = form.getfirst("cancel", None)
          if install or not cancel:
            self.queue.put(url)
          self.send_response(200)
          self.end_headers()
          REDIRECT_TEMPLATE = self.get_webui_file("redirect.html")
          self.wfile.write(REDIRECT_TEMPLATE % {"ref":ref})
        else:
          # wrong nonce: fail
          self.send_response(401)
          self.end_headers()
          self.wfile.write("""Bad Request""")
      else:
        # no nonce; display confirmation page
        nonce = self.get_random_nonce()
        self.nonce_dict[url] = nonce
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        CONFIRM_TEMPLATE = self.get_webui_file("confirm.html")
        self.wfile.write(CONFIRM_TEMPLATE % {
          "url":cgi.escape(url), 
          "nonce": nonce,
          "ref": cgi.escape(ref)
          })
    else:
      self.send_response(401)
      self.end_headers()
      self.wfile.write("""Bad Request""")
    

class myhttpd(HTTPServer):
  def __init__(self, server_address, RequestHandlerClass, queue):
    HTTPServer.__init__(self, server_address, RequestHandlerClass)
    self.queue = queue
    self.nonce_dict = {}
  def finish_request(self, request, client_address):
    # overridden from SocketServer.TCPServer
    self.RequestHandlerClass(request, client_address, self, self.queue,
      self.nonce_dict)

class Httpd(threading.Thread):
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue
  def run(self):
    server = myhttpd(('localhost', 31750), myhandler, self.queue)
    server.serve_forever()

def displayMessage(msg):
  enso.messages.displayMessage("<p>%s</p>" % msg)

def install_command_from_url(command_url):  
  try:
    fp = urllib.urlopen(command_url)
  except:
    msg = "Couldn't install that command"
    displayMessage(msg)
    return
    
  text = fp.read()
  fp.close()
  
  lines = text.split("\n")
  if len(lines) < 3:
    msg = "There was no command to install!"
    displayMessage(msg)
    return
  while lines[0].strip() == "": 
    lines.pop(0)
  command_file_name = command_url.split("/")[-1]
  if not command_file_name.endswith(".py"):
    msg = "Couldn't install this command %s" % command_file_name
    displayMessage(msg)
    return
  from enso.providers import getInterface
  cmd_folder = getInterface("scripts_folder")()
  command_file_path = os.path.join(cmd_folder, command_file_name)
  shortname = os.path.splitext(command_file_name)[0]
  if os.path.exists(command_file_path):
    msg = "You already have a command named %s" % shortname
    displayMessage(msg)
    return

  allGlobals = {}
  # normalise text for crlf
  text = text.replace('\r\n','\n').replace('\r','\n')
  code = compile( text, command_file_path, "exec" )
  exec code in allGlobals
  installed_commands = [x["cmdName"] for x in 
      cmdretriever.getCommandsFromObjects(allGlobals)]

  if len(installed_commands) == 1:
    install_message = "%s is now a command" % installed_commands[0]
  else:
    install_message = "%s are now commands" % ", ".join(installed_commands)
  # Use binary mode for writing so endlines are not converted to "\r\n" on win32
  fp = open(command_file_path, "wb")
  fp.write(text)
  fp.close()
  displayMessage(install_message)


commandq = Queue.Queue()

def pollqueue(ms):
  try:
    command_url = commandq.get(False, 0)
  except Queue.Empty:
    return

  # FIXME: here we should check to see if it's OK to install this command!
  install_command_from_url(command_url)

def start(eventManager):
  httpd = Httpd(commandq)
  httpd.setDaemon(True)
  httpd.start()
  eventManager.registerResponder( pollqueue, "timer" )

