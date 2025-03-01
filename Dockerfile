FROM alpine:latest

# Install required packages
RUN apk add --no-cache curl nano openssl python3-pip weechat weechat-perl weechat-python

# Create weechat user
RUN adduser -D -h /home/weechat weechat

# Switch to weechat user
USER weechat
WORKDIR /home/weechat

# Create weechat directory structure
RUN mkdir -p .weechat/{python/autoload,perl/autoload,logs,tls} && chmod 700 .weechat

# Copy our local files into the container
COPY scripts/python/*.py .weechat/python/autoload/
COPY scripts/perl/*.pl   .weechat/perl/autoload/
COPY alias.conf          .weechat/

# Install Python dependencies for scripts
RUN pip3 install --user requests

# Create fifo for external commands
RUN mkfifo .weechat/weechat_fifo

# Generate SSL certificate
RUN openssl req -x509 -new -newkey rsa:4096 -sha256 -days 3650 -nodes -out .weechat/tls/cert.pem -keyout .weechat/tls/cert.pem -subj "/CN=HARDCHATS" && chmod 400 .weechat/tls/cert.pem

# Start actual weechat client
ENTRYPOINT ["weechat"] 