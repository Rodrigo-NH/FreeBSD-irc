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

import urllib2
import re
from supybot import utils, plugins, ircutils, callbacks, ircmsgs
from supybot.commands import *
import inspect
import getopt


try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FreeBSDman')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class FreeBSDman(callbacks.Plugin):
    """Reply with manpage description and link"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(FreeBSDman, self)
        self.__parent.__init__(irc)

    def _getmandesc(self, webData_):

        for x in range(0, 30):
            ifield = re.sub(r'([\n]|[\r])', '', webData_[x], flags=re.M).replace('\t', ' ')
            ifield = ifield.upper()
            if ifield == "NAME":
                idescription = webData_[x + 1]
                idescription = re.sub(r'([\n]|[\r])', '', idescription, flags=re.M).replace('\t', ' ').lstrip(
                    " ").rstrip(" ")
                idescription = idescription.split()
                odescription = ""
                for x in range(2, idescription.__len__()):
                    odescription = odescription + idescription[x] + " "
                break

        return odescription

    def man(self, irc, msg, args, arg1, arg2):
        """<command>[(section)] @[nick]

        Output <command> description from manpage of selected [(section)] and redirects output to @[nick] in the channel.
        """
        uoption = None
        command_ = None
        nick_ = None
        section_ = None

        # Syntax validation
        if arg2 is not None:
            if arg2[:1] != "@":
                uoption = "wrong"
            else:
                if not arg2[1:] in irc.state.channels[msg.args[0]].users: # Check nick is in channel
                    uoption = "wrong"
                else:
                    nick_ = arg2[1:]

        if uoption is not "wrong":
            res = re.findall('\(([^()]*)\)', arg1)
            rl = res.__len__()
            if rl == 1:
                if res is not None:
                    if not res[0].isdigit():
                        uoption = "wrong"
                    else:
                        section_ = res[0]
                        command_ = arg1.split("(")[0]
                else:
                        command_ = arg1
            elif rl == 0:
                command_ = arg1
            else:
                uoption = "wrong"


        # Continue
        if uoption != "wrong":
            if section_ is not None:
                urldir = "https://www.freebsd.org/cgi/man.cgi?query=" + str(command_).lower() + "&sektion=" + \
                         section_
            else:
                urldir = "https://www.freebsd.org/cgi/man.cgi?query=" + str(command_).lower()

            response = urllib2.urlopen(urldir + "&format=ascii")
            webData_ = response.read()
            webData_ = webData_.splitlines()

            if "</pre>" not in str(webData_[0]) and "EMPTY INPUT" not in str(webData_[0]):
                if section_ is None:
                    sektion = re.sub(r'([\n]|[\r])', '', webData_[0], flags=re.M).replace('\t', ' ')
                    sektion = sektion.split()
                    sektion = sektion[0]
                    sektion = sektion.split("(")
                    sektion = "(" + sektion[1]
                else:
                    sektion = "(" + section_ + ")"

                if nick_ is not None:
                    an = nick_ + ": "
                else:
                    an = ""
                queryresult = an + str(command_).lower() + sektion + " - " + self._getmandesc(webData_) + urldir
                irc.reply(queryresult, prefixNick=False)

    man = wrap(man, ['somethingWithoutSpaces', optional('somethingWithoutSpaces')])



Class = FreeBSDman


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
