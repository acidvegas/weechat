# This script was made to improve upon keepnick.py

use strict;
use warnings;

no strict 'subs';

my $SCRIPT_NAME = 'keepnick';
my $SCRIPT_AUTHOR = 'The Krusty Krab <wowaname@volatile.ch>';
my $SCRIPT_VERSION = '1.0';
my $SCRIPT_LICENCE = 'Public domain';
my $SCRIPT_DESC = 'Keep your primary nickname';

our (%waiting, %connecting, %noison);

my %OPTIONS = (
	default_enable => ['Whether to enable keepnick on servers by default', '0'],
	check_time => ['Time between ISON checks (reload script to take effect)', '60'],
);


sub arrindex
{
	1 while $_[0] ne pop;
	return @_ - 1;
}

sub info
{
	weechat::print(weechat::buffer_search('irc', 'server.'.shift),
		weechat::prefix('server').shift);
}

sub my_nick
{	return lc weechat::info_get('irc_nick', shift); }

sub is_preferable
{
	my ($server, $target) = @_;
	my ($targidx, $myidx) = (
		arrindex($target, @{$waiting{$server}}),
		arrindex(my_nick($server), @{$waiting{$server}}));
	return ($myidx == -1 or $targidx < $myidx);
}

sub is_waiting
{
	my $server = lc shift;
	return exists $waiting{$server} ? @{ $waiting{$server} } : ();
}


sub disable
{	delete $waiting{lc shift}; }

sub enable
{
	my $server = shift;
	my $force = shift // 0;
	my @target = @_ ? split ',', shift : ();
	unless (@target) {
		my ($conf_nicks, $confd_nicks) = (
			weechat::config_get("irc.server.$server.nicks"),
			weechat::config_get("irc.server_default.nicks"));
		@target = split ',', weechat::config_string(
			weechat::config_option_is_null($conf_nicks)
			? $confd_nicks : $conf_nicks);
	}
	$server = lc $server;
	my ($defaultconf, $serverconf) = (
		weechat::config_get_plugin('default_enable'),
		weechat::config_get_plugin("server.$server"));
	unless ($force) {
		return () if $serverconf ne '' and !$serverconf;
		return () if $serverconf eq '' and !$defaultconf;
	}
	return () if lc $target[0] eq my_nick($server);

	$waiting{$server} = \@target;
	return @target;
}


sub do_nick
{
	my ($server, $nick) = @_;
	weechat::hook_signal_send('irc_input_send',
		weechat::WEECHAT_HOOK_SIGNAL_STRING,
		"$server;;;;/nick $nick");
	if (lc $waiting{$server}->[0] eq lc $nick) {
		# we're done if we have our primary nick choice, otherwise keep trying
		disable($server);
		info($server, "got your primary nick!");
	} else {
		info($server, "got one of your nicks; still trying for your primary nick");
	}
}

sub try_nick
{
	my ($server, $oldnick) = @_;
	($server, $oldnick) = (lc $server, lc $oldnick);
	my ($mynick, @confnick) = (my_nick($server), is_waiting($server));
	return unless @confnick;
	return unless is_preferable($server, $oldnick);

	if ($mynick eq $oldnick) { disable($server); }
	else { lc $_ eq $oldnick and do_nick($server, $_) for @confnick; }
}

sub ison_check
{
	my $iptr = weechat::infolist_get('irc_server', '', '');

	while (weechat::infolist_next($iptr)) {
		next unless weechat::infolist_integer($iptr, 'is_connected');
		my $server = lc weechat::infolist_string($iptr, 'name');
		next unless is_waiting($server);
		next unless exists $noison{$server};
		weechat::hook_hsignal_send('irc_redirect_command', {
			server => $server,
			pattern => 'ison',
			signal => $SCRIPT_NAME,
			timeout => weechat::config_get_plugin('check_time') - 1,
			});
		weechat::hook_signal_send('irc_input_send',
			weechat::WEECHAT_HOOK_SIGNAL_STRING,
			"$server;;;;/ison ".(join ' ', @{ $waiting{$server} }));
	}

	weechat::infolist_free($iptr);
	return weechat::WEECHAT_RC_OK;
}

