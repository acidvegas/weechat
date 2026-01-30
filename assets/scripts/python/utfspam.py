# -*- coding: utf-8 -*-
#
# utf8spam.py — WeeChat filter for UTF-8 spam”
#
# Commands:
#   /utf8spam on
#   /utf8spam off
#   /utf8spam toggle
#   /utf8spam threshold <n>
#   /utf8spam status

import weechat

SCRIPT_NAME    = "utf8spam"
SCRIPT_AUTHOR  = "acidvegas"
SCRIPT_VERSION = "1.4"
SCRIPT_LICENSE = "ISC"
SCRIPT_DESC    = "Detect U+1000..U+3000 unicode spam bursts in IRC PRIVMSG"

DEFAULT_ENABLED   = "on"
DEFAULT_THRESHOLD = "20"

def cfg_enabled():
    v = weechat.config_get_plugin("enabled") or DEFAULT_ENABLED
    return v.strip().lower() in ("1", "on", "true", "yes", "enabled")

def cfg_threshold():
    v = weechat.config_get_plugin("threshold") or DEFAULT_THRESHOLD
    try:
        return max(1, int(v))
    except Exception:
        return int(DEFAULT_THRESHOLD)

def set_enabled(on):
    weechat.config_set_plugin("enabled", "on" if on else "off")

def set_threshold(n):
    weechat.config_set_plugin("threshold", str(max(1, int(n))))

def warning_mirc_codes():
    # Bold + white-on-red + padded spaces + reset (mIRC formatting codes)
    # fg white=00, bg red=04
    return "\x02\x0300,04  UNICODE SPAM DETECTED  \x0F"

def has_1000_3000_run(msg, threshold):
    run = 0
    for ch in msg:
        o = ord(ch)
        if 0x1000 <= o <= 0x3000:
            run += 1
            if run >= threshold:
                return True
        else:
            run = 0
    return False

def replace_text_preserving_action(text):
    # Preserve CTCP ACTION framing if present
    if text.startswith("\x01ACTION ") and text.endswith("\x01"):
        return "\x01ACTION " + warning_mirc_codes() + "\x01"
    return warning_mirc_codes()

def filter_privmsg_raw_line(raw):
    # Only act on PRIVMSG lines
    if " PRIVMSG " not in raw:
        return raw

    # The message text is always after the LAST " :"
    # This avoids breaking lines that also contain " :" earlier (e.g., tags + prefix).
    if " :" not in raw:
        return raw

    head, text = raw.rsplit(" :", 1)

    if not text:
        return raw

    if has_1000_3000_run(text, cfg_threshold()):
        return head + " :" + replace_text_preserving_action(text)

    return raw

def irc_in2_privmsg_cb(data, modifier, modifier_data, string):
    if not cfg_enabled():
        return string
    return filter_privmsg_raw_line(string)

def irc_in_privmsg_cb(data, modifier, modifier_data, string):
    if not cfg_enabled():
        return string
    return filter_privmsg_raw_line(string)

def cmd_utf8spam_cb(data, buf, args):
    argv = args.strip().split()
    cmd = (argv[0].lower() if argv else "status")

    if cmd in ("on", "enable", "enabled"):
        set_enabled(True)
        weechat.prnt(buf, "utf8spam: enabled")
    elif cmd in ("off", "disable", "disabled"):
        set_enabled(False)
        weechat.prnt(buf, "utf8spam: disabled")
    elif cmd == "toggle":
        set_enabled(not cfg_enabled())
        weechat.prnt(buf, "utf8spam: {}".format("enabled" if cfg_enabled() else "disabled"))
    elif cmd == "threshold" and len(argv) >= 2:
        try:
            set_threshold(int(argv[1]))
            weechat.prnt(buf, "utf8spam: threshold={}".format(cfg_threshold()))
        except Exception:
            weechat.prnt(buf, "utf8spam: invalid threshold")
    elif cmd == "status":
        weechat.prnt(buf, "utf8spam: {} threshold={}".format(
            "enabled" if cfg_enabled() else "disabled",
            cfg_threshold()
        ))
    else:
        weechat.prnt(buf, "Usage: /utf8spam on|off|toggle|status|threshold <n>")

    return weechat.WEECHAT_RC_OK

def setup_defaults():
    if not weechat.config_get_plugin("enabled"):
        weechat.config_set_plugin("enabled", DEFAULT_ENABLED)
    if not weechat.config_get_plugin("threshold"):
        weechat.config_set_plugin("threshold", DEFAULT_THRESHOLD)

if __name__ == "__main__":
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
        setup_defaults()
        weechat.hook_modifier("irc_in2_privmsg", "irc_in2_privmsg_cb", "")
        weechat.hook_modifier("irc_in_privmsg",  "irc_in_privmsg_cb",  "")
        weechat.hook_command(
            "utf8spam",
            "Replace messages containing long U+1000..U+3000 bursts with a warning.",
            "on | off | toggle | status | threshold <n>",
            "Examples:\n"
            "  /utf8spam on\n"
            "  /utf8spam threshold 20\n"
            "  /utf8spam off\n",
            "on|off|toggle|status|threshold",
            "cmd_utf8spam_cb",
            ""
        )