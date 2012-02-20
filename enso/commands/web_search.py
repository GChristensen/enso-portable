import urllib
import webbrowser
import threading
import os
import sys
import platform
import re
import xml.sax.saxutils
import logging

from urlparse import urlparse, urlunparse

from enso.commands import CommandManager, CommandObject
from enso.messages import displayMessage
import enso.config


class ThreadedFunc(threading.Thread):
    def __init__(self, target, args = None):
        self.__target = target
        self.__args = args
        threading.Thread.__init__(self)
        self.__success = False
        self.__retval = None
        self.setDaemon(True)
        self.start()

    def run(self):
        if self.__args is None:
            self.__retval = self.__target()
        else:
            self.__retval = self.__target(*self.__args)
        self.__success = True

    def wasSuccessful(self):
        if self.isAlive():
            raise Exception( "Thread not finished" )
        return self.__success

    def getRetval(self):
        if self.isAlive():
            raise Exception( "Thread not finished" )
        return self.__retval


class WebSearchCmd(CommandObject):

    def __init__(self, url_template):
        super( WebSearchCmd, self ).__init__()

        self._url_template = url_template
        self.desc = "asasa"
        self.help = "asasa"
        self.hel_text = "sdsd"
        self.HELP = "Asasa"
        self.DESCRIPTION = "aaaa"
        self.setDescription("D")
        self.setName("H")

    def __call__(self, ensoapi, query=None):
        if not query:
            query = ensoapi.get_selection().get("text", u"")
        query = query.strip().strip("\0")

        if not query:
            ensoapi.display_message( "No query." )
            return

        query = urllib.quote_plus( query.encode("utf-8") )

        try:
            webbrowser.open( self._url_template % {"query" : query} )
        except Exception, e:
            logging.error(e)


def _extract_url_from_text(text):
    # Extract URL from text
    urlfinders = [
        re.compile("(?#Protocol)(?:(?:ht|f)tp(?:s?)\:\/\/|~/|/)?(?#Username:Password)(?:\w+:\w+@)?(?#Subdomains)(?:(?:[-\w]+\.)+(?#TopLevel Domains)(?:com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|museum|travel|[a-z]{2}))(?#Port)(?::[\d]{1,5})?(?#Directories)(?:(?:(?:/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+)+|/)+|\?|#)?(?#Query)(?:(?:\?(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)(?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)*)*(?#Anchor)(?:#(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)?"),
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]"),
        re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
        re.compile("(~/|/|\\./)([-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]|\\\\)+"),
        ]

    url = text.strip(" \t\r\n\0")
    print url
    for urlregexp in urlfinders:
        matched = re.search(urlregexp, url, re.IGNORECASE)
        if matched:
            print "matched: " + str(matched.groups())
            url = matched.group(0)
            print "matched: %s" % url
            break

    logging.info("Extracted URL: \"%s\"" % url)

    parsed_url = urlparse(url)
    print parsed_url

    if parsed_url.scheme == '' and parsed_url.netloc == '':
        url = "http://" + url
        parsed_url = urlparse(url)
        print parsed_url

    if parsed_url.netloc != "":
        if parsed_url.scheme == "":
            # make http default
            parsed_url = urlparse(urlunparse(["http"] + list(parsed_url[1:])))
            print parsed_url
        return parsed_url

    return None


def cmd_abbreviation(ensoapi, query = None):
    """ Search for abbreviation meaning """
    ws = WebSearchCmd("http://www.urbandictionary.com/define.php?term=%(query)s")
    ws(ensoapi, query)


def cmd_wikipedia(ensoapi, query = None):
    """ Search Wikipedia """
    ws = WebSearchCmd("http://en.wikipedia.org/wiki/%(query)s")
    ws(ensoapi, query)


def cmd_imdb(ensoapi, query = None):
    """ Search Internet Movie Database """
    ws = WebSearchCmd("http://www.imdb.com/find?s=all&q=%(query)s&x=0&y=0")
    ws(ensoapi, query)


def cmd_youtube(ensoapi, query = None):
    """ Search videos on Youtube """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://www.youtube.com/results?search_query=%(query)s&search_type=&aq=0&oq=")
    ws(ensoapi, query)


def cmd_urban_dictionary(ensoapi, query = None):
    """ Search urban dictionary """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://www.urbandictionary.com/define.php?term=%(query)s")
    ws(ensoapi, query)


def cmd_images(ensoapi, query = None):
    """ Search Google images """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://images.google.com/images?um=1&hl=en&rlz=1C1GGLS_en-USCZ294&q=%(query)s&btnG=Search+Images")
    ws(ensoapi, query)


def cmd_deviantart(ensoapi, query = None):
    """ Search DeviantArt.com """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://deviantart.com/#order=24&q=%(query)s")
    ws(ensoapi, query)


