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
from lxml.html import fromstring

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FreeBSDbugcatch')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class FreeBSDbugcatch(callbacks.Plugin):
    """Catch or direct command PR ID on IRC talk and return Summary + Link"""

    def __init__(self, irc):
        self.__parent = super(FreeBSDbugcatch, self)
        self.__parent.__init__(irc)
        self.filtering = True

    def listCommands(self):
        commands = ['issue']
        return commands

    def inFilter(self, irc, msg):
        self.filtering = True
        self._catchbug(irc, msg)
        return msg

    def _catchbug(self, irc, msg):
        try: # Test actual input from 'inFilter' contains a IRC message in a channel
            ircmsg_ = msg.args[1]
            channel = msg.args[0]
        except:
            ircmsg_ = None

        if ircmsg_ is not None:
            prefixChars = list(conf.supybot.reply.whenAddressedBy.chars())
            ct = False
            res = None
            for x in prefixChars:  # Check user issued commands directly and avoid automatic parsing
                regex_ = r"^(" + re.escape(x) + r")"
                res = re.search(regex_, ircmsg_)
                if res:
                    ct = True

            if not ct:
                channlist = list(conf.supybot.plugins.freebsdbugcatch.channels())
                if channel in channlist:
                    res = re.search('((pr|issue|bug) #(\d+))|((pr|issue|bug)#(\d+))|((pr|issue|bug)(\d+))|((pr|issue|bug) (\d+))', ircmsg_, flags=re.IGNORECASE)
                    bugn = 0
                    result = None

                    if res:
                        reslenght = res.groups().__len__()
                        for x in range(0, reslenght):
                            val = res.groups()[x]
                            try:
                                bugn = str(int(val)) # Preferable find a way to test 'val' is digit instead of using try/except
                                if bugn != 0:
                                    self._returnbug(irc, msg, bugn, "")
                            except:
                                pass

    def _returnbug(self, irc, msg, bugn, nickprefix):
        result = nickprefix
        url = 'https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=' + bugn
        try:
            page = requests.get(url, )
            tree = fromstring(page.content)
            pagedesc = tree.findtext('.//title')
            if pagedesc == "Missing Bug ID" or pagedesc == "Invalid Bug ID":
                result = ""
            else:
                result = result + pagedesc + " " + url
                channel = msg.args[0]
                irc.queueMsg(ircmsgs.privmsg(channel, result))
        except:
            pass # Network issues

    def issue(self, irc, msg, args, text):
        """<issueID> @[nick]

        Output Bugzilla <issueID> description and redirects output to @[nick] in the channel.
        """
        uoption_ = None
        bugid_ = None
        nick_ = None

        # Syntax check
        res = re.match("(\d+)( @(\w+))?\Z", text)
        if res is not None:
            res = res.groups()
            bugid_ = res[0]
            nick_ = res[2]
            if nick_ is not None:
                if not nick_ in irc.state.channels[msg.args[0]].users:  # Check nick is in channel
                    uoption_ = "nonick"
                else:
                    nick_ = nick_ + ": "
        else:
            uoption_ = "wrongS"

        # continue
        if uoption_ != "wrongS" and uoption_ != "nonick":
            if nick_ == None:
                nick_ = ""
            self._returnbug(irc, msg, bugid_, nick_)
        elif uoption_ == "wrongS":
            irc.reply(self.getCommandHelp(['issue']))  # Probably not the best way for achieving this
    issue = wrap(issue, ['text'])


Class = FreeBSDbugcatch


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
