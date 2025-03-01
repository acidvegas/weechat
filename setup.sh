#!/bin/bash
docker build -t weechat .
docker run --restart=always -d --name weechat weechat

echo "Attach to   WeeChat: docker attach weechat"
echo "Detach from WeeChat: Ctrl+p Ctrl+q"
