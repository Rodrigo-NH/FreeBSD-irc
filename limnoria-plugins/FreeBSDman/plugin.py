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


    def man(self, irc, msg, args, command_):
        """<command>"""
        uoption = None
        command_ = command_.split()
        # possible use case examples:
        # !man zfs 1 @DanDare
        # !man zfs @DanDare
        # !man zfs 1
        # !man zfs

        # Syntax check 1st step
        if command_.__len__() == 3:
            uoption = "full"  # !man zfs 3 @DanDare
        elif command_.__len__() == 2:
            if command_[1].isdigit():
                uoption = "sektion"  # !man zfs 3
            else:
                uoption = "redirect"  # !man zfs @DanDare
        elif command_.__len__() == 1:
            uoption = "simple"  # !man zfs
        else:
            uoption = "wrong"

        # Syntax check 2nd step
        if uoption == "full":
            if command_[2][:1] != "@":
                uoption = "wrong"
            if not command_[1].isdigit():
                uoption = "wrong"

        # Syntax check 3rd step
        if uoption == "redirect":
            if command_[1][:1] != "@":
                uoption = "wrong"
        if uoption == "sektion":
            if not command_[1].isdigit():
                uoption = "wrong"

        # Continue
        if uoption != "wrong":
            if uoption == "sektion" or uoption == "full":
                urldir = "https://www.freebsd.org/cgi/man.cgi?query=" + command_[0] + "&sektion=" + \
                         command_[1]
            else:
                urldir = "https://www.freebsd.org/cgi/man.cgi?query=" + command_[0]

            response = urllib2.urlopen(urldir + "&format=ascii")
            webData_ = response.read()
            webData_ = webData_.splitlines()

            if webData_[0] == "</pre>":
                irc.reply("Manpage not found.", prefixNick=True)
            else:
                sektion = re.sub(r'([\n]|[\r])', '', webData_[0], flags=re.M).replace('\t', ' ')
                sektion = sektion.split()
                sektion = sektion[0]
                sektion = sektion.split("(")
                sektion = "(" + sektion[1]

                description = None
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

                queryresult = ""
                if uoption == "simple" or uoption == "sektion":
                    queryresult = command_[0].lower() + sektion + " - " + odescription + urldir
                elif uoption == "full":
                    queryresult = command_[2][1:] + ": " + command_[
                        0].lower() + sektion + " - " + odescription + urldir
                elif uoption == "redirect":
                    queryresult = command_[1][1:] + ": " + command_[
                        0].lower() + sektion + " - " + odescription + urldir
                irc.reply(queryresult, prefixNick=False)

        else:
            irc.reply("Syntax error.", prefixNick=True)

    man = wrap(man, ['text'])


Class = FreeBSDman


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
