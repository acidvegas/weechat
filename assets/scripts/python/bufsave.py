# -*- coding: utf-8 -*-
# bufsave script for weechat - developed by acidvegas (https://git.acid.vegas/weechat)
# usage: /bufsave saves current buffer to a $HOME/.weechats/logs/

import time
import weechat

def cstrip(text):
	return weechat.string_remove_color(text, '')

def bufsave_cmd(data, buffer, args):
	filename = weechat.buffer_get_string(buffer, 'localvar_server') + '.' + weechat.buffer_get_string(buffer, 'localvar_channel') + '-' + time.strftime('%y_%m_%d-%I_%M_%S') + '.log'
	filename = weechat.string_eval_path_home('%h/logs/' + filename, {}, {}, {})
	try:
		fp = open(filename, 'w')
	except:
		weechat.prnt('', 'Error writing to target file!')
		return weechat.WEECHAT_RC_OK
	own_lines = weechat.hdata_pointer(weechat.hdata_get('buffer'), buffer, 'own_lines')
	if own_lines:
		line = weechat.hdata_pointer(weechat.hdata_get('lines'), own_lines, 'first_line')
		hdata_line = weechat.hdata_get('line')
		hdata_line_data = weechat.hdata_get('line_data')
		while line:
			data = weechat.hdata_pointer(hdata_line, line, 'data')
			if data:
				date = weechat.hdata_time(hdata_line_data, data, 'date')
				if not isinstance(date, str):
					date = time.strftime('%F %T', time.localtime(int(date)))
				fp.write('{0} {1} {2}\n'.format(date, cstrip(weechat.hdata_string(hdata_line_data, data, 'prefix')), cstrip(weechat.hdata_string(hdata_line_data, data, 'message'))))
			line = weechat.hdata_move(hdata_line, line, 1)
	fp.close()
	return weechat.WEECHAT_RC_OK

if weechat.register('bufsave', 'acidvegas', '1.0', 'ISC', 'save buffer to file', '', ''):
	weechat.hook_command('bufsave', 'save current buffer to a file', '[filename]', 'filename: target file (must not exist)\n', '%f', 'bufsave_cmd', '')