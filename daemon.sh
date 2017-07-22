#!/bin/sh
ps -fe | grep "node app.js" | grep -v grep
if [ $? -ne 0 ]
then
    cd /Users/hzshuai/Freestyle/music-crawler/NeteaseCloudMusicApi
    echo "start process....." >> node.log
    nohup node ./app.js >> node.log 2>&1 & 
else
    echo "runing....." >> /Users/hzshuai/Freestyle/music-crawler/NeteaseCloudMusicApi/node.log
fi
