# pump.py - /pump <name> sends ircart from git.supernets.org/ircart/ircart to the current buffer
import random
import weechat

SCRIPT_NAME = 'pump'
BASE = 'https://git.supernets.org/ircart/ircart/raw/branch/master/ircart'
EXCLUDE = ('big', 'birds', 'doc', 'gorf', 'hang', 'nazi', 'pokemon')

weechat.register(SCRIPT_NAME, 'acidvegas', '1.0', 'MIT', 'pump ircart into channel', '', '')

jobs = {}


def fetch(url, cb, data):
	jobs[data] = ''
	weechat.hook_process('url:' + url, 30000, cb, data)


def pick_random(query, paths):
	if not query:
		pool = [p for p in paths if '/' not in p or p.split('/', 1)[0] not in EXCLUDE]
	elif any(p.startswith(query + '/') for p in paths):
		pool = [p for p in paths if p.startswith(query + '/')]
	else:
		pool = [p for p in paths if query.lower() in p.rsplit('/', 1)[-1].lower()]
	return random.choice(pool) if pool else None


def resolve(name, listing):
	if name == 'random' or name.startswith('random '):
		return pick_random(name[6:].strip(), [p.strip() for p in listing.splitlines() if p.strip()])
	exact = first = None
	for path in listing.splitlines():
		path = path.strip()
		if path == name:
			exact = path
		if first is None and path.rsplit('/', 1)[-1] == name:
			first = path
	return exact or first


def list_cb(data, command, rc, out, err):
	jobs[data] += out
	if rc == weechat.WEECHAT_HOOK_PROCESS_RUNNING:
		return weechat.WEECHAT_RC_OK
	listing = jobs.pop(data)
	buffer, name = data.split(' ', 1)
	if name.startswith('search '):
		search(buffer, name[7:].strip(), listing)
		return weechat.WEECHAT_RC_OK
	path = resolve(name, listing)
	if not path:
		weechat.prnt(buffer, '%spump: no art named \'%s\'' % (weechat.prefix('error'), name))
		return weechat.WEECHAT_RC_OK
	fetch('%s/%s.txt' % (BASE, path), 'art_cb', buffer + ' ' + path)
	return weechat.WEECHAT_RC_OK


def art_cb(data, command, rc, out, err):
	jobs[data] += out
	if rc == weechat.WEECHAT_HOOK_PROCESS_RUNNING:
		return weechat.WEECHAT_RC_OK
	art = jobs.pop(data)
	buffer, path = data.split(' ', 1)
	if rc != 0 or not art:
		weechat.prnt(buffer, '%spump: failed to fetch %s' % (weechat.prefix('error'), path))
		return weechat.WEECHAT_RC_OK
	for line in art.replace('\r', '').splitlines():
		weechat.command(buffer, '/msg * \x0f' + line + '\x0f')
	weechat.prnt(buffer, 'the ascii gods have chosen... %s%s' % (weechat.color('cyan'), path))
	return weechat.WEECHAT_RC_OK


def search(buffer, query, listing):
	results = [p.strip() for p in listing.splitlines() if query.lower() in p.strip().rsplit('/', 1)[-1].lower()]
	if not results:
		weechat.prnt(buffer, '%spump: no results found (%s)' % (weechat.prefix('error'), query))
	for i, path in enumerate(results[:10], 1):
		dir, _, name = path.rpartition('/')
		weechat.prnt(buffer, '[%s%02d%s] %s%s' % (weechat.color('lightmagenta'), i, weechat.color('reset'), name, ' %s(%s)' % (weechat.color('darkgray'), dir) if dir else ''))


def pump_cmd(data, buffer, args):
	name = args.strip()
	if not name:
		weechat.prnt(buffer, '%spump: usage: /pump <name>' % weechat.prefix('error'))
		return weechat.WEECHAT_RC_OK
	fetch(BASE + '/.list', 'list_cb', buffer + ' ' + name)
	return weechat.WEECHAT_RC_OK


weechat.hook_command('pump', 'send ircart to the current channel', '<name> || random [<dir>|<word>] || search <word>', 'name: art name, e.g. e (plays reaction/e)\nrandom: random art, from <dir> if given, else with <word> in its name\nsearch: list up to 10 art names containing <word>','', 'pump_cmd', '')
