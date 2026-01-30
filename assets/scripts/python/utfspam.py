#!/usr/bin/env python3
# Unicode Spam Filter - developed by acidvegas in python (https://github.com/acidvegas/weechat)

import weechat

SCRIPT_NAME    = 'utf8spam'
SCRIPT_AUTHOR  = 'acidvegas'
SCRIPT_VERSION = '1.1'
SCRIPT_LICENSE = 'ISC'
SCRIPT_DESC    = 'Replace unicode spam bursts in messages (U+1000–U+3000, except box/block), toggle with /utf8spam'

ENABLED   = True
THRESHOLD = 10


def is_boxblock_chars(o):
	return (0x2500 <= o <= 0x257F) or (0x2580 <= o <= 0x259F)


def count_forbidden_unicode(s):
	c = 0
	for ch in s:
		o = ord(ch)
		if 0x1000 <= o <= 0x3000 and not is_boxblock_chars(o):
			c += 1
	return c


def warning_text():
	return '{}{}   UNICODE SPAM DETECTED   {}'.format(weechat.color('white,red'), weechat.color('bold'), weechat.color('reset'))


def utf8spam_cmd_cb(data, buffer, args):
	global ENABLED, THRESHOLD
	argv = args.strip().split()

	if argv:
		try:
			n = int(argv[0])
			if n < 1:
				raise ValueError
			THRESHOLD = n
			weechat.prnt(buffer, 'utf8spam: threshold={}'.format(THRESHOLD))
		except Exception:
			weechat.prnt(buffer, 'utf8spam: invalid threshold')
		return weechat.WEECHAT_RC_OK

	ENABLED = not ENABLED
	weechat.prnt(buffer, 'utf8spam: {}'.format('ON' if ENABLED else 'OFF'))
	return weechat.WEECHAT_RC_OK


def get_tags_from_modifier_data(modifier_data):
	if modifier_data.startswith('0x'):
		parts = modifier_data.split(';', 1)
		return parts[1] if len(parts) == 2 else ''
	parts = modifier_data.split(';', 2)
	return parts[2] if len(parts) == 3 else ''


def weechat_print_cb(data, modifier, modifier_data, string):
	if not ENABLED:
		return string

	tags = get_tags_from_modifier_data(modifier_data)
	if 'irc_privmsg' not in tags:
		return string

	if '\t' not in string:
		return string

	prefix, msg = string.split('\t', 1)
	msg_plain = weechat.string_remove_color(msg, '')

	if count_forbidden_unicode(msg_plain) >= THRESHOLD:
		return prefix + '\t' + warning_text()

	return string


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, '', ''):
	weechat.hook_modifier('weechat_print', 'weechat_print_cb', '')
	weechat.hook_command('utf8spam', 'Toggle utf8spam on/off or set threshold', '[n]', '', '', 'utf8spam_cmd_cb', '')