sub irc_ison
{
	my %hashtable = %{ pop() };
	unless ($hashtable{output}) {
		$noison{lc $hashtable{server}} = 1;
		return weechat::WEECHAT_RC_ERROR;
	}
	my %nicks = map { lc $_ => 1 }
		split / +/, ($hashtable{output} =~ s/^:[^ ]* 303 [^ ]+ :?//r);

	for my $confnick (is_waiting($hashtable{server})) {
		next if exists $nicks{lc $confnick}; # still taken
		do_nick($hashtable{server}, $confnick);
		last;
	}
	return weechat::WEECHAT_RC_OK;
}

sub irc_nick
{
	my (undef, $server, $oldnick, $newnick) = (shift,
		shift =~ /(.+),irc_raw_in_nick/i,
		shift =~ /:([^! ]+)[^ ]* nick :?(.*)/i);
	return weechat::WEECHAT_RC_OK if lc $oldnick eq lc $newnick;
	try_nick($server, $oldnick);
	return weechat::WEECHAT_RC_OK;
}

sub irc_quit
{
	my (undef, $server, $nick) = (shift,
		shift =~ /(.+),irc_raw_in_quit/i,
		shift =~ /:([^! ]+)[^ ]* quit /i);
	try_nick($server, $nick);
	return weechat::WEECHAT_RC_OK;
}

sub irc_433
{
	my ($server) = $_[1] =~ /(.+),irc_raw_in2_433/i;
	$server = lc $server;
	# nick is taken when we connect? enable
	if (exists $connecting{$server}) {
		enable($server) and info($server, 'keepnick enabled');
	}
	return weechat::WEECHAT_RC_OK;
}

sub irc_connecting
{
	$connecting{lc pop} = 1;
	return weechat::WEECHAT_RC_OK;
}

sub irc_connected
{
	delete $connecting{lc pop};
	return weechat::WEECHAT_RC_OK;
}

sub irc_disconnect
{
	my $server = lc pop;
	delete $connecting{$server};
	disable($server);

	return weechat::WEECHAT_RC_OK;
}

sub cmd_keepnick
{
	my (undef, $buffer, $command) = @_;
	my $server = lc weechat::buffer_get_string($buffer, 'localvar_server');
	for ($command) {
		chomp;
		if (/^$/) {
			info($server, is_waiting($server)
				? "trying to get '".(join "', '", is_waiting($server))."'"
				: "not keeping your nick");
		}
		elsif (/^-enable$/) {
			my @waiting = enable($server, 1);
			if (@waiting) { info($server, "enabled, now waiting for '".(join "', '", @waiting)."'"); }
			else { info($server, "you already have your primary nick! doing nothing"); }
		}
		elsif (/^-disable$/) {
			disable($server);
			info($server, "no longer trying to keep your nick");
		}
		elsif (/^-autoenable$/) {
			weechat::config_get_plugin('default_enable')
				? weechat::config_unset_plugin("server.$server")
				: weechat::config_set_plugin("server.$server", '1');
			enable($server);
			info($server, "keepnick enabled on this server");
		}
		elsif (/^-autodisable$/) {
			weechat::config_get_plugin('default_enable')
				? weechat::config_set_plugin("server.$server", '0')
				: weechat::config_unset_plugin("server.$server");
			disable($server);
			info($server, "keepnick disabled on this server");
		}
		else {
			my @waiting = enable($server, 1, $command =~ s/ /,/gr);
			if (@waiting) { info($server, "now waiting for '".(join "', '", @waiting)."'"); }
			else { info($server, "you already have your primary nick! doing nothing"); }
		}
	}

	return weechat::WEECHAT_RC_OK;
}

if (weechat::register($SCRIPT_NAME, $SCRIPT_AUTHOR, $SCRIPT_VERSION,
 $SCRIPT_LICENCE, $SCRIPT_DESC, '', '')) {
	for my $option (keys %OPTIONS) {
		weechat::config_set_plugin($option, $OPTIONS{$option}[1])
			unless weechat::config_is_set_plugin($option);
		weechat::config_set_desc_plugin($option, $OPTIONS{$option}[0]);
	}

	weechat::hook_command('keepnick', $SCRIPT_DESC,
		"[nick]\n-enable|-disable\n-autoenable|-autodisable",
		"This command allows you to check the current server keepnick\n".
		"status or to manually specify nicks (separated by comma) to keep.\n".
		"You may also manually -enable or -disable keepnick on the current\n".
		"server. Both -autoenable and -autodisable choices are saved in\n".
		"config under 'plugins.var.perl.$SCRIPT_NAME.server.xxx' where 'xxx'\n".
		"is the server name.",
		'-enable|-disable|-autoenable|-autodisable %-', 'cmd_keepnick', '');
	weechat::hook_signal('*,irc_raw_in_nick', 'irc_nick', '');
	weechat::hook_signal('*,irc_raw_in_quit', 'irc_quit', '');
	weechat::hook_signal('*,irc_raw_in2_433', 'irc_433', '');
	weechat::hook_signal('irc_server_connecting', 'irc_connecting', '');
	weechat::hook_signal('irc_server_connected', 'irc_connected', '');
	weechat::hook_signal('irc_server_disconnected', 'irc_disconnect', '');
	weechat::hook_timer(weechat::config_get_plugin('check_time') * 1000, 0, 0,
		'ison_check', '');
	weechat::hook_hsignal("irc_redirection_${SCRIPT_NAME}_ison", 'irc_ison', '');

	my $iptr = weechat::infolist_get('irc_server', '', '');
	enable(weechat::infolist_string($iptr, 'name'))
		while (weechat::infolist_next($iptr));
	weechat::infolist_free($iptr);
}