def cmd_website(ensoapi, text = None):
    """ Go to web site {text} """
    import urllib
    import simplejson
    import urllib2
    import time
    import threading
    import logging

    def set_description(arg):
        print arg

    json = None

    if text is None:
        sel = None
        try:
            sel = ensoapi.get_selection()
        except:
            pass
        logging.debug("Selection: " + str(sel))
        if sel:
            text = sel.get('text')

    if text is None:
        ensoapi.display_message("No text provided", "Error")
        return

    text = text.replace(":", ", ").strip().strip("\0")

    query = urllib.urlencode({
        'q' : text 
    })

    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % (query)
    #print url
    resp = urllib2.urlopen(url)
    json = simplejson.loads(resp.read())
    #logging.info(json)
    if json and json['responseStatus'] == 200 and len(json.get('responseData').get('results')) > 0:
        url = json.get('responseData').get('results')[0].get('url')
        #ensoapi.display_message(url, "Translated text")
    
        try:
            webbrowser.open( url )
        except Exception, e:
            logging.error(e)


def website_set_description(arg):
    return u"Go to web site \u201c%s\u201d" % arg

cmd_website.set_description = website_set_description


def cmd_download(ensoapi, text):
    """ Download software """
    if text is None:
        sel = None
        try:
            sel = ensoapi.get_selection()
        except:
            pass
        logging.debug("Selection: " + str(sel))
        if sel:
            text = sel.get('text')

    if text is None:
        ensoapi.display_message("No text provided", "Error")
        return

    text = text.replace(":", ", ").strip().strip("\0")

    opsys = ""
    if sys.platform.startswith("win"):
        opsys = "windows"
        #if platform.win32_ver()[0]:
        #    opsys = opsys + " " + platform.win32_ver()[0]
        #if "64" in platform.architecture()[0]:
        #    opsys = opsys + " 64-bit 64bit"
        #else:
        #    opsys = opsys + " 32-bit 32bit"
    elif sys.platform.startswith("linux"):
        opsys = "linux"
    elif sys.platform.startswith("darwin"):
        opsys = ".dmg"

    text = text + " download " + opsys
    #print text
    cmd_website(ensoapi, text)


def cmd_stackoverflow(ensoapi, query = None):
    """ Search stackoverflow.com """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://stackoverflow.com/search?q=%(query)s")
    ws(ensoapi, query)


def cmd_torrent(ensoapi, query = None):
    """ Search torrents """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
    ws = WebSearchCmd("http://www.speckly.com/s?q=%(query)s&f=exact")
    ws(ensoapi, query)


def cmd_wolfram(ensoapi, query = None):
    """ Search wolfram-alpha """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
    ws = WebSearchCmd("http://www.wolframalpha.com/input/?i=%(query)s")
    ws(ensoapi, query)


def cmd_subtitles(ensoapi, query = None):
    """ Search subtitles for movie """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
    ws = WebSearchCmd("http://www.opensubtitles.org/en/search2/sublanguageid-cze/moviename-%(query)s")
    ws(ensoapi, query)


def cmd_filestube(ensoapi, query = None):
    """ Search for file on filestube.com """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
    ws = WebSearchCmd("http://www.filestube.com/search.html?q=%(query)s&select=All")
    ws(ensoapi, query)


def cmd_define_ninjawords(ensoapi, query = None):
    """ Search word definition using ninjawords.com """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
    ws = WebSearchCmd("http://ninjawords.com/%(query)s")
    ws(ensoapi, query)


def cmd_urban_dictionary(ensoapi, query = None):
    """ Search urban dictionary """
    if query:
        query = query.replace(":", ", ").strip().strip("\0")
    ws = WebSearchCmd("http://www.urbandictionary.com/define.php?term=%(query)s")
    ws(ensoapi, query)


python_ver = "%d.%d" % (sys.version_info[0], sys.version_info[1])

def cmd_python_help(ensoapi, query = None):
    """ Search Python %s documentation """
    if query:
        query = query.replace(":", ",").strip().strip("\0")
        query = query.replace("-", "_").strip()
    ws = WebSearchCmd("http://starship.python.net/crew/theller/pyhelp.cgi?keyword=%(query)s&version=" + python_ver)
    ws(ensoapi, query)

cmd_python_help.func_doc = cmd_python_help.func_doc % python_ver


def cmd_thesaurus(ensoapi, word = None):
    """ Search English thesaurus """
    if not word:
        word = ensoapi.get_selection().get("text", u"")
        word = word.strip()

        if not word:
            ensoapi.display_message( "Parameter required." )
            return

    word = word.replace(":", ",").strip().strip("\0")

    ws = WebSearchCmd("http://thesaurus.reference.com/browse/%(query)s")
    ws(ensoapi, word)
    




def get_html(ensoapi, url):
    import urllib
    import urllib2

    if url is None:
        return None

    resp = urllib2.urlopen(url)
    return resp.read()


