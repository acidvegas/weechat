# Random Spaces Weechat Script - Developed by Acidvegas in Python (https://git.acid.vegas/weechat)

import weechat
import random

def cmd_rdsp(data, buf, args):
    num_spaces = random.randint(1, 100)
	weechat.command(buf, '/input send \x03' + ' '*num_spaces + args)
    return weechat.WEECHAT_RC_OK

if weechat.register('rdsp', 'acidvegas', '1.0', 'ISC', 'prefix a message with random spaces', '', ''):
    weechat.hook_command('rdsp', 'Generate random spaces', '', '', '', 'cmd_rdsp', '')
