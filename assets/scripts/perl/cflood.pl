#{{{ BSD License
# Copyright (c) 2008 hzu/zionist
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL  DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#}}}

# Ported from irssi to WeeChat by the Krusty Krab

use strict;
use warnings;
no strict 'subs';

my $SCRIPT_NAME = 'colourflood';
my $SCRIPT_AUTHOR = 'hzu';
my $SCRIPT_VERSION = '0.3';
my $SCRIPT_LICENCE = 'BSD';
my $SCRIPT_DESC = 'A-rab style ircing';

my $USAGE = <<EOF;
options:
    -r      Random back & foreground colours (default)
    -f      Amount of times the message is flooded
    -fg     font colour, available colours:
                black, blue, green
                lightred, red, magenta, orange
                yellow, lightgreen, cyan,
                lightcyan, lightblue,
                lightmagenta, gray, lightgray.
    -bg     background colour, available colours:
                black, blue, green, red,
                magenta, orange, green, cyan,
                lightcyan, lightblue,
                lightmagenta, gray, lightgray
EOF

our %clr = (
  black        => 1,
  blue         => 2,
  green        => 3,
  lightred     => 4,
  red          => 5,
  magenta      => 6,
  orange       => 7,
  yellow       => 8,
  lightgreen   => 9,
  cyan         => 10,
  lightcyan    => 11,
  lightblue    => 12,
  lightmagenta => 13,
  gray         => 14,
  lightgray    => 15,
);

if (weechat::register($SCRIPT_NAME, $SCRIPT_AUTHOR, $SCRIPT_VERSION,
 $SCRIPT_LICENCE, $SCRIPT_DESC, '', '')) {
	weechat::hook_command('cflood', $SCRIPT_DESC, '[options] text',
		$USAGE, '', 'cmd_cflood', '');

	my %OPTIONS = (
		dir => ['Database directory',
			weechat::info_get('weechat_dir', '').'/yiffs'],
		db => ['Default database', 'yiffs'],
		solodb => ['Default database when nick is omitted', 'solos'],
		);

	for my $option (keys %OPTIONS) {
		weechat::config_set_plugin($option, $OPTIONS{$option}[1])
		 unless weechat::config_is_set_plugin($option);
		weechat::config_set_desc_plugin($option, $OPTIONS{$option}[0]);
	}
}

sub colour {
	my ($fg, $bg, $text) = @_;
	my $fore = ($fg =~ /^[0-9][0-9]?$/) ? $fg : $clr{$fg};
	my $back = ($fg =~ /^[0-9][0-9]?$/) ? $bg : $clr{$bg};
	$fore-- if $fore == $back;
	$text = "\003$fore,$back $text \003$back,$fore $text ";
	$text x= (int 400 / length $text);
	return "$text\003";
}

sub parse {
	my @args = ( split / +/, shift );
	my ( %todo, $text, $body );

	while ( ($_ = shift @args) ne '' ) {
		/^-r$/ and next;
		/^-f$/ and $todo{f} = shift @args, next;
		/^-fg$/ and $todo{fg} = shift @args, next;
		/^-bg$/ and $todo{bg} = shift @args, next;
		/^-/ and weechat::print('', weechat::prefix('error').
			'Invalid arguments (see /help cflood)'), return;
		$text = @args < 1 ? $_ : "$_ " . join ' ', @args;
		last;
	}

	if (!(defined $todo{fg}) || !(defined $todo{bg})) {
		$body = "";
		my @rnd_clr = keys %clr;
		foreach ( 1 .. (defined $todo{f} ? $todo{f} : 1 ) ) {
			$body .= colour($rnd_clr[rand @rnd_clr],
				$rnd_clr[rand @rnd_clr], $text, $todo{f});
			$body .= "\n";
		}
	} else {
		$body = "";
		foreach ( 1 .. (defined $todo{f} ? $todo{f} : 1 ) ) {
			$body .= colour( $todo{fg}, $todo{bg}, $text );
			$body .= "\n";
		}
	}
	return $body;
}

sub cmd_cflood {
	my (undef, $buffer, $data) = @_;
	my $ret;

	return weechat::WEECHAT_RC_OK if ($data eq '');

	chomp( $ret = parse($data) );

	if ($ret =~ /\n/) {
		map { weechat::command($buffer, "/msg * $_") } (split /\n/, $ret);
	} else { 
		weechat::command($buffer, "/msg * $ret");
	}

	return weechat::WEECHAT_RC_OK;
}
