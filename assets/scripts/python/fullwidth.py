# -*- coding: utf-8 -*-
# fullwidth script for weechat - developed by acidvegas in python (https://git.acid.vegas/weechat)

import weechat

def cmd_fullwidth(data, buf, args):
	chars = list()
	for char in list(args):
		if ord(char) == 32:
			char = chr(12288)
		elif ord(char) > 32 and ord(char) <= 126:
			char = chr(ord(char) + 65248)
		chars.append(char)
	weechat.command(buf, '/input send ' + ''.join(chars))
	return weechat.WEECHAT_RC_OK

if weechat.register('fullwidth', 'acidvegas', '1.0', 'ISC', 'convert text to wide characters.', '', ''):
	weechat.hook_command('fullwidth', 'convert text to wide characters.', '<text>', '', '', 'cmd_fullwidth', '')