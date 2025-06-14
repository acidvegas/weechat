# -*- coding: utf-8 -*-
# unifuck script for weechat - developed by acidvegas in python (https://git.acid.vegas/weechat)

import random
import weechat

def cmd_unifuck(data, buf, args):
	if args[:2] == '-e':
		msg = ''
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x1F600,0x1F64F))
	else:
		msg='\u202e\u0007\x03' + str(random.randint(2,13))
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x1000,0x3000))
	weechat.command(buf, '/input send ' + msg)
	return weechat.WEECHAT_RC_OK

if weechat.register('unifuck', 'acidvegas', '1.0', 'ISC', 'random unicode spam', '', ''):
	weechat.hook_command('unifuck', 'random unicode spam', '', '', '', 'cmd_unifuck', '')