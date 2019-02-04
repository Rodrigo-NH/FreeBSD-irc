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
from urllib2 import urlopen
import lxml.html
import os, sqlite3
from pathlib import Path


try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FreeBSDbugcatch')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


if not (sqlite3 or sqlalchemy):
    raise callbacks.Error('You have to install python-sqlite3 or '
            'python-sqlalchemy in order to load this plugin.')


class FreeBSDbugcatch(callbacks.Plugin):
    """Catch or direct command PR ID on IRC talk and returns Summary + Link"""

    def __init__(self, irc):
        self.__parent = super(FreeBSDbugcatch, self)
        self.__parent.__init__(irc)
        self.filtering = True
        self.DBpath = self._getDBpath()
        self._checkDBexists()

    def listCommands(self):
        commands = ['add', 'list', 'remove', 'issue']
        return commands

    def inFilter(self, irc, msg):
        self.filtering = True
        self._catchbug(irc, msg)
        return msg

    def _catchbug(self, irc, msg):
        prefixChars = list(conf.supybot.reply.whenAddressedBy.chars())
        ct = False
        res = None
        for x in prefixChars:  # Check user issued commands directly and avoid automatic parsing
            regex_ = r"^(" + re.escape(x) + r")"
            try:
                res = re.search(regex_, msg.args[1])
            except IndexError:
                pass
            if res:
                ct = True

        if not ct:
            channel = msg.args[0]
            res = self._checkDBhasChannel(channel)
            if res is True:
                res = re.search('((pr|issue|bug) #(\d+))|((pr|issue|bug)#(\d+))|((pr|issue|bug)(\d+))|((pr|issue|bug) (\d+))', msg.args[1], flags=re.IGNORECASE)
                bugn = 0
                result = None

                if res:
                    reslenght = res.groups().__len__()
                    for x in range(0, reslenght):
                        val = res.groups()[x]
                        if val is not None:
                            if unicode(val).isnumeric():
                                bugn=val
                if bugn != 0:
                    self._returnbug(irc, msg, bugn, "")

    def _returnbug(self, irc, msg, bugn, nickprefix):
        result = nickprefix
        url = 'https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=' + bugn
        try:
            page = urlopen(url)
            t = lxml.html.parse(page)
            pagedesc = t.find(".//title").text
            if pagedesc == "Missing Bug ID" or pagedesc == "Invalid Bug ID":
                result = ""
            else:
                result = result + pagedesc + " " + url
                result = result.encode('utf8')
                channel = msg.args[0]
                irc.queueMsg(ircmsgs.privmsg(channel.encode('utf8'), result))
        except:
            pass # Network issues

    def _checkDBexists(self):
        fexists = os.path.isfile(self.DBpath)
        if not fexists:
            SQL = "CREATE TABLE registry (channel text PRIMARY KEY); "
            self._SQLexec(SQL, -1)

    def _SQLexec(self, SQL, SQLargs):
        conn = (sqlite3.connect(self.DBpath))
        cursor = conn.cursor()
        if SQLargs != -1:
            cursor.execute(SQL, SQLargs)
            conn.commit()
            res = cursor.fetchall()
            conn.close()
        else:
            cursor.execute(SQL)
            conn.commit()
            res = cursor.fetchall()
            conn.close()
        return res

    def _getDBpath(self):
        p = Path(os.path.dirname(os.path.abspath(__file__)))
        db = str(p.parents[1].joinpath('data')) + "/freebsdbugcatch.db"
        return db

    def _checkDBhasChannel(self, channel):
        chan = (channel,)
        SQL = 'SELECT * FROM registry WHERE channel = ?'
        cursor = self._SQLexec(SQL, chan)
        if len(cursor) == 0:
            return False
        else:
            return True

    def add(self, irc, msg, args, channel):
        """Add channel."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            irc.reply("Channel already activated.", prefixNick=True)
        else:
            SQL = 'INSERT INTO registry (channel) VALUES (?)'
            SQLargs = (channel,)
            self._SQLexec(SQL, SQLargs)
            irc.reply("Channel activated.", prefixNick=True)

    add = wrap(add, ['inChannel'])

    def remove(self, irc, msg, args, channel):
        """Remove channel."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            SQL = 'DELETE FROM registry WHERE channel = ?'
            SQLargs = (channel,)
            self._SQLexec(SQL, SQLargs)
            irc.reply("Channel deactivated.", prefixNick=True)
        else:
            irc.reply("Channel does not exist in DB.", prefixNick=True)

    remove = wrap(remove, ['somethingWithoutSpaces'])

    def list(self, irc, msg, args):
        """List registered channels"""
        SQL = 'SELECT * FROM registry'
        cursor = self._SQLexec(SQL, -1)
        if len(cursor) == 0:
            irc.reply("No channel in DB", prefixNick=True)
        for x in cursor:
            v0 = x[0]  # channel
            output_ = "Channel: " + v0
            irc.reply(output_, prefixNick=True)

    list = wrap(list)

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
