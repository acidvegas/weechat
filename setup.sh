#!/bin/bash
# Weechat Container - Developed by acidvegas (https://git.acid.vegas/weechat)
# weechat/setup.sh

# Configuration
DEPLOYMENT_DIR=/opt/weechat
RELAY_DOMAIN=weechat.supernets.org
RELAY_PORT=5000
WEECHAT_USER=acidvegas

# Check if we are in the correct deployment directory
[ ! -d $DEPLOYMENT_DIR ] && echo "Error: You must be in the $DEPLOYMENT_DIR directory" && exit 1

renew_relay_certificate() {
	# Copy the certificate and key to the data directory
	cat /etc/letsencrypt/live/$RELAY_DOMAIN/fullchain.pem /etc/letsencrypt/live/$RELAY_DOMAIN/privkey.pem > $DEPLOYMENT_DIR/data/tls/relay.pem

	# Set the ownership and permissions of the certificate and key
	chown -R $WEECHAT_USER:$WEECHAT_USER $DEPLOYMENT_DIR/data/tls/relay.pem && chmod 400 $DEPLOYMENT_DIR/data/tls/relay.pem

	# Tell weechat to use the new certificate
	printf '%b' '*/relay tlscertkey\n' > $DEPLOYMENT_DIR/data/weechat_fifo &
}

setup_root() {
	# Install dependencies
	apt update && apt install -y certbot

	# Install docker
	curl -fsSL https://get.docker.com | sh && gpasswd -a $WEECHAT_USER docker
	
	# Generate certificate
	certbot certonly --standalone -d $RELAY_DOMAIN --agree-tos --non-interactive --register-unsafely-without-email --quiet

	# Create the systemd service for certbot renewal
	{
		echo "[Unit]"
		echo "Description=Certbot renewal"
		echo "[Service]"
		echo "Type=oneshot"
		echo "ExecStart=/usr/bin/certbot renew -n --quiet --agree-tos --deploy-hook '$DEPLOYMENT_DIR/setup.sh renew'"
		echo "[Install]"
		echo "WantedBy=multi-user.target"
	} > /etc/systemd/system/certbot.service

	# Create the systemd timer for certbot renewal
	{
		echo "[Unit]"
		echo "Description=Certbot renewal timer"
		echo "[Timer]"
		echo "OnCalendar=0/12:00:00"
		echo "RandomizedDelaySec=1h"
		echo "Persistent=true"
		echo "[Install]"
		echo "WantedBy=timers.target"
	} > /etc/systemd/system/certbot.timer


	# Enable and start the services
	systemctl enable certbot.timer && systemctl start certbot.timer
}

setup_weechat() {
	# Create the persistent data directory structure for weechat
	mkdir -p $DEPLOYMENT_DIR/data/{python,perl}/autoload
	mkdir -p $DEPLOYMENT_DIR/data/{logs,tls}

	# Create the FIFO pipe for weechat
	[ -p $DEPLOYMENT_DIR/data/weechat_fifo ] || mkfifo $DEPLOYMENT_DIR/data/weechat_fifo

	# Copy scripts and config into the data directory
	cp -f $DEPLOYMENT_DIR/assets/alias.conf          $DEPLOYMENT_DIR/data/alias.conf
	cp -f $DEPLOYMENT_DIR/assets/scripts/perl/*.pl   $DEPLOYMENT_DIR/data/perl/autoload/
	cp -f $DEPLOYMENT_DIR/assets/scripts/python/*.py $DEPLOYMENT_DIR/data/python/autoload/

	# Copy the client certificate if it exists
	if [ -f $DEPLOYMENT_DIR/assets/tls/cert.pem ]; then
		cp -f $DEPLOYMENT_DIR/assets/tls/cert.pem $DEPLOYMENT_DIR/data/tls/cert.pem
		chown $WEECHAT_USER:$WEECHAT_USER $DEPLOYMENT_DIR/data/tls/cert.pem && chmod 400 $DEPLOYMENT_DIR/data/tls/cert.pem
	fi

	# Remove existing docker container if it exists
	docker rm -f weechat 2>/dev/null || true

	# Build the custom weechat image
	docker build -t weechat .

	# Run the container
	docker run -it --name weechat --restart unless-stopped \
		--detach-keys="ctrl-a,d" \
		-e TERM=$TERM \
		-v $DEPLOYMENT_DIR/data:/home/user/.weechat \
		-p $RELAY_PORT:5000 \
		weechat \
		weechat -d /home/user/.weechat -P 'alias,buflist,charset,exec,fifo,fset,irc,logger,perl,python,relay,script,trigger,typing' -r '/set weechat.plugin.autoload alias,buflist,charset,exec,fifo,fset,irc,logger,perl,python,relay,script,trigger,typing;/save'
}

case "$1" in
	root)    setup_root                                             ;;
	weechat) setup_weechat                                          ;;
	renew)   renew_relay_certificate                                ;;
	attach)  docker attach --detach-keys="ctrl-a,d" weechat         ;;
	*)       echo "Usage: $0 <root|weechat|renew|attach>" && exit 1 ;;
esac