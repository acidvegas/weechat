#!/bin/bash
# Weechat Incus Container Setup Script - Developed by acidvegas (https://git.acid.vegas/weechat)

set -xev

create_container() {
    incus storage create weechat-pool dir
    incus launch images:debian/12 weechat-container -s weechat-pool
    incus config set weechat-container boot.autostart true
    sleep 10
    incus exec weechat-container -- apt update  -y
    incus exec weechat-container -- apt upgrade -y
    incus exec weechat-container -- apt install -y git nano nattended-upgrades wget
    incus exec weechat-container -- useradd -m -s /bin/bash agent
    incus exec weechat-container -- journalctl --vacuum-time=1d
    incus exec weechat-container -- sh -c 'printf "[Journal]\nStorage=volatile\nSplitMode=none\nRuntimeMaxUse=500K\n" > /etc/systemd/journald.conf'
    incus exec weechat-container -- systemctl restart systemd-journald
    incus exec weechat-container -- bash -c "echo 'TERM=xterm-256color' >> /etc/environment"
    incus config set weechat-container boot.autostart true
}


install_weechat() {
    incus exec weechat-container -- apt install -y ca-certificates
    incus exec weechat-container -- mkdir -p /etc/apt/keyrings
    incus exec weechat-container -- bash -c "curl --silent https://weechat.org/dev/info/debian_repository_signing_key_asc/ > /etc/apt/keyrings/weechat.asc"
    incus exec weechat-container -- bash -c "echo 'deb     [arch=amd64,i386,arm64,armhf signed-by=/etc/apt/keyrings/weechat.asc] https://weechat.org/debian bookworm main'  > /etc/apt/sources.list.d/weechat.list"
    incus exec weechat-container -- bash -c "echo 'deb-src [arch=amd64,i386,arm64,armhf signed-by=/etc/apt/keyrings/weechat.asc] https://weechat.org/debian bookworm main' >> /etc/apt/sources.list.d/weechat.list"
    incus exec weechat-container -- apt update
    incus exec weechat-container -- apt install -y screen weechat-curses weechat-plugins weechat-python weechat-perl
}


configure_weechat() {
    incus exec weechat-container -- su - agent -c "weechat -P 'alias,buflist,charset,exec,fifo,fset,irc,logger,perl,python,relay,script,trigger,typing' -r '/set weechat.plugin.autoload alias,buflist,charset,exec,fifo,fset,irc,logger,perl,python,relay,script,trigger,typing;/save;/quit'"
    incus exec weechat-container -- su - agent -c "mkdir /home/agent/.config/weechat/tls"
    incus exec weechat-container -- su - agent -c "git clone --depth 1 https://github.com/acidvegas/weechat.git /home/agent/weechat"
    incus exec weechat-container -- su - agent -c "mv /home/agent/weechat/assets/alias.conf /home/agent/.config/weechat/alias.conf && mv /home/agent/weechat/assets/scripts/perl/*.pl /home/agent/.local/share/weechat/perl/autoload/ && mv /home/agent/weechat/assets/scripts/python/*.py /home/agent/.local/share/weechat/python/autoload/ && rm -rf /home/agent/weechat"
    incus exec weechat-container -- su - agent -c "mkdir /home/agent/.local/share/weechat/logs"
    incus exec weechat-container -- su - agent -c "mkfifo /home/agent/.local/share/weechat/FIFO"
    incus exec weechat-container -- bash -c "git clone https://github.com/tat3r/tdfiglet.git && cd tdfiglet && make && sudo make install && cd && rm -rf tdfiglet"
}


configure_relay() {
    RELAY_PORT=2222
    RELAY_DOMAIN=big.dick.acid.vegas
    CONTAINER_IP=$(incus list | grep weechat-container | awk '{print $6}')
    
    incus config device add weechat-container weechat-certbot-port proxy listen=tcp:0.0.0.0:80          connect=tcp:$CONTAINER_IP:80
    incus config device add weechat-container weechat-relay-port   proxy listen=tcp:0.0.0.0:$RELAY_PORT connect=tcp:$CONTAINER_IP:$RELAY_PORT

    incus file push assets/renew weechat-container/home/agent/.local/share/weechat/renew
    incus exec weechat-container -- chown agent:agent /home/agent/.local/share/weechat/renew
    incus exec weechat-container -- chmod +x /home/agent/.local/share/weechat/renew
 
    incus exec weechat-container -- apt install -y certbot
    incus exec weechat-container -- certbot certonly --standalone -d $RELAY_DOMAIN -m nobody@noname.gov
    incus file push assets/certbot.service weechat-container/etc/systemd/system/certbot.service
    incus file push assets/certbot.timer weechat-container/etc/systemd/system/certbot.timer
    incus exec weechat-container -- systemctl enable certbot.timer && incus exec weechat-container -- systemctl start certbot.timer
}

create_container && install_weechat && configure_weechat && configure_relay