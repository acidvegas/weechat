# -*- coding: utf-8 -*-
# unifuck script for weechat - developed by acidvegas in python (https://git.acid.vegas/weechat)

import random
import weechat

def cmd_unifuck(data, buf, args):
	if args[:2] == '-e': # Emoji
		msg = ''
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x1F600,0x1F64F))
	elif args[:3] == '-ch': # Chinese
		msg = ''
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x4E00,0x9FFF))
	elif args[:3] == '-cu': # CJK Unified Ideographs
		msg = ''
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x12000,0x123FF))
	else: # Unicode
		msg='\u202e\u0007\x03' + str(random.randint(2,13))
		for i in range(random.randint(300, 400)):
			msg += chr(random.randint(0x1000,0x3000))
	weechat.command(buf, '/input send ' + msg)
	return weechat.WEECHAT_RC_OK

if weechat.register('unifuck', 'acidvegas', '1.0', 'ISC', 'random unicode spam', '', ''):
	weechat.hook_command('unifuck', 'random unicode spam', '', '', '', 'cmd_unifuck', '')