# Weechat Container - Developed by acidvegas (https://git.acid.vegas/weechat)
# weechat/Dockerfile

# Use the official weechat image as the base image
FROM weechat/weechat

# Set the user to root
USER root

# Install the dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates make gcc libc6-dev && \
    git clone --depth 1 https://github.com/tat3r/tdfiglet.git /tmp/tdfiglet && \
    cd /tmp/tdfiglet && make && make install && \
    apt-get purge -y git make gcc libc6-dev && \
    apt-get autoremove -y && \
    rm -rf /tmp/tdfiglet /var/lib/apt/lists/*

# Set the user to user
USER user
