
# -*- coding: utf-8 -*-
#
# protectops.py — ISC
#
# /protectops        -> sets +e and +I using ONLY ~a:account for % and higher
# /protectops lock   -> same, plus runs ChanServ "mode lock" commands (configurable)
#
# Author: acidvegas
# License: ISC

import weechat

SCRIPT_NAME    = "protectops"
SCRIPT_AUTHOR  = "acidvegas"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "ISC"
SCRIPT_DESC    = "Protect ops/halfops by setting +e/+I ~a:account (optional ChanServ lock)"

DEFAULTS = {
    # These vary by services package; edit as needed:
    "lock_cmd_e": "/msg ChanServ MODE {chan} LOCK ADD +e {mask}",
    "lock_cmd_I": "/msg ChanServ MODE {chan} LOCK ADD +I {mask}",
}

def cfg(k): return weechat.config_get_plugin(k)
def run(buf, s): weechat.command(buf, s)

def cb(data, buf, args):
    server = weechat.buffer_get_string(buf, "localvar_server")
    chan   = weechat.buffer_get_string(buf, "localvar_channel")
    if not server or not chan or not chan.startswith("#"):
        weechat.prnt(buf, "protectops: run in a channel buffer.")
        return weechat.WEECHAT_RC_OK

    want_lock = (args.strip().lower() == "lock")
    lock_e = cfg("lock_cmd_e") or DEFAULTS["lock_cmd_e"]
    lock_I = cfg("lock_cmd_I") or DEFAULTS["lock_cmd_I"]

    allowed = set(["%", "@", "&", "~"])  # halfop+ (common)
    seen = set()
    n = 0

    il = weechat.infolist_get("irc_nick", "", f"{server},{chan}")
    if not il:
        weechat.prnt(buf, "protectops: can't read irc_nick infolist.")
        return weechat.WEECHAT_RC_OK

    while weechat.infolist_next(il):
        prefix = (weechat.infolist_string(il, "prefix") or "")[:1]
        if prefix not in allowed:
            continue

        account = (weechat.infolist_string(il, "account") or "").strip()
        if not account:
            continue

        if account in seen:
            continue
        seen.add(account)

        mask = f"~a:{account}"
        run(buf, f"/mode {chan} +e {mask}")
        run(buf, f"/mode {chan} +I {mask}")

        if want_lock:
            run(buf, lock_e.format(chan=chan, mask=mask, account=account))
            run(buf, lock_I.format(chan=chan, mask=mask, account=account))

        n += 1

    weechat.infolist_free(il)
    weechat.prnt(buf, f"protectops: set +e/+I for {n} account(s){' + locked' if want_lock else ''}.")
    return weechat.WEECHAT_RC_OK

def setup():
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    for k, v in DEFAULTS.items():
        if not weechat.config_is_set_plugin(k):
            weechat.config_set_plugin(k, v)

    weechat.hook_command(
        "protectops",
        "Set +e/+I using ~a:account for % and higher in current channel; add 'lock' to ChanServ-lock",
        "[lock]",
        "Examples:\n"
        "  /protectops\n"
        "  /protectops lock\n\n"
        "Config:\n"
        "  /set plugins.var.python.protectops.lock_cmd_e ...\n"
        "  /set plugins.var.python.protectops.lock_cmd_I ...\n",
        "",
        "cb",
        "",
    )

if __name__ == "__main__":
    setup()
