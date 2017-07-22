#!/bin/sh
ps -fe | grep "node app.js" | grep -v grep
if [ $? -ne 0 ]
then
    cd /Users/hzshuai/Freestyle/music-crawler/NeteaseCloudMusicApi
    nohup node app.js > node.log 2>&1 & 
    echo "start process....."
else
    echo "runing....."
fi
# cronjob
# */1 * * * * sh /Users/hzshuai/Freestyle/music-crawler/daemon.sh
