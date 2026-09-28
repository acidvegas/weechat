 # pump.py - /pump <name> sends ircart from git.supernets.org/ircart/ircart to the current buffer
  import weechat

  SCRIPT_NAME = "pump"
  BASE = "https://git.supernets.org/ircart/ircart/raw/branch/master/ircart"

  weechat.register(SCRIPT_NAME, "brandon", "1.0", "MIT", "pump ircart into channel", "", "")

  jobs = {}


  def fetch(url, cb, data):
      jobs[data] = ""
      weechat.hook_process("url:" + url, 30000, cb, data)


  def resolve(name, listing):
      exact = first = None
      for path in listing.splitlines():
          path = path.strip()
          if path == name:
              exact = path
          if first is None and path.rsplit("/", 1)[-1] == name:
              first = path
      return exact or first


  def list_cb(data, command, rc, out, err):
      jobs[data] += out
      if rc == weechat.WEECHAT_HOOK_PROCESS_RUNNING:
          return weechat.WEECHAT_RC_OK
      listing = jobs.pop(data)
      buffer, name = data.split(" ", 1)
      path = resolve(name, listing)
      if not path:
          weechat.prnt(buffer, "%spump: no art named '%s'" % (weechat.prefix("error"), name))
          return weechat.WEECHAT_RC_OK
      fetch("%s/%s.txt" % (BASE, path), "art_cb", buffer + " " + path)
      return weechat.WEECHAT_RC_OK


  def art_cb(data, command, rc, out, err):
      jobs[data] += out
      if rc == weechat.WEECHAT_HOOK_PROCESS_RUNNING:
          return weechat.WEECHAT_RC_OK
      art = jobs.pop(data)
      buffer, path = data.split(" ", 1)
      if rc != 0 or not art:
          weechat.prnt(buffer, "%spump: failed to fetch %s" % (weechat.prefix("error"), path))
          return weechat.WEECHAT_RC_OK
      for line in art.replace("\r", "").splitlines():
          weechat.command(buffer, "/msg * " + (line or " "))
      return weechat.WEECHAT_RC_OK


  def pump_cmd(data, buffer, args):
      name = args.strip()
      if not name:
          weechat.prnt(buffer, "%spump: usage: /pump <name>" % weechat.prefix("error"))
          return weechat.WEECHAT_RC_OK
      fetch(BASE + "/.list", "list_cb", buffer + " " + name)
      return weechat.WEECHAT_RC_OK


  weechat.hook_command("pump", "send ircart to the current channel", "<name>",
                       "name: art name, e.g. e (plays reaction/e)", "", "pump_cmd", "")
