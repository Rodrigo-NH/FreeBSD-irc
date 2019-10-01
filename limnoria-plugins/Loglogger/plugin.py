###
# Copyright (c) 2019, Rodrigo
# All rights reserved.
#
#
###

from supybot import utils, plugins, ircutils, callbacks, ircmsgs, conf
from supybot.commands import *
import threading, time, io, os
from pathlib import Path
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Loglogger')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Loglogger(callbacks.Plugin):
    """Fetch limnoria logs and reproduce on IRC channels"""
    loopthread = True
    lastknowline = 0

    def __init__(self, irc):
        self.__parent = super(Loglogger, self)
        self.__parent.__init__(irc)
        self.logpath_ = self._getlogpath()
        self._startrun(irc)

    def _startrun(self, irc):
        count = 0
        logfile_ = io.open(self.logpath_, mode="r", encoding="utf-8")
        for line in logfile_: count += 1
        logfile_.close()
        count -= 1
        self.lastknowline = count
        g = threading.Thread(target=self._getlogs, args=(irc,))
        g.setDaemon(True)
        g.start()

    def _getlogs(self, irc):
        while self.loopthread:
            logfile_ = io.open(self.logpath_, mode="r", encoding="utf-8")
            count = 0
            for line in logfile_:
                count += 1
                if count > self.lastknowline:
                    iline_ = line.rstrip("\n")
                    if 'FLUSHERS FLUSHED' not in iline_.upper():
                        while True:
                            if conf.supybot.plugins.Loglogger.Channel() not in irc.state.channels:
                                time.sleep(5)
                            else:
                                irc.queueMsg(ircmsgs.privmsg(conf.supybot.plugins.Loglogger.Channel(), iline_))
                                break
                    self.lastknowline += 1
            logfile_.close()
            time.sleep(5)

    def die(self):
        self.loopthread = False

    def _getlogpath(self):
        p = Path(os.path.dirname(os.path.abspath(__file__)))
        db = str(p.parents[1].joinpath('logs')) + "/messages.log"
        return db

Class = Loglogger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
