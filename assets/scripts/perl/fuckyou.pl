# Ported from irssi to WeeChat by the Krusty Krab

use Time::HiRes qw(time);
use Digest::MD5 qw(md5_hex);


#__        ___    ____  _   _ ___ _   _  ____   _   _ ____ ___ _   _  ____
#\ \      / / \  |  _ \| \ | |_ _| \ | |/ ___| | | | / ___|_ _| \ | |/ ___|
# \ \ /\ / / _ \ | |_) |  \| || ||  \| | |  _  | | | \___ \| ||  \| | |  _
#  \ V  V / ___ \|  _ <| |\  || || |\  | |_| | | |_| |___) | || |\  | |_| |
#   \_/\_/_/   \_\_| \_\_| \_|___|_| \_|\____|  \___/|____/___|_| \_|\____|
#
# _____ _   _ _____ ____  _____   ____   ____ ____  ___ ____ _____ ____
#|_   _| | | | ____/ ___|| ____| / ___| / ___|  _ \|_ _|  _ \_   _/ ___|
#  | | | |_| |  _| \___ \|  _|   \___ \| |   | |_) || || |_) || | \___ \
#  | | |  _  | |___ ___) | |___   ___) | |___|  _ < | ||  __/ | |  ___) |
#  |_| |_| |_|_____|____/|_____| |____/ \____|_| \_\___|_|    |_| |____/
#
# __  __    _ __   __  ____  _____    _    _     _  __   __
#|  \/  |  / \\ \ / / |  _ \| ____|  / \  | |   | | \ \ / /
#| |\/| | / _ \\ V /  | |_) |  _|   / _ \ | |   | |  \ \//
#| |  | |/ ___ \| |   |  _ <| |___ / ___ \| |___| |___| |
#|_|  |_/_/   \_\_|   |_| \_\_____/_/   \_\_____|_____|_|
#
# _____ _   _  ____ _  _____ _   _  ____      _    _   _ _   _  _____   __
#|  ___| | | |/ ___| |/ /_ _| \ | |/ ___|    / \  | \ | | \ | |/ _ \ \ / /
#| |_  | | | | |   | ' / | ||  \| | |  _    / _ \ |  \| |  \| | | | \ V /
#|  _| | |_| | |___| . \ | || |\  | |_| |  / ___ \| |\  | |\  | |_| || |
#|_|    \___/ \____|_|\_\___|_| \_|\____| /_/   \_\_| \_|_| \_|\___/ |_|
#
#__   _____  _   _ ____    _   _ ____  _____ ____  ____
#\ \ / / _ \| | | |  _ \  | | | / ___|| ____|  _ \/ ___|
# \ V / | | | | | | |_) | | | | \___ \|  _| | |_) \___ \
#  | || |_| | |_| |  _ <  | |_| |___) | |___|  _ < ___) |
#  |_| \___/ \___/|_| \_\  \___/|____/|_____|_| \_\____/


my $SCRIPT_NAME = 'fuckyou';
my $SCRIPT_AUTHOR = 'Goat-See <mrtheplague@gmail.com>';
my $SCRIPT_VERSION = '2.3';
my $SCRIPT_LICENCE = 'urmom';
my $SCRIPT_DESC = '/fuckyou NICK numberchannels';

my %OPTIONS = (
	forcejoin => ['Command to forcejoin. ratbox uses forcejoin, unreal sajoin',
		'forcejoin'],
	forcepart => ['Command to forcepart. ratbox uses forcepart, unreal sapart',
		'forcepart'],
	furry => ['Channel prefix (include # or &)', '&HYE'],
	parallel => ['Number of channels to send per forcejoin command', 1],
	whois_cmd => ['Prefix to whois user (e.g. for ratbox operspy, "/whois !")',
		'/whois '],
	);

sub fuckyou
{
	my $buffer = shift;
	my $nig = $$ * time;
	my @jews;
	push @jews, "${FURRY}_".md5_hex($nig + $_) for (1..$PARALLEL);

	weechat::command($buffer, "/quote $FORCEJOIN $target ".join(',', @jews));

	return weechat::WEECHAT_RC_OK;
}

