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
import os, sqlite3, lxml.html, threading, time
from pathlib import Path
from sqlite3 import Error
from urllib2 import urlopen


try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FreeBSDbugs')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

if not (sqlite3 or sqlalchemy):
    raise callbacks.Error('You have to install python-sqlite3 or '
            'python-sqlalchemy in order to load this plugin.')


class FreeBSDbugs(callbacks.Plugin):
    """Monitor bugs.freebsd.org/bugzilla/ and echo new PR entries to registered channels"""
    loopthread = True
    channelscontrol = list()
    lastknowbug = 0
    locklist = False


    def __init__(self, irc):
        self.__parent = super(FreeBSDbugs, self)
        self.__parent.__init__(irc)
        self.DBpath = self._getDBpath()
        self._checkDBexists()
        self._bugRun(irc)


    def listCommands(self):
        commands = ['add', 'remove', 'setactive', 'setinactive', 'setinterval', 'list']
        return commands


    def _bugRun(self, irc):
        SQL = 'SELECT lastknowbug FROM lastknowbug'
        cursor = self._SQLexec(SQL, -1)
        self.lastknowbug = cursor[0][0]
        SQL = 'SELECT * FROM registry'
        cursor = self._SQLexec(SQL, -1)
        for x in cursor:
            v0 = x[0]  # channel
            v1 = x[1]  # isactive
            v2 = x[2]  # updateinterval
            v3 = 0  # lastcheckdtime (lives only in RAM)
            v4 = 0  # Per channel, last know bug (lives only in RAM)
            list_ = [v0, v1, v2, v3, v4]
            self.channelscontrol.append(list_)
            if v1 == 1:
                g = threading.Thread(target=self._getLastBug, args=(irc, v0,))
                g.start()
        t = threading.Thread(target = self._checkchannels ,args=(irc, ))
        t.start()


    def die(self):
        self.loopthread = False
        SQL = 'UPDATE lastknowbug SET lastknowbug = ?'
        SQLargs = (self.lastknowbug,)
        self._SQLexec(SQL, SQLargs)


    def _locklist(self): # It seems that colision/block is possible so this is needed
        if self.locklist == False:
            self.locklist = True
            return True
        else:
            self.locklist = False
            return False


    def _checkchannels(self, irc):
        while self.loopthread:
            time_ = int(time.time())
            while self.locklist:
                time.sleep(0.01)
                pass
            self._locklist()
            for x in range(0, len(self.channelscontrol)):
                v0 = self.channelscontrol[x][0]
                v1 = self.channelscontrol[x][1]
                v2 = self.channelscontrol[x][2]
                v3 = self.channelscontrol[x][3]
                v4 = self.channelscontrol[x][4]
                if v1 == 1 and (time_ - v3) > v2 and v4 != 0:
                    list_ = [v0, v1, v2, time_, v4]
                    self.channelscontrol[x] = list_
                    t = threading.Thread(target=self._updatechannel, args=(irc, x, list_,))
                    t.start()
            self._locklist()
            time.sleep(1)


    def _updatechannel(self, irc, listindex, chancontrol ):
        #print chancontrol
        while self.locklist:
            time.sleep(0.01)
            pass
        self._locklist()
        v0 = chancontrol[0]  # channel
        v1 = chancontrol[1]  # isactive
        v2 = chancontrol[2]  # updateinterval
        v3 = chancontrol[3]  # lastcheckdtime
        v4 = chancontrol[4]  # Per channel last know bug
        lastseen = v4
        reachend = 0
        while reachend == 0:
            lastseen += 1
            url = 'https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=' + str(lastseen)
            try:
                pagedesc = self._getPageTitle(url)
                if pagedesc != "Missing Bug ID":
                    notice = "#" + pagedesc + " " + "https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=" + str(lastseen) + " (NEW)"
                    notice = notice.encode('utf8')
                    if self.loopthread:
                        irc.queueMsg(ircmsgs.privmsg(v0.encode('utf8'), notice))  # notice.encode() must be outside of ircmsgs.privmsg here
                        #print notice
                else:
                    lastseen -= 1
                    reachend = 1
                list_ = [v0, v1, v2, v3, lastseen]
                self.lastknowbug = lastseen
                self.channelscontrol[listindex] = list_
            except:
                lastseen -= 1
        self._locklist()


    def _getLastBug(self, irc, channel):
        maxbug = 500000 # Arbitrary up limit
        minbug = self.lastknowbug
        ct1 = 0
        ct2 = 0
        notAlready = True
        while notAlready and self.loopthread:
            #print "maxbug: " + str(maxbug)
            #print "minbug: " + str(minbug)
            url = 'https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=' + str(maxbug)
            try:
                pagedesc = self._getPageTitle(url)
                ct2 += 1
                if pagedesc == "Missing Bug ID":
                    ct1 = (maxbug - minbug) / 2
                    maxbug = maxbug - ct1
                else:
                    minbug = maxbug
                    maxbug = minbug + ct1
                if maxbug == minbug + 1 or maxbug == minbug:
                    maxbug = minbug - 1 # Define maxbug like ('REAL'maxbug -1) so plugin outputs at least one result after it's loaded or channel set active
                    self.lastknowbug = maxbug
                    notAlready = False
            except:
                pass
        if not notAlready:
            SQL = 'UPDATE lastknowbug SET lastknowbug = ?'
            SQLargs = (maxbug,)
            self._SQLexec(SQL, SQLargs)


        while self.locklist:
            time.sleep(0.01)
            pass
        self._locklist()
        for x in range(0, len(self.channelscontrol)):
            v0 = self.channelscontrol[x][0]
            v1 = self.channelscontrol[x][1]
            v2 = self.channelscontrol[x][2]
            v3 = self.channelscontrol[x][3]
            if str(v0) == channel:
                list_ = [v0, v1, v2, v3, maxbug]
                self.channelscontrol[x] = list_
        self._locklist()


    def _checkDBexists(self):
        fexists = os.path.isfile(self.DBpath)
        if not fexists:
            SQL = "CREATE TABLE registry (channel text PRIMARY KEY, isActive integer, updateInterval integer); "
            self._SQLexec(SQL, -1)
            SQL = "CREATE TABLE lastknowbug (lastknowbug integer); "
            self._SQLexec(SQL, -1)
            SQL = 'INSERT INTO lastknowbug (lastknowbug) VALUES (0)'
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
        db = str(p.parents[1].joinpath('data')) + "/freebsdbugs.db"
        return db


    def _checkDBhasChannel(self, channel):
        chan = (channel,)
        SQL = 'SELECT * FROM registry WHERE channel = ?'
        cursor = self._SQLexec(SQL, chan)
        if len(cursor) == 0:
            return False
        else:
            return True


    def _getPageTitle(self, url):
        page = urlopen(url)
        t = lxml.html.parse(page)
        pagedesc = t.find(".//title").text
        return pagedesc


    def add(self, irc, msg, args, channel, updateInterval):
        """Add channel to receive NEW bugs notices."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            irc.reply("Channel exist in database.", prefixNick=True)
        else:
            if updateInterval < 60 or updateInterval > 600:
                irc.reply("Update interval must be greater or equal 60 seconds AND maxvalue = 600 (10 minutes)", prefixNick=True)
            else:
                SQL = 'INSERT INTO registry (channel, isActive, updateInterval) VALUES (?, ?, ?)'
                SQLargs = (channel, 1, updateInterval)
                self._SQLexec(SQL, SQLargs)
                while self.locklist:
                    time.sleep(0.01)
                    pass
                self._locklist()
                v0 = channel  # channel
                v1 = 1  # isactive
                v2 = updateInterval  # updateinterval
                v3 = 0  # lastcheckdtime
                v4 = 0  # Per channel last know bug
                list_ = [v0, v1, v2, v3, v4]
                self.channelscontrol.append(list_)
                self._locklist()
                irc.reply("Channel added and activated.", prefixNick=True)
                g = threading.Thread(target=self._getLastBug, args=(irc, channel,))
                g.start()

    add = wrap(add, ['inChannel', 'int'])


    def remove(self, irc, msg, args, channel):
        """Remove channel that receives NEW bugs notices."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            SQL = 'DELETE FROM registry WHERE channel = ?'
            SQLargs = (channel,)
            self._SQLexec(SQL, SQLargs)
            while self.locklist:
                time.sleep(0.01)
                pass
            self._locklist()
            for x in range(0, len(self.channelscontrol)):
                v0 = str(self.channelscontrol[x][0])
                if v0 == channel:
                    self.channelscontrol.pop(x)
                    break
            self._locklist()
            irc.reply("Channel removed from DB.", prefixNick=True)
        else:
            irc.reply("Channel does not exist in DB.", prefixNick=True)

    remove = wrap(remove, ['somethingWithoutSpaces'])


    def setinactive(self, irc, msg, args, channel):
        """Set inactive register to channel stored in DB."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            SQL = 'UPDATE registry SET isActive = ? WHERE channel = ?'
            SQLargs = (0, channel)
            self._SQLexec(SQL, SQLargs)
            while self.locklist:
                time.sleep(0.01)
                pass
            self._locklist()
            for x in range(0, len(self.channelscontrol)):
                v0 = str(self.channelscontrol[x][0])
                if v0 == channel:
                    self.channelscontrol[x][1] = 0
            self._locklist()
            irc.reply("Channel set inactive.", prefixNick=True)
        else:
            irc.reply("Channel does not exist in DB.", prefixNick=True)

    setinactive = wrap(setinactive, ['somethingWithoutSpaces'])


    def setactive(self, irc, msg, args, channel):
        """Set active register to channel stored in DB."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            SQL = 'UPDATE registry SET isActive = ? WHERE channel = ?'
            SQLargs = (1, channel)
            self._SQLexec(SQL, SQLargs)
            while self.locklist:
                time.sleep(0.01)
                pass
            self._locklist()
            for x in range(0, len(self.channelscontrol)):
                v0 = str(self.channelscontrol[x][0])
                if v0 == channel:
                    self.channelscontrol[x][1] = 1
                    self.channelscontrol[x][4] = 0
            self._locklist()
            irc.reply("Channel set active.", prefixNick=True)
            g = threading.Thread(target=self._getLastBug, args=(irc, channel,))
            g.start()
        else:
            irc.reply("Channel does not exist in DB.", prefixNick=True)

    setactive = wrap(setactive, ['somethingWithoutSpaces'])


    def setinterval(self, irc, msg, args, channel, updateInterval):
        """Change update interval for channel."""
        res = self._checkDBhasChannel(channel)
        if res is True:
            if updateInterval < 60 or updateInterval > 600:
                irc.reply("Update interval must be greater or equal 60 seconds AND maxvalue = 600 (10 minutes)", prefixNick=True)
            else:
                SQL = 'UPDATE registry SET updateInterval = ? WHERE channel = ?'
                SQLargs = (updateInterval, channel)
                self._SQLexec(SQL, SQLargs)
                while self.locklist:
                    time.sleep(0.01)
                    pass
                self._locklist()
                for x in range(0, len(self.channelscontrol)):
                    v0 = str(self.channelscontrol[x][0])
                    if str(v0) == channel:
                        self.channelscontrol[x][2] = updateInterval
                self._locklist()
                irc.reply("Update interval set to: " + str(updateInterval), prefixNick=True)
        else:
            irc.reply("Channel does not exist in DB.", prefixNick=True)

    setinterval = wrap(setinterval, ['somethingWithoutSpaces', 'int'])


    def list(self, irc, msg, args):
        """List registered channels"""
        SQL = 'SELECT * FROM registry'
        cursor = self._SQLexec(SQL, -1)
        for x in cursor:
            v0 = x[0]  # channel
            v1 = x[1]  # isactive
            v2 = x[2]  # updateinterval
            output_ = "Channel: " + v0 + " | " + "Is active: " + str(v1) + " | " + "Update interval: " + str(v2)
            irc.reply(output_, prefixNick=True)
        SQL = 'SELECT lastknowbug FROM lastknowbug'
        cursor = self._SQLexec(SQL, -1)
        lastknowbug_ = "Last know bug in DB is: " + str(cursor[0][0])
        irc.reply(lastknowbug_, prefixNick=True)

    list = wrap(list)


Class = FreeBSDbugs
