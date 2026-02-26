# -*- coding: utf-8 -*-
# pump ascii from the ircart repo script for weechat - developed by wrk

import time
import weechat
import urllib.request
import random

def cmd_pump(data, buf, name):
	ascii_list=urllib.request.urlopen("https://git.supernets.org/ircart/ircart/raw/branch/master/ircart/.list").read().decode('utf-8').split("\n")
	asc=""
	if name == '':
		asc=random.choice(ascii_list)
	else:
		asc=[i for i in ascii_list if name in i][0]
	data=urllib.request.urlopen(f"https://git.supernets.org/ircart/ircart/raw/branch/master/ircart/{asc}.txt").read().decode('utf-8')
	weechat.command(buf, f'/input send {data}')
	return weechat.WEECHAT_RC_OK

if weechat.register('pump', 'wrk', '1.0', 'ISC', 'pump', '', ''):
	weechat.hook_command('pump', 'pumpit name', '<text>', '', '', 'cmd_pump', '')