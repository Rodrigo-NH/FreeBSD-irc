# Copyright (c) 2019, Rodrigo Nascimento Hernandez, rodrigo.freebsd@minasambiente.com.br
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#   1- Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#   2- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
###

from supybot import utils, plugins, ircutils, callbacks, ircmsgs
from supybot.commands import *
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Githubgethook')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Githubgethook(callbacks.Plugin):
    """Get Github WebHook POST and redirect to channels"""
    threaded = False
    loopthread = True

    def __init__(self, irc):
        self.__parent = super(Githubgethook, self)
        self.__parent.__init__(irc)
        self.webserver = httpreq
        self.httpd = HTTPServer(('localhost', 49010), self.webserver)
        self._loadHttpd(irc)

    def _loadHttpd(self, irc):
        g = threading.Thread(target=self._serverstart, args=(irc, ))
        g.setDaemon(True)
        g.start()

    def _serverstart(self, irc):
        while self.loopthread:
           self.httpd.handle_request()
           postData = self.webserver.postData
           if postData is not None:
                self._payloadproc(irc, postData)
        self.httpd.socket.close()
        self.httpd.server_close()
        self.httpd.shutdown()

    def _payloadproc(self, irc, postData):
        message_ = None
        committer_ = None
        file_ = ""
        url_ = None

        sd_ = json.loads(postData)
        httpreq.postData = None

        for t in sd_:
            if t == 'commits':
                cont = sd_[t][0]
                for o in cont:
                    content = str(cont[o])
                    if o == 'message':
                        message_ = content
                    if o == 'url':
                        url_ = content
                    if o == 'modified':
                        if content != '[]':
                            file_ = file_ + " modified: " + content
                    if o == 'added':
                        if content != '[]':
                            file_ = file_ + "added: " + content
                    if o == 'removed':
                        if content != '[]':
                            file_ = file_ + " removed: " + content
                    if o == 'author':
                        for x in cont[o]:
                            if x == 'username':
                                committer_ = cont[o][x]

        output_ = message_ + " - " + file_ + " - (" + committer_ + ") - " + url_
        irc.queueMsg(ircmsgs.privmsg("#freebsd-labs", output_))

    def die(self):
        self.loopthread = False

Class = Githubgethook

class httpreq(BaseHTTPRequestHandler):
    postData = None

    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        self.postData = None

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        httpreq.postData = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args): # Avoid logging to stdout. TODO: Log to limnoria? (y)(n)
        return

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
