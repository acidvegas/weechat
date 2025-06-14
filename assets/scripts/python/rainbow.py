# -*- coding: utf-8 -*-
# rainbow script for weechat - developed by acidvegas in python (https://git.acid.vegas/weechat)

import weechat

def cmd_rainbow(data, buf, args):
	colors = [5,4,7,8,3,9,10,11,2,12,6,13]
	output = ''
	if args[:2] == '-w':
		for word in args[2:].split():
			output += '\x03' + str(colors[0]) + word + ' '
			colors.append(colors.pop(0))
	else:
		for char in list(args):
			if char == ' ':
				output += char
			else:
				output += '\x03' + str(colors[0]) + char
				colors.append(colors.pop(0))
	weechat.command(buf, '/input send ' + output)
	return weechat.WEECHAT_RC_OK

if weechat.register('rainbow', 'acidvegas', '1.0', 'ISC', 'rainbow text', '', ''):
	weechat.hook_command('rainbow', 'rainbow text', '<text>', '', '', 'cmd_rainbow', '')