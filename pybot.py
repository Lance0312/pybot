#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2

from bs4 import BeautifulSoup
import ConfigParser
import cookielib
import re
import signal
import socket
import time
import urllib2

config = ConfigParser.RawConfigParser()
config.read('config')

IRC_SERVER = config.get('general', 'IRC_SERVER')
IRC_PORT = config.getint('general', 'IRC_PORT')
IRC_NICK = config.get('general', 'IRC_NICK')
IRC_CHANNELS = eval(config.get('general', 'IRC_CHANNELS'), {}, {})

def look_for_sender(data):
  sender = None
  match = re.match(':(\w+)!', data)
  if match != None:
    sender = match.group(1)
  return sender

def signal_handler(signal, frame):
  s.send('QUIT\r\n')
  s.close()
signal.signal(signal.SIGINT, signal_handler)
  

try:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((IRC_SERVER, IRC_PORT))
except socket.error:
  s.close()
  raise ServerConnectionError("Couldn't connect to socket!")

try:
  s.send('USER ' + IRC_NICK + ' * * :' + IRC_NICK + '\r\n')
  s.send('NICK ' + IRC_NICK + '\r\n')
  for channel,key in IRC_CHANNELS:
    s.send('JOIN ' + channel + ' ' + key + '\r\n')
  time.sleep(10)
  for channel,key in IRC_CHANNELS:
    s.send('PRIVMSG ' + channel + ' :Hi, there!\r\n')
  while True:
    data = s.recv(256)
    sender = look_for_sender(data)
    print data
    if data:
      if 'PING' in data:
        match = re.match('^PING (:\w+)', data)
        if match != None:
          s.send('PONG ' + match.group(1) + '\r\n')
      if 'http' in data:
        if re.match(':\w+_bot.*', data):
          continue
        match = re.match('.*PRIVMSG\s+(\S+)\s+:.*(https?://\S+)', data)
        if match != None:
          channel = match.group(1)
          url = match.group(2)
          try:
            cj = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urlhandle = opener.open(url)
            if 'text/html' in urlhandle.info()['Content-Type']:
              soup = BeautifulSoup(urlhandle)
              title = re.sub('[\r\n ]+', ' ', soup.title.string)
              s.send("PRIVMSG %s :%s's url: [] %s\r\n" %
                (channel, sender, title.encode('utf-8')))
            else:
              s.send("PRIVMSG %s :%s's url: [] is %s type. (%.2f MB)\r\n" %
                (channel, sender, urlhandle.info()['Content-Type'],
                  float(urlhandle.info()['Content-Length'])/1024/1024))
          except AttributeError:
            s.send('PRIVMSG ' + channel + ' :' + sender + ': No title!\r\n')
          except IOError:
            s.send('PRIVMSG ' + channel + ' :' + sender + ': No such site!\r\n')
except socket.error:
  print 'err'


