#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Plugins to show URL's title
"""
import unicodedata
import sqlite3
from os.path import exists, dirname, expanduser
import re
from urllib.parse import urlparse
from os import makedirs

import irc3
from irc3.plugins.command import command
import requests
from bs4 import BeautifulSoup

TITLE_MSG = "Titre: %s - (@ %s)"
URL_ERROR_MSG = "Erreur %d: %s"

@irc3.plugin
class Urls(object):
    """
    A plugin for print Url title
    """
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log

        if 'paulla.ircbot.plugins.Urls' in self.bot.config\
                and 'db' in self.bot.config['paulla.ircbot.plugins.Urls']\
                and self.bot.config['paulla.ircbot.plugins.Urls']['db']:
            database = self.bot.config['paulla.ircbot.plugins.Urls']['db']
        else:
            database = '~/.irc3/Urls.db'
        if '~' in database:
            database = expanduser(database)
        if not exists(database):
            if not exists(dirname(database)):
                makedirs(dirname(database))
            open(database, 'a').close()
        self.conn = sqlite3.connect(database)
        cur = self.conn.cursor()
        cur.execute('''create table if not exists url
                (id_url integer primary key,
                value text,
                title text,
                dt_inserted datetime,
                nick text
                )''')
        cur.execute('''create table if not exists tag
                (id_tag integer primary key,
                id_url interger,
                value text,
                dt_inserted datetime,
                nick text
                )''')

        cur.execute('''create table if not exists old
                (id_old integer primary key,
                value text,
                dt_inserted datetime,
                nick text
                )''')
        self.conn.commit()
        cur.close()


    @irc3.event(irc3.rfc.PRIVMSG)
    def url(self, mask, event, target, data):
        """
        parse and reply url title
        """
        urls = re.findall(r'(?P<url>http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', data)

        nick = mask.split('!')[0]

        for url in urls:
            req = requests.get(url)
            # check HTTP status code, success if code is 2xx (rfc 2616)
            if (req.status_code / 100 % 10) == 2:
                soup = BeautifulSoup(req.content)
                title = unicodedata.normalize('NFKD',soup.title.string.decode('UTF-8')).encode('ascii', 'ignore')
                domain = urlparse(url).netloc.split(':')[0]
                self.bot.privmsg(target, TITLE_MSG % (title, domain))

                cur = self.conn.cursor()

                cur.execute("SELECT dt_inserted, nick from url where value='%s'" % url)
                data = cur.fetchall()

                if data:
                    self.display_old(target, nick, data[0][0])
                else:
                    cur.execute("INSERT INTO url(value, title, nick, dt_inserted) VALUES('%s', '%s', '%s', datetime('now')) ;" % (url, title, nick))
                    self.conn.commit()
                cur.close()
            else:
                self.bot.privmsg(target, URL_ERROR_MSG % (req.status_code, url))

    def display_old(self, target, nick, dt_inserted):
        """display an old stored URL"""
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM old ORDER BY RANDOM() LIMIT 1")
        data = cur.fetchall()
        if data:
            self.bot.privmsg(target, '%s %s %s' % (nick, data[0][0], dt_inserted))
        cur.close()

    @command(permission='admin', public=True)
    def old(self, mask, target, args):
        """old command

           %%old <add/remove> <message>...
        """
        nick = mask.split('!')[0]

        if args['<add/remove>'].lower() == 'add':
            cur = self.conn.cursor()
            cur.execute("INSERT INTO old(value, nick, dt_inserted) VALUES('%s', '%s', datetime('now'));" %(str(' '.join(args['<message>'])).replace("'", "''"), nick))
            self.conn.commit()
            return

        if args['<add/remove>'].lower() == 'remove':
            cur = self.conn.cursor()
            cur.execute("DELETE FROM old where value= '%s';" %(str(' '.join(args['<message>'])).replace("'", "''")))
            self.conn.commit()
            return

    @command
    def show(self, mask, target, args):
        """tag command

           %%show <url>
        """
        cur = self.conn.cursor()
        cur.execute("SELECT id_url FROM url WHERE value='%s'" % args['<url>'])
        data = cur.fetchall()

        if not data:
            return

        cur.execute("SELECT value FROM tag WHERE id_url=%d;" % data[0][0])

        data = cur.fetchall()

        tags = ' '.join([tag[0] for tag in data])
        nick = mask.split('!')[0]

        self.bot.privmsg(target, '%s: %s' % (nick, tags))

    @command(permission='admin', public=True)
    def tag(self, mask, target, args):
        """tag command

           %%tag <add/remove> <url> <tags>...
        """
        nick = mask.split('!')[0]

        cur = self.conn.cursor()
        cur.execute("SELECT id_url FROM url WHERE value='%s'" % args['<url>'])
        data = cur.fetchall()

        if not data:
            return

        if args['<add/remove>'].lower() == 'add':

            for tag in args['<tags>']:
                cur.execute("INSERT INTO tag(id_url, value, nick, dt_inserted) VALUES(%d, '%s', '%s', DATETIME('now'));" % (data[0][0], tag, nick))
            self.conn.commit()
            cur.close()
            return

        if args['<add/remove>'].lower() == 'remove':
            for tag in args['<tags>']:
                cur.execute("DELETE FROM tag WHERE id_url=%d AND value='%s';" % (data[0][0], tag))
            self.conn.commit()
            cur.close()
            return
