### FreestyleSpider

项目目的: 爬取netease cloud music中的所有中文歌曲的歌词、歌曲文件(也可以扩展到爬取评论等数据)


### 参考项目：
[musicbox](https://github.com/darknessomi/musicbox/blob/master/NEMbox/api.py)
[NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi.git)

实现了网易云音乐的接口（获取歌手专辑、专辑歌曲、歌词、音频），详见`NeteaseCloudMusicApi`

- 主要用到里面的api请求，里面调用了网易云音乐的weapi，需要对query进行加密，使用了里面的加密过程。
- 具体实现见`NetEaseApi.py`

### 爬取过程

- Step1. 获取歌手id见`fetcher.py`
- Step2. 获取歌曲id
    + 生成抓取任务, 使用`prepare.py`中的`prepare_artist_jobs`, 会生成一个sqllitedb, "artists.db"
    + 然后用`artist_spider.py`去爬每个歌手所有专辑下的歌曲id
- Step3. 抓取歌词和歌曲
    + 生成抓取任务, 使用`prepare.py`中的`prepare_music_jobs`, 会生成一个sqllitedb, "musics.db"
    + 然后用`music_spider.py`去抓取每个歌曲的歌词和歌曲,考虑到歌曲抓取时间较长,可以控制只抓取歌曲, 通过ftype='mp3'|'lrc'控制
    
### 其他

- `DbClient.py`封装了netease cloud music的请求

