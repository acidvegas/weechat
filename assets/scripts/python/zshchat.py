#!/usr/bin/env python3
# ZSH-style ghost hint autosuggestions for commands - developed by acidvegas in python (https://github.com/acidvegas/weechat)

import weechat
import re

SCRIPT_NAME    = 'autosuggest'
SCRIPT_AUTHOR  = 'acidvegas'
SCRIPT_VERSION = '1.2'
SCRIPT_LICENSE = 'ISC'
SCRIPT_DESC    = 'ZSH-style ghost hint autosuggestions for commands'

# Global state
current_suggestion = ''
command_history    = []
channel_history    = set()
hooks              = []

# Default settings
settings = {
    'color'       : ('240', 'Color for ghost hint'),
    'accept_key'  : ('right', 'Key to accept suggestion (right, tab, or both)'),
    'max_history' : ('5000', 'Maximum command history entries'),
}


def config_get(option):
    '''Get a config option value.'''
    return weechat.config_get_plugin(option)


def config_init():
    '''Initialize configuration options.'''
    for option, (default, description) in settings.items():
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, default)
        weechat.config_set_desc_plugin(option, description)


def add_to_history(cmd):
    '''Add command to history (no duplicates).'''
    global command_history, channel_history
    
    if not cmd or not cmd.startswith('/'):
        return
    
    # Remove if exists (will re-add at end)
    if cmd in command_history:
        command_history.remove(cmd)
    
    command_history.append(cmd)
    
    # Extract channels
    channels = re.findall(r'(#[^\s,]+)', cmd)
    for chan in channels:
        channel_history.add(chan)
    
    # Trim if needed
    max_hist = int(config_get('max_history') or '5000')
    if len(command_history) > max_hist:
        command_history = command_history[-max_hist:]


def get_aliases():
    '''Get all defined aliases.'''
    aliases = {}
    infolist = weechat.infolist_get('alias', '', '')
    if infolist:
        while weechat.infolist_next(infolist):
            name = weechat.infolist_string(infolist, 'name')
            command = weechat.infolist_string(infolist, 'command')
            if name:
                aliases['/' + name] = command
        weechat.infolist_free(infolist)
    return aliases


def get_weechat_commands():
    '''Get core weechat commands.'''
    commands = {}
    infolist = weechat.infolist_get('hook', '', 'command')
    if infolist:
        while weechat.infolist_next(infolist):
            cmd = weechat.infolist_string(infolist, 'command')
            args = weechat.infolist_string(infolist, 'args')
            if cmd:
                commands['/' + cmd] = args if args else ''
        weechat.infolist_free(infolist)
    return commands


def get_buffer_nicks(buffer):
    '''Get list of nicks in the current buffer.'''
    nicks = []
    infolist = weechat.infolist_get('nicklist', buffer, '')
    if infolist:
        while weechat.infolist_next(infolist):
            nick_type = weechat.infolist_string(infolist, 'type')
            if nick_type == 'nick':
                nick = weechat.infolist_string(infolist, 'name')
                if nick:
                    nicks.append(nick)
        weechat.infolist_free(infolist)
    return nicks


def get_servers():
    '''Get list of configured IRC servers.'''
    servers = []
    infolist = weechat.infolist_get('irc_server', '', '')
    if infolist:
        while weechat.infolist_next(infolist):
            name = weechat.infolist_string(infolist, 'name')
            if name:
                servers.append(name)
        weechat.infolist_free(infolist)
    return servers


def get_channels():
    '''Get list of channels we are currently in.'''
    channels = set()
    infolist = weechat.infolist_get('irc_channel', '', '')
    if infolist:
        while weechat.infolist_next(infolist):
            name = weechat.infolist_string(infolist, 'name')
            if name:
                channels.add(name)
        weechat.infolist_free(infolist)
    return channels


def get_all_channels():
    '''Get all known channels (current + history).'''
    channels = get_channels()
    channels.update(channel_history)
    return channels


def suggest_nick(buffer, partial):
    '''Suggest a nick based on partial input.'''
    buffer_type = weechat.buffer_get_string(buffer, 'localvar_type')
    if buffer_type != 'channel':
        return ''
    
    nicks = get_buffer_nicks(buffer)
    partial_lower = partial.lower()
    for nick in sorted(nicks, key=str.lower):
        if nick.lower().startswith(partial_lower) and nick.lower() != partial_lower:
            return nick[len(partial):]
    return ''


def suggest_channel(partial):
    '''Suggest a channel based on partial input.'''
    all_channels = get_all_channels()
    partial_lower = partial.lower()
    for chan in sorted(all_channels, key=str.lower):
        if chan.lower().startswith(partial_lower) and chan.lower() != partial_lower:
            return chan[len(partial):]
    return ''


def suggest_server(partial):
    '''Suggest a server based on partial input.'''
    servers = get_servers()
    partial_lower = partial.lower()
    for server in sorted(servers, key=str.lower):
        if server.lower().startswith(partial_lower) and server.lower() != partial_lower:
            return server[len(partial):]
    return ''


def find_suggestion(input_text, buffer):
    '''Find a suggestion for the current input.'''
    if not input_text or not input_text.startswith('/'):
        return ''
    
    # Check history first (most recent match)
    input_lower = input_text.lower()
    for cmd in reversed(command_history):
        if cmd.lower().startswith(input_lower) and cmd.lower() != input_lower:
            return cmd[len(input_text):]
    
    # Split into command and args
    parts = input_text.split(' ', 1)
    cmd_part = parts[0]
    has_args = len(parts) > 1
    args_part = parts[1] if has_args else ''
    
    # If still typing the command (no space yet)
    if not has_args and not input_text.endswith(' '):
        cmd_lower = cmd_part.lower()
        
        # Check aliases first
        aliases = get_aliases()
        for alias in sorted(aliases.keys()):
            if alias.lower().startswith(cmd_lower) and alias.lower() != cmd_lower:
                return alias[len(cmd_part):]
        
        # Check weechat commands
        commands = get_weechat_commands()
        for cmd in sorted(commands.keys()):
            if cmd.lower().startswith(cmd_lower) and cmd.lower() != cmd_lower:
                return cmd[len(cmd_part):]
    
    # If we have a command and are typing args
    elif has_args or input_text.endswith(' '):
        cmd_lower = cmd_part.lower()
        
        # Get the last word being typed in args
        if args_part:
            words = args_part.split(' ')
            last_word = words[-1]
        else:
            last_word = ''
        
        # Commands that take a nick as argument
        nick_commands = ['/msg', '/query', '/whois', '/whowas', '/notice',
                        '/kick', '/ban', '/unban', '/op', '/deop', '/halfop',
                        '/dehalfop', '/voice', '/devoice', '/kickban', '/ignore',
                        '/unignore', '/dcc', '/ctcp']
        
        # Commands that take a channel as argument
        channel_commands = ['/join', '/part', '/topic', '/mode', '/invite',
                          '/kick', '/kickban', '/names', '/who', '/msg', '/query']
        
        # Commands that take a server as argument
        server_commands = ['/connect', '/disconnect', '/reconnect', '/server']
        
        # Check if this is an alias - if so, treat args as potentially nick/channel
        aliases = get_aliases()
        is_alias = cmd_part in aliases or cmd_part.lower() in [a.lower() for a in aliases]
        
        # Suggest channel if typing #
        if last_word.startswith('#'):
            suggestion = suggest_channel(last_word)
            if suggestion:
                return suggestion
        
        # For aliases or nick commands, suggest nick
        elif (is_alias or cmd_lower in nick_commands) and last_word and not last_word.startswith('#'):
            suggestion = suggest_nick(buffer, last_word)
            if suggestion:
                return suggestion
        
        # For channel commands with no arg yet, suggest first channel
        elif cmd_lower in channel_commands and not last_word:
            all_channels = get_all_channels()
            if all_channels:
                return sorted(all_channels)[0]
        
        # For aliases with no arg yet, try nick suggestion
        elif is_alias and not last_word:
            buffer_type = weechat.buffer_get_string(buffer, 'localvar_type')
            if buffer_type == 'channel':
                nicks = get_buffer_nicks(buffer)
                if nicks:
                    return sorted(nicks, key=str.lower)[0]
        
        # Suggest server
        elif cmd_lower in server_commands:
            if last_word:
                suggestion = suggest_server(last_word)
                if suggestion:
                    return suggestion
            else:
                servers = get_servers()
                if servers:
                    return servers[0]
    
    return ''


def bar_item_suggestion_cb(data, item, window):
    '''Callback for the suggestion bar item.'''
    global current_suggestion
    
    if not current_suggestion:
        return ''
    
    color = config_get('color') or '240'
    return weechat.color(color) + current_suggestion


def signal_input_text_changed_cb(data, signal, signal_data):
    '''Called when input text changes.'''
    global current_suggestion
    
    buffer = signal_data if signal_data else weechat.current_buffer()
    if not buffer:
        return weechat.WEECHAT_RC_OK
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    current_suggestion = find_suggestion(input_text, buffer)
    
    weechat.bar_item_update('autosuggest')
    
    return weechat.WEECHAT_RC_OK


def signal_input_return_cb(data, signal, signal_data):
    '''Called when user presses Enter.'''
    buffer = signal_data if signal_data else weechat.current_buffer()
    if not buffer:
        return weechat.WEECHAT_RC_OK
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    add_to_history(input_text)
    
    return weechat.WEECHAT_RC_OK


def accept_suggestion(buffer):
    '''Accept the current suggestion.'''
    global current_suggestion
    
    if not current_suggestion:
        return False
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    new_input = input_text + current_suggestion
    
    weechat.buffer_set(buffer, 'input', new_input)
    weechat.buffer_set(buffer, 'input_pos', str(len(new_input)))
    
    current_suggestion = ''
    weechat.bar_item_update('autosuggest')
    
    return True


def command_run_input_cb(data, buffer, command):
    '''Intercept input commands to handle suggestion acceptance.'''
    global current_suggestion
    
    accept_key = config_get('accept_key') or 'right'
    
    if current_suggestion:
        if command == '/input move_next_char' and accept_key in ('right', 'both'):
            input_text = weechat.buffer_get_string(buffer, 'input')
            input_pos = weechat.buffer_get_integer(buffer, 'input_pos')
            
            if input_pos >= len(input_text):
                if accept_suggestion(buffer):
                    return weechat.WEECHAT_RC_OK_EAT
        
        elif command == '/input complete_next' and accept_key in ('tab', 'both'):
            if accept_suggestion(buffer):
                return weechat.WEECHAT_RC_OK_EAT
    
    return weechat.WEECHAT_RC_OK


def command_autosuggest_cb(data, buffer, args):
    '''Handle /autosuggest command.'''
    global command_history, channel_history
    
    args_list = args.split()
    
    if not args_list or args_list[0] == 'status':
        weechat.prnt('', '')
        weechat.prnt('', 'autosuggest status:')
        weechat.prnt('', '  color: %s' % config_get('color'))
        weechat.prnt('', '  accept_key: %s' % config_get('accept_key'))
        weechat.prnt('', '  max_history: %s' % config_get('max_history'))
        weechat.prnt('', '  history entries: %d' % len(command_history))
        weechat.prnt('', '  channels known: %d' % len(get_all_channels()))
        weechat.prnt('', '  aliases: %d' % len(get_aliases()))
        weechat.prnt('', '  commands: %d' % len(get_weechat_commands()))
        weechat.prnt('', '  servers: %d' % len(get_servers()))
        return weechat.WEECHAT_RC_OK
    
    elif args_list[0] == 'clear':
        command_history = []
        channel_history = set()
        weechat.prnt('', 'autosuggest: history cleared')
        return weechat.WEECHAT_RC_OK
    
    return weechat.WEECHAT_RC_OK


def unload_cb():
    '''Called when script is unloaded.'''
    return weechat.WEECHAT_RC_OK


if __name__ == '__main__':
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                        SCRIPT_LICENSE, SCRIPT_DESC, 'unload_cb', ''):
        
        config_init()
        
        weechat.bar_item_new('autosuggest', 'bar_item_suggestion_cb', '')
        
        hooks.append(weechat.hook_signal('input_text_changed',
                                          'signal_input_text_changed_cb', ''))
        hooks.append(weechat.hook_signal('input_return',
                                          'signal_input_return_cb', ''))
        
        hooks.append(weechat.hook_command_run('/input *',
                                               'command_run_input_cb', ''))
        
        weechat.hook_command(
            'autosuggest',
            'Autosuggest management',
            '[status|clear]',
            'status: show current status\n'
            ' clear: clear all history',
            'status || clear',
            'command_autosuggest_cb',
            ''
        )
        
        weechat.prnt('', '%s %s loaded' % (SCRIPT_NAME, SCRIPT_VERSION))
        weechat.prnt('', 'Setup: /set weechat.bar.input.items '
                     '\'[input_prompt]+(away),[input_search],[input_paste],'
                     'input_text,autosuggest\'')