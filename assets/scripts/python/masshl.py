# -*- coding: utf-8 -*-
# masshl script for weechat - developed by acidvegas (https://git.acid.vegas/weechat)

import weechat

nicks = list()

def timer_cb(data, remaining_calls):
	try:
		chan = data.split('[split]')[0]
		msg  = data.split('[split]')[1]
		if '%n' in msg:
			while '%n' in msg:
				msg = msg.replace('%n', nicks[0], 1)
				nicks.pop(0)
			weechat.command(chan, msg)
	except:
		pass
	finally:
		return weechat.WEECHAT_RC_OK

def masshl_cmd_cb(data, buffer, args):
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