def cmd_is_down(ensoapi, url = None):
    """ Check if the site is down """
    if url is None:
        get_selection_thread = ThreadedFunc(
            target = ensoapi.get_selection
        )
        while get_selection_thread.isAlive():
            yield
        if get_selection_thread.wasSuccessful():
            seldict = get_selection_thread.getRetval()
            if seldict.get("text"):
                url = seldict['text'].strip().strip("\0")

    if url is None:
        return

    parsed_url = _extract_url_from_text(url)
    
    if not parsed_url:
        ensoapi.display_message("Unrecognized URL format.")
        return

    scheme = parsed_url.scheme
    netloc = parsed_url.netloc
    if netloc.endswith(":80"):
        netloc = netloc[:-3]
    base_url = scheme + "://" + netloc

    print base_url

    query_url = "http://downforeveryoneorjustme.com/%s" % urllib.quote_plus(base_url)
    t = ThreadedFunc(
        target = get_html,
        args = (ensoapi, query_url))

    while t.isAlive():
        yield

    if t.wasSuccessful():
        html = t.getRetval()
        if html.find("It's just you") > -1:
            displayMessage(u"<p>Site <command>%s</command> is online</p>" % base_url)
        elif html.find("doesn't look like a site") > -1:
            displayMessage(u"<p>Site <command>%s</command> is unknown!</p>" % base_url)
        elif html.find("It's not just you") > -1:
            displayMessage(u"<p>Site <command>%s</command> is down!</p>" % base_url)
        else:    
            print html


def ping_host(ensoapi, host):
    assert host is not None
    
    pingres = os.popen(
        os.path.expandvars(
            "${WINDIR}\\system32\\ping.exe -n 1 -w 1000 %s") 
            % host, "r")
    sys.stdout.flush()
    average_ping = None
    while 1:
        line = pingres.readline()
        if not line: 
            break
        loss = re.findall("([0-9]+)% loss", line)
        if loss:
            if int(loss[0]) > 0:
                break
        average = re.findall("Average = ([0-9]+)ms", line)
        if average:
            average_ping = int(average[0])

    displayable_host = xml.sax.saxutils.escape(host)
    if average_ping is not None:
        displayMessage(u"<p>Host <command>%s</command> is up! (%dms)</p>" 
                       % (displayable_host, average_ping))
    else:
        displayMessage(u"<p>Host <command>%s</command> is down</p>" 
                       % displayable_host)

def cmd_ping(ensoapi, host = None):
    """ Ping the host (hostname or IP-address, use . for recently pinged) """
    if host is None:
        seldict = ensoapi.get_selection()
        if seldict.get("text"):
            host = seldict['text'].strip().strip("\0")

    if host is None:
        return

    if host == ".":
        host = None
        # User wants to ping again recet host
        if hasattr(enso.config, "CMD_PING_LAST_SITE"):
            host = enso.config.CMD_PING_LAST_SITE
        if host is None:
            ensoapi.display_message("No host has been pinged recently.")
    else:
        # Store it for later reuse
        enso.config.CMD_PING_LAST_SITE = host

    displayable_host = xml.sax.saxutils.escape(host)
    displayMessage(u"<p>Pinging host <command>%s</command></p>" % displayable_host)
    
    pt = threading.Thread(target = ping_host, args = (ensoapi, host))
    pt.start()



def cmd_url(ensoapi, parameter = None):
    """ Open selected text as URL in browser. """
    if parameter != None:
        text = parameter.decode()
    else:
        seldict = ensoapi.get_selection()
        text = seldict.get( "text", u"" )

    text = text.strip(" \t\r\n\0")
    if not text:
        ensoapi.display_message( "No text was selected." )
        return

    parsed_url = _extract_url_from_text(text)
    
    if not parsed_url:
        ensoapi.display_message("Unrecognized URL format.")
        return

    try:
        """
		if webbrowser.get("kmeleon") is None:
            webbrowser.register(
                "kmeleon",
                None,
                webbrowser.BackgroundBrowser(
                    "C:\winapp\Internet\KMeleon\k-meleon.exe"), -1)
        """
        logging.info(webbrowser.open_new_tab(parsed_url.geturl()))
    except Exception, e:
        logging.error(e)


def cmd_what_is_my_ip(ensoapi):
    """ Show the external IP address """
    def make_get_url_func(url):
        def get_url():
            import urllib2

            f = urllib2.urlopen(url)
            return f.read()
        return get_url
    
    import re
    thread = ThreadedFunc(make_get_url_func("http://checkip.dyndns.com/"))
    while thread.isAlive():
        yield
    matches = []
    ip = re.search("Address: ([^<]+)", thread.getRetval()).group(1)
    ensoapi.display_message("Your IP is %s." % ip)

# vim:set tabstop=4 shiftwidth=4 expandtab:
