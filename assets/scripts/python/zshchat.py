# -*- coding: utf-8 -*-
#
# autosuggest.py - ZSH-style ghost hint autosuggestions for WeeChat
#
# Usage:
#   /script load autosuggest.py
#   Press Tab or Right Arrow to accept suggestion
#
# Options:
#   /set plugins.var.python.autosuggest.color 'darkgray'
#   /set plugins.var.python.autosuggest.use_history 'on'
#   /set plugins.var.python.autosuggest.max_history '1000'
#
# Author: acidvegas
# License: ISC

import weechat

SCRIPT_NAME = 'autosuggest'
SCRIPT_AUTHOR = 'acidvegas'
SCRIPT_VERSION = '1.0'
SCRIPT_LICENSE = 'ISC'
SCRIPT_DESC = 'ZSH-style ghost hint autosuggestions for commands'

# Global state
command_db = {}  # {command_name: {'args': str, 'description': str}}
history_commands = []  # List of previously used commands with args
current_suggestion = ''
hooks = []

# Default settings
settings = {
    'color': ('darkgray', 'Color for the ghost hint suggestion'),
    'use_history': ('on', 'Use command history for suggestions'),
    'max_history': ('1000', 'Maximum history entries to track'),
    'accept_key': ('right', 'Key to accept suggestion (right, tab, or both)'),
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


def build_command_database():
    '''Build database of all available commands with their arguments.'''
    global command_db
    command_db = {}

    # Get all hooks (commands are registered as hooks)
    infolist = weechat.infolist_get('hook', '', 'command')
    if infolist:
        while weechat.infolist_next(infolist):
            cmd = weechat.infolist_string(infolist, 'command')
            args = weechat.infolist_string(infolist, 'args')
            desc = weechat.infolist_string(infolist, 'description')
            if cmd:
                command_db['/' + cmd] = {
                    'args': args if args else '',
                    'description': desc if desc else ''
                }
        weechat.infolist_free(infolist)

    return len(command_db)


def add_to_history(command_line):
    '''Add a command to our history tracking.'''
    global history_commands

    if not command_line or not command_line.startswith('/'):
        return

    # Don't add if it's the same as the last entry
    if history_commands and history_commands[-1] == command_line:
        return

    history_commands.append(command_line)

    # Trim history if needed
    max_hist = int(config_get('max_history') or '1000')
    if len(history_commands) > max_hist:
        history_commands = history_commands[-max_hist:]


def find_suggestion(input_text):
    '''Find a suggestion for the current input.'''
    if not input_text:
        return ''

    # Only suggest for commands (starting with /)
    if not input_text.startswith('/'):
        return ''

    suggestion = ''

    # First, check history if enabled
    if config_get('use_history') == 'on':
        # Search history in reverse (most recent first)
        for hist_cmd in reversed(history_commands):
            if hist_cmd.startswith(input_text) and hist_cmd != input_text:
                suggestion = hist_cmd[len(input_text):]
                break

    # If no history match, try to suggest from command database
    if not suggestion:
        # Extract the command part (first word)
        parts = input_text.split(' ', 1)
        cmd_part = parts[0].lower()
        has_space = len(parts) > 1 or input_text.endswith(' ')
        
        if not has_space:
            # User is still typing the command name - suggest command completion
            for cmd in sorted(command_db.keys()):
                if cmd.lower().startswith(cmd_part) and cmd.lower() != cmd_part:
                    # Suggest the rest of the command name
                    suggestion = cmd[len(cmd_part):]
                    # Also add a hint about arguments
                    if cmd in command_db and command_db[cmd]['args']:
                        args = command_db[cmd]['args']
                        # Show just first line of args as hint
                        first_line = args.split('\n')[0]
                        if first_line:
                            suggestion += ' ' + first_line
                    break
        else:
            # User has typed a command and space - suggest arguments
            cmd_name = cmd_part
            # Find matching command (case insensitive)
            matched_cmd = None
            for cmd in command_db.keys():
                if cmd.lower() == cmd_name:
                    matched_cmd = cmd
                    break
            
            if matched_cmd and command_db[matched_cmd]['args']:
                args_typed = parts[1] if len(parts) > 1 else ''
                full_args = command_db[matched_cmd]['args']
                # Show argument template
                first_line = full_args.split('\n')[0]
                if first_line and not args_typed:
                    suggestion = first_line
    
    return suggestion


def bar_item_suggestion_cb(data, item, window):
    '''Callback for the suggestion bar item.'''
    global current_suggestion
    
    if not current_suggestion:
        return ''
    
    color = config_get('color') or 'darkgray'
    return weechat.color(color) + current_suggestion


def signal_input_text_changed_cb(data, signal, signal_data):
    '''Called when input text changes.'''
    global current_suggestion
    
    buffer = signal_data if signal_data else weechat.current_buffer()
    if not buffer:
        return weechat.WEECHAT_RC_OK
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    current_suggestion = find_suggestion(input_text)
    
    # Update the bar item
    weechat.bar_item_update('autosuggest')
    
    return weechat.WEECHAT_RC_OK


def signal_input_return_cb(data, signal, signal_data):
    '''Called when user presses Enter - track command in history.'''
    buffer = signal_data if signal_data else weechat.current_buffer()
    if not buffer:
        return weechat.WEECHAT_RC_OK
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    if input_text.startswith('/'):
        add_to_history(input_text)
    
    return weechat.WEECHAT_RC_OK


def accept_suggestion(buffer):
    '''Accept the current suggestion.'''
    global current_suggestion
    
    if not current_suggestion:
        return False
    
    input_text = weechat.buffer_get_string(buffer, 'input')
    new_input = input_text + current_suggestion
    
    # Set the new input
    weechat.buffer_set(buffer, 'input', new_input)
    # Move cursor to end
    weechat.buffer_set(buffer, 'input_pos', str(len(new_input)))
    
    current_suggestion = ''
    weechat.bar_item_update('autosuggest')
    
    return True


def command_run_input_cb(data, buffer, command):
    '''Intercept input commands to handle suggestion acceptance.'''
    global current_suggestion
    
    accept_key = config_get('accept_key') or 'right'
    
    # Check if this is a key we should intercept for accepting suggestions
    if current_suggestion:
        if command == '/input move_next_char' and accept_key in ('right', 'both'):
            # Right arrow pressed - accept suggestion
            input_text = weechat.buffer_get_string(buffer, 'input')
            input_pos = weechat.buffer_get_integer(buffer, 'input_pos')
            
            # Only accept if cursor is at end of input
            if input_pos >= len(input_text):
                if accept_suggestion(buffer):
                    return weechat.WEECHAT_RC_OK_EAT
        
        elif command == '/input complete_next' and accept_key in ('tab', 'both'):
            # Tab pressed - accept suggestion
            if accept_suggestion(buffer):
                return weechat.WEECHAT_RC_OK_EAT
    
    return weechat.WEECHAT_RC_OK


def command_autosuggest_cb(data, buffer, args):
    '''Handle /autosuggest command.'''
    global command_db, history_commands
    
    args_list = args.split()
    
    if not args_list or args_list[0] == 'status':
        weechat.prnt('', '')
        weechat.prnt('', 'autosuggest: %d commands in database' % len(command_db))
        weechat.prnt('', 'autosuggest: %d commands in history' % len(history_commands))
        weechat.prnt('', 'autosuggest: color = %s' % config_get('color'))
        weechat.prnt('', 'autosuggest: use_history = %s' % config_get('use_history'))
        weechat.prnt('', 'autosuggest: accept_key = %s' % config_get('accept_key'))
        return weechat.WEECHAT_RC_OK
    
    elif args_list[0] == 'reload':
        count = build_command_database()
        weechat.prnt('', 'autosuggest: reloaded %d commands' % count)
        return weechat.WEECHAT_RC_OK
    
    elif args_list[0] == 'clear':
        history_commands = []
        weechat.prnt('', 'autosuggest: history cleared')
        return weechat.WEECHAT_RC_OK
    
    elif args_list[0] == 'list':
        weechat.prnt('', '')
        weechat.prnt('', 'autosuggest: Available commands:')
        for cmd in sorted(command_db.keys())[:50]:
            args_hint = command_db[cmd]['args'].split('\n')[0][:50] if command_db[cmd]['args'] else ''
            weechat.prnt('', '  %s %s' % (cmd, args_hint))
        if len(command_db) > 50:
            weechat.prnt('', '  ... and %d more (use /autosuggest list all)' % (len(command_db) - 50))
        return weechat.WEECHAT_RC_OK
    
    elif args_list[0] == 'history':
        weechat.prnt('', '')
        weechat.prnt('', 'autosuggest: Recent command history:')
        for cmd in history_commands[-20:]:
            weechat.prnt('', '  %s' % cmd)
        return weechat.WEECHAT_RC_OK
    
    return weechat.WEECHAT_RC_OK


def unload_cb():
    '''Called when script is unloaded.'''
    global hooks
    for hook in hooks:
        weechat.unhook(hook)
    return weechat.WEECHAT_RC_OK


# Main entry point
if __name__ == '__main__':
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                        SCRIPT_LICENSE, SCRIPT_DESC, 'unload_cb', ''):
        
        # Initialize config
        config_init()
        
        # Build command database
        count = build_command_database()
        
        # Create bar item for suggestion display
        weechat.bar_item_new('autosuggest', 'bar_item_suggestion_cb', '')
        
        # Hook signals
        hooks.append(weechat.hook_signal('input_text_changed', 
                                          'signal_input_text_changed_cb', ''))
        hooks.append(weechat.hook_signal('input_return',
                                          'signal_input_return_cb', ''))
        
        # Hook command runs to intercept Tab/Right arrow
        hooks.append(weechat.hook_command_run('/input *',
                                               'command_run_input_cb', ''))
        
        # Register our command
        weechat.hook_command(
            'autosuggest',
            'Manage autosuggest plugin',
            'status | reload | clear | list | history',
            '  status: show current status\n'
            '  reload: reload command database\n'
            '   clear: clear command history\n'
            '    list: list known commands\n'
            ' history: show recent command history\n'
            '\n'
            'The suggestion appears as a ghost hint after your cursor.\n'
            'Press Right arrow (or Tab) to accept the suggestion.\n'
            '\n'
            'Add the \'autosuggest\' bar item to your input bar:\n'
            '  /set weechat.bar.input.items \'[input_prompt]+(away),[input_search],'
            '[input_paste],input_text,autosuggest\'\n',
            'status || reload || clear || list || history',
            'command_autosuggest_cb',
            ''
        )

        weechat.prnt('', '%s %s loaded - %d commands indexed' % 
                     (SCRIPT_NAME, SCRIPT_VERSION, count))
        weechat.prnt('', 'Add bar item with: /set weechat.bar.input.items '
                     '\'[input_prompt]+(away),[input_search],[input_paste],'
                     'input_text,autosuggest\'')