sub cmd_fuckyou
{
	my (undef, $buffer, $data) = @_;
	my $server = weechat::buffer_get_string($buffer, 'localvar_server');
	my $amt_end;
	($target, $amt_end) = split / +/, $data;
	our ($FORCEJOIN, $FURRY, $PARALLEL) = (
		weechat::config_get_plugin('forcejoin'),
		weechat::config_get_plugin('furry'),
		weechat::config_get_plugin('parallel'));

	weechat::unhook($signal) if $signal;
	weechat::unhook($timer) if $timer;

	unless ($target) {
		weechat::print($buffer, 'Stopped any current /fuckyou');
		return weechat::WEECHAT_RC_OK;
	}
	$amt_end //= 0;

	$signal = weechat::hook_signal("$server,irc_raw_in_402", 'irc_402', '');
	$timer = weechat::hook_timer(50, 0, $amt_end, 'fuckyou', $buffer);

	return weechat::WEECHAT_RC_OK;
}

sub cmd_unfuckyou
{
	my (undef, $buffer, $data) = @_;
	my ($server, $channel) = (
		weechat::buffer_get_string($buffer, 'localvar_server'),
		weechat::buffer_get_string($buffer, 'localvar_channel')
		);
	my $WHOIS = weechat::config_get_plugin('whois_cmd');

	unless ($data) {
		weechat::print($buffer, '/unfuckyou user user2 user3');
		return weechat::WEECHAT_RC_OK;
	}

	foreach my $dick (split / +/, $data) {
		weechat::hook_hsignal_send(
			'irc_redirect_command',
			{
				server => "$server",
				pattern => "whois",
				signal => "sigwhois"
			});
		weechat::hook_signal_send(
			'irc_input_send',
			weechat::WEECHAT_HOOK_SIGNAL_STRING,
			"$server;;1;;$WHOIS$dick"
			);
	}

	return weechat::WEECHAT_RC_OK;
}

sub event_whois_channels
{
	my %hashtable = %{$_[2]};
	my $FORCEPART = weechat::config_get_plugin('forcepart');
	my $FURRY = weechat::config_get_plugin('furry');
	my $counter = 0;
	my ($nick, $channels);

	for (split /^/, $hashtable{output}) {
		if (/^:[^ ]* 319 [^ ]+ ([^ ]+) :(.*)$/) {
			($nick, $channels) = ($1, $2);
		} else { next; }

		$channels =~ s/ +$//;

		my @niggers = split / +/, $channels;
		foreach (@niggers)
		{
			s/^[!@%+]*([&#])/$1/;
			if(/${FURRY}_[a-f0-9]+/i)
			{
				#Irssi::print("Forceparting $nick from $_");
				weechat::command('', "/quote $FORCEPART $nick $_");
				++$counter;
			}
		}
	}

	weechat::print('', "Forceparted $nick from $counter channels")
		if $counter;

	return weechat::WEECHAT_RC_OK;
}

sub irc_402 {
	my $message = pop;
	my $targmatch = quotemeta $target;

	return weechat::WEECHAT_RC_OK
		unless ($message =~ /^[^ ]* 402 [^ ]+ $targmatch /i);
	weechat::unhook($signal);
	weechat::unhook($timer);

	return weechat::WEECHAT_RC_OK;
}

if (weechat::register($SCRIPT_NAME, $SCRIPT_AUTHOR, $SCRIPT_VERSION,
 $SCRIPT_LICENCE, $SCRIPT_DESC, '', '')) {
	weechat::hook_command('fuckyou', '', '[<nick> [<amt>]]',
		"if nick is not given, stops current fuckyou, if any is running\n\n".
		"amt is 0 by default - user will be fuckyoud until they disconnect\n".
		"or you stop it manually\n",
		'', 'cmd_fuckyou', '');
	weechat::hook_command('unfuckyou', '', '<nick> [nick...]', '', '',
		'cmd_unfuckyou', '');
	weechat::hook_hsignal('irc_redirection_sigwhois_whois',
		'event_whois_channels', '');

	for my $option (keys %OPTIONS) {
		weechat::config_set_plugin($option, $OPTIONS{$option}[1])
		 unless weechat::config_is_set_plugin($option);
		weechat::config_set_desc_plugin($option, $OPTIONS{$option}[0]);
	}
}
