# -*- coding: utf-8 -*-
# pump ascii from the ircart repo script for weechat - developed by wrk

import time
import weechat
import requests
import random

def cmd_pump(data, buf, name):
	ascii_list=requests.get("https://raw.githubusercontent.com/ircart/ircart/master/ircart/.list").text.split("\n")
	asc=""
	if name == '':
		asc=random.choice(ascii_list)
	else:
		asc=[i for i in ascii_list if name in i][0]
	data=requests.get(f"https://raw.githubusercontent.com/ircart/ircart/master/ircart/{asc}.txt").text
	weechat.command(buf, f'/input send {data}')
	return weechat.WEECHAT_RC_OK

if weechat.register('pump', 'wrk', '1.0', 'ISC', 'pump', '', ''):
	weechat.hook_command('pump', 'pumpit name', '<text>', '', '', 'cmd_pump', '')