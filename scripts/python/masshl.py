# -*- coding: utf-8 -*-
# developed by acidvegas (https://acid.vegas/weechat)

import weechat

nicks = list()

def timer_cb(data, remaining_calls):
	split = data.split('[split]')
	weechat.command(split[0], split[1].replace('%n',nicks[0]))
	nicks.pop(0)
	return weechat.WEECHAT_RC_OK

def masshl_cmd_cb(data, buffer, args):
	global nicks
	server   = weechat.buffer_get_string(buffer, 'localvar_server')
	channel  = weechat.buffer_get_string(buffer, 'localvar_channel')
	nicklist = weechat.infolist_get('irc_nick', '', server+','+channel)
	while weechat.infolist_next(nicklist):
		nicks.append(weechat.infolist_string(nicklist, 'name'))
	weechat.infolist_free(nicklist)
	del server, channel, nicklist
	nicks.pop(0)
	if args[:2] == '-1':
		weechat.command(buffer, ', '.join(nicks))
	else:
		weechat.hook_timer(100, 0, len(nicks), 'timer_cb', '[split]'.join((buffer,args)))
	return weechat.WEECHAT_RC_OK

if weechat.register('masshl', 'acidvegas', '1.0', 'ISC', 'mass hilight all nicks in a channel', '', ''):
	weechat.hook_command('masshl', 'mass hilight all nicks in a channel', '', '', '', 'masshl_cmd_cb', '')