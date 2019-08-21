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

from supybot import utils, plugins, ircutils, callbacks, conf
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import re
import requests
from lxml import etree
from io import BytesIO

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('URLtitleSnarfer')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class URLtitleSnarfer(callbacks.Plugin):
    """Simple URL Title Snarfer"""
    threaded = False

    def __init__(self, irc):
        self.__parent = super(URLtitleSnarfer, self)
        self.__parent.__init__(irc)
        self.filtering = True

    def inFilter(self, irc, msg):
        self.filtering = True
        self._parseline(irc, msg)
        return msg

    def _parseline(self, irc, msg):
        try: # Test actual input from 'inFilter' contains a IRC message in a channel
            ircmsg_ = msg.args[1]
            channel = msg.args[0]
        except:
            ircmsg_ = None

        channlist = list(conf.supybot.plugins.URLtitleSnarfer.channels())
        if ircmsg_ is not None and channel in channlist:
            checkurl = re.search('((http|https)(\S+))', ircmsg_, flags=re.IGNORECASE)
            if checkurl is not None:
                urltext = checkurl.groups()[0]
                try:
                    r = requests.get(urltext, timeout=5)
                    statusCategory = int(r.status_code)                   
                    if statusCategory < 300: # Go ahead only if status code is under 'informational' category
                        data = r.content                        
                        if data is not None:                            
                            enc = r.encoding 
                            parser = etree.HTMLParser(recover=True, encoding=enc)                            
                            tree   = etree.parse(BytesIO(data), parser)                            
                            res = "Title: " + tree.findtext('.//title').replace('\n', ' ').replace('\r', ' ').strip() 
                            if res is not None:
                                irc.queueMsg(ircmsgs.privmsg(channel, res))
                except Exception as err:
                    pass

Class = URLtitleSnarfer