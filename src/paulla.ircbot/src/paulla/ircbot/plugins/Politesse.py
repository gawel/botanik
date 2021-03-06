import irc3
import random
from time import sleep
from irc3.plugins.cron import cron


@irc3.plugin
class Politesse:
    """ Hello world """
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log
        self.users = []
        self.usersreplied = []
        self._hi = ('salut','bonjour','yop', 'matin')
        self._reply = ('Alors, ca roule?', 'C\'est maintenant que t\'arrives?', 'Enfin de retour parmis nous!', 'Te voila enfin! Comment ca va?')

    @irc3.event(irc3.rfc.PING)
    def at_ping(self, data):
        if not self.users:
            self.users = [nick.lower() for nick in self.bot.nicks]

    @irc3.event(irc3.rfc.JOIN)
    def hello(self, mask, channel):
        if mask.nick != self.bot.nick\
                and not mask.nick.lower() in self.users:
                    self.users.append(mask.nick.lower())
                    self.bot.call_with_human_delay(
                            self.bot.privmsg,
                            channel,
                            "Hello %s" % mask.nick)
        elif mask.nick.lower() == self.bot.nick.lower():
            self.users = [nick.lower() for nick in self.bot.nicks]
  
    @irc3.event(irc3.rfc.PRIVMSG)
    def bienlebonjour(self, mask, event, target, data):  
        if [word for word in self._hi if '%s' % word in data.lower()]:
            if mask.nick != self.bot.nick\
                    and not mask.nick.lower() in self.usersreplied:
                        self.usersreplied.append(mask.nick.lower())
                        #self.bot.privmsg(target, "%s, %s" % (mask.nick, self._reply[random.randint(0, len(self._reply)-1)]))
            elif mask.nick.lower() == self.bot.nick.lower():
                self.usersreplied = [nick.lower() for nick in self.bot.nicks]
    

    @cron('0 8 * * *')
    def matin(self):
        for chan in self.bot.channels:
            self.bot.privmsg(chan, 'Matin!')

    @cron('15 3 * * *')
    def update_users(self):
        self.users = [nick.lower() for nick in self.bot.nick]
        self.usersreplied = [nick.lower() for nick in self.bot.nick]

#
