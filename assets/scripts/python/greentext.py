# -*- coding: utf-8 -*-
# greentext script for weechat - developed by acidvegas in python (https://git.acid.vegas/weechat)

'''
Todo: this can be turned into a trigger
'''

import re,weechat

def between(source, start, stop):
	data = re.compile(start + '(.*?)' + stop, re.IGNORECASE|re.MULTILINE).search(source)
	if data:
		return data.group(1)
	else:
		return False

def cb_greentext(data,buffer,command):
	if command=='/input return':
		data=weechat.buffer_get_string(buffer,'input')
		if data:
			if data[0]=='>':
				data='\x0303'+data
			elif '!!' in data or '__' in data or '**' in data:
				for word in data.split():
					if word[:2] == '!!':
						data = data.replace(word, '\x1F\x02\x0304 ' + word[2:].upper() + ' \x0f', 1)
					elif word[:2] == '__':
						data = data.replace(word, '\x1F\x02' + word[2:].upper() + '\x0f', 1)
		weechat.buffer_set(buffer,'input',data)
	return weechat.WEECHAT_RC_OK

if weechat.register('greentext','','','','','',''):weechat.hook_command_run('/input return','cb_greentext','')