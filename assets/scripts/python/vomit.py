# -*- coding: utf-8 -*-
# do some fake n fancy encryption shit - developed by wrk

import weechat
import random
import string
import time

def get_random_unicode():
	try:
		get_char = unichr
	except NameError:
		get_char = chr
	include_ranges = [
		( 0x0021, 0x0021 ),
		( 0x0023, 0x0026 ),
		( 0x0028, 0x007E ),
		( 0x00A1, 0x00AC ),
		( 0x00AE, 0x00FF ),
		( 0x0100, 0x017F ),
		( 0x0180, 0x024F ),
		( 0x2C60, 0x2C7F ),
		( 0x16A0, 0x16F0 ),
		( 0x0370, 0x0377 ),
		( 0x037A, 0x037E ),
		( 0x0384, 0x038A ),
		( 0x038C, 0x038C ),
	]
	alphabet = [
		get_char(code_point) for current_range in include_ranges
			for code_point in range(current_range[0], current_range[1] + 1)
	]
	return random.choice(alphabet)

def cmd_vomit(data, buf, msg):
	dec_bools = [False for _ in range(len(msg))]
	indices = list(range(len(msg)))
	random.shuffle(indices)
	while len(indices) > 0:
		idx = indices.pop()
		ret_str = ""
		is_dec = True
		for i in range(len(dec_bools)):
			if dec_bools[i]:
				if not is_dec:
					is_dec=True
					ret_str += "\x0f"
				ret_str += msg[i]
			else:
				if is_dec:
					is_dec=False
				ret_str += f"\x03{random.choice([3, 9]):02d}"
				ret_str += get_random_unicode()
		dec_bools[idx] = True
		weechat.command(buf, f'/input send {ret_str}')
		enc_str = ret_str
		time.sleep(0.1)
	weechat.command(buf, f'/input send {msg}')
	return weechat.WEECHAT_RC_OK

if weechat.register('vomit', 'wrk', '1.0', 'ISC', 'vomit text', '', ''):
	weechat.hook_command('vomit', 'vomit text', '<text>', '', '', 'cmd_vomit', '')