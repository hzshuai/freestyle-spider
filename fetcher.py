"""
网易云api以及文件操作，包括：解析操作
获取所有歌手，歌手的专辑以及专辑的歌ids
"""
import requests
import json
import os
import time
import sys
import random
import logging
import logging.config
from bs4 import BeautifulSoup
import socket

headers = {
    'Referer':'http://music.163.com/',
    'Host':'music.163.com',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

proxies = {}

logging.config.fileConfig("conf/log.ini")
logger_name = "root"
logger = logging.getLogger(logger_name)

atdict = {}

def fetch_artist(group_id, initial, fout):
    params = {'id': group_id, 'initial': initial}
    logger.info('params: (id = %s, initial = %s)' % (group_id, initial))
    r = requests.get('http://music.163.com/discover/artist/cat', headers = headers, params = params)

    # 网页解析
    soup = BeautifulSoup(r.content.decode(), 'html.parser')
    body = soup.body

    hot_artists = body.find_all('a', attrs={'class': 'msk'})
    artists = body.find_all('a', attrs={'class': 'nm nm-icn f-thide s-fc0'})

    for artist in hot_artists:
        artist_id = artist['href'].replace('/artist?id=', '').strip()
        artist_name = artist['title'].replace('的音乐', '')
        try:
            if artist_id in atdict:
                logger.error("duplicate artist id: %s %s %s" % (artist_id, group_id, initial))
            else:
                atdict[artist_id] = 1
                fout.write('%s, %s\n' % (artist_id, artist_name))
                logger.info('%s, %s' % (artist_id, artist_name))
        except Exception as e:
            # 打印错误日志
            logger.exception("artist id: ", artist_id, group_id, initial)

    for artist in artists:
        artist_id = artist['href'].replace('/artist?id=', '').strip()
        artist_name = artist['title'].replace('的音乐', '')
        try:
            if artist_id in atdict:
                logger.error("duplicate artist id: %s %s %s" % (artist_id, group_id, initial))
            else:
                atdict[artist_id] = 1
                fout.write('%s, %s\n' % (artist_id, artist_name))
                logger.info('%s, %s' % (artist_id, artist_name))
        except Exception as e:
            # 打印错误日志
            logger.exception("artist id: %s %s %s" % (artist_id, group_id, initial))

def fetch_songs(album_id, fout):
    params = {'id': album_id}
    logger.info('start fetch_songs_id params: album_id = %s' % album_id)
    # 获取专辑对应的页面
    r = requests.get('http://music.163.com/album', headers = headers, params = params)

    # 网页解析
    soup = BeautifulSoup(r.content.decode(), 'html.parser')
    body = soup.body

    musics = body.find('ul', attrs={'class': 'f-hide'}).find_all('li')  # 获取专辑的所有音乐

    for music in musics:
        music = music.find('a')
        music_id = music['href'].replace('/song?id=', '')
        music_name = music.getText()
        fout.write('%s, %s\n' % (music_id, music_name))
        logger.info('\t%s, %s' % (music_id, music_name))

def fetch_albums(artist_id):
    offset = 0
    limit = 12
    more = False
    # len(None)
    artist_dir = ('musics/at-%s' % artist_id)
    if not os.path.exists(artist_dir):
        os.mkdir(artist_dir)

    with open(artist_dir + '/songs-id-list.csv', 'w') as fout:
        while offset == 0 or more:
            params = {'id': artist_id, 'limit': limit, 'offset': offset}
            print('start fetch_album params: ', params)
            # 获取歌手个人主页
            r = requests.get('http://music.163.com/artist/album', headers = headers, params = params)

            # 网页解析
            soup = BeautifulSoup(r.content.decode(), 'html.parser')
            body = soup.body
            albums = body.find_all('a', attrs={'class': 'tit s-fc0'})  # 获取所有专辑

            for album in albums:
                album_id = album['href'].replace('/album?id=', '')
                album_name = album.string
                print('\t%s, %s' % (album_id, album_name))
                fetch_songs(album_id, fout)

                sleep_time = random.random() / 8
                print('\talbum: (%s, %s, sleep = %f s)' % (album_id, album_name, sleep_time))
                time.sleep(sleep_time)

            offset += limit
            if len(albums) > 0:
                more = True
            else:
                more = False
            print('sleeping... 2 seconds')
            time.sleep(random.random() * 1) # sleep 5 seconds while fetch 12 albums

def fetch_songs_using_nodejs_api(album_id, fout):
    params = {'id': album_id}
    logger.info('start fetch_songs_id params: album_id = %s' % album_id)
    # 获取专辑对应的页面
    try:
        print('http://localhost:3000/album', params, headers, proxies)
        r = requests.get('http://localhost:3000/album', params = params, headers = headers, proxies = proxies)
        j = json.loads(r.text)
        if j['code'] == 200:
            for s in j['songs']:
                fout.write('%s, %s\n' %(s['id'], s['name']))
                logger.info('\t%s, %s' %(s['id'], s['name']))
        else :
            logger.warn('fetch songs failed, album_id = %s' % album_id)
    except Exception as e:
        logger.warn('[unknown error] fetch_songs_using_nodejs_api : %s' % e)
        raise e

def fetch_albums_using_nodejs_api(artist_id):
    offset = 0
    limit = 12
    more = False
    # 获取歌手个人主页
    try:
        artist_dir = ('musics/at-%s' % artist_id)
        if not os.path.exists(artist_dir):
            os.mkdir(artist_dir)
        with open(artist_dir + '/songs-id-list.csv', 'w') as fout:
            while offset == 0 or more:
                params = {'id': artist_id, 'limit': limit, 'offset': offset}
                logger.info('start fetch_album params: {id : %s, limit: %s, offset: %s' %(artist_id, limit, offset))
                r = requests.get('http://localhost:3000/artist/album', params = params)
                j = json.loads(r.text)
                if j['code'] == 200:
                    more = j['more']
                    for al in j['hotAlbums']:
                        fetch_songs_using_nodejs_api(al['id'], fout)
                        sleep_time = random.random() / 8
                        logger.info('\talbum: (%s, %s, sleeping = %f ms)' % (al['id'], al['name'], sleep_time))
                        time.sleep(sleep_time)
                else :
                    logger.warn('fetch albums failed, artist_id = %s' % artist_id)
                offset += limit
    except Exception as e:
        logger.warn('[unknown error] fetch_albums_using_nodejs_api: %s' % e)
        raise e

def fetch_all_artists(id_arr, outfile):
    with open(outfile, 'w') as fout:
        for gg in id_arr:
            for i in range(65, 91):
                fetch_artist(gg, i, fout)
            fetch_artist(gg, 0, fout)

def fetch_hot_artists(id_arr, outfile):
    with open(outfile, 'w') as fout:
        for gg in id_arr:
            fetch_artist(gg, -1, fout)

def health_check(ftype = 'web'):
    try:
        if ftype == 'web':
            fetch_albums(805076)
        else :
            fetch_albums_using_nodejs_api(805076)
        logger.info("health_check: Everything is alive. ")
        return True
    except Exception as e:
        logger.error('health_check: It maybe dead, %s' % e)
        return False

def fetch_all_albums(filepath, ftype = 'api', start = '', end = ''):
    run = start == ''
    logger.info("start fetch_all_albums %s, from %s to %s" % (filepath, start, end))
    cnt = 0
    has_failed = False
    with open(filepath, 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            logger.info('======== ' + line.strip())
            if l[0] == start:
                run = True
                logger.info('start run.........')

            if not run:
                continue

            cnt += 1
            if cnt % 200 == 0 and not has_failed:
                logger.critical("spider has crawled %s artists" % cnt)

            num_retries = 4 * 60 * 60
            nt = 0
            sleep_time = 60
            while nt < num_retries:
                try:
                    if ftype == 'web':
                        fetch_albums(l[0])
                    else :
                        fetch_albums_using_nodejs_api(l[0])
                    nt = num_retries
                except Exception as e:
                    nt += 1
                    if health_check(ftype) and nt > 3:
                        logger.error('give up to fetch atist_id: %s' % l[0])
                        nt = num_retries
                    else :
                        logger.warn('[unknown error] fetch_all_albums atist_id: %s, has tried %d times, sleep %d s : ' % (l[0], nt, sleep_time))
                        time.sleep(sleep_time)

            if nt == num_retries:
                logger.critical('************ Give up the crawl at artist id %s' % l[0])
                break

            if l[0] == end:
                logger.info('************ Finished the download, from %s to %s' % (start, end))
                break

def fetch_single(artist_id, ftype = 'api'):
    try:
        if ftype == 'web':
            fetch_albums(artist_id)
        else :
            fetch_albums_using_nodejs_api(artist_id)
        print("fetch_test: Everything is alive. ")
    except Exception as e:
        print('fetch_test: It maybe dead', e)

def run_test():
    fetch_single(2799)
    fetch_single(3841)
    fetch_single(12523504)
    fetch_single(12521473)
    fetch_single(12521439)
    fetch_single(12521417)
    fetch_single(12520605)
    fetch_single(12520251)

    fetch_single(12519287)
    fetch_single(12519665)
    fetch_single(11715)


if __name__ == '__main__':
    ##
    #run_test()

    '''
        fetch chinese artists
    '''
    #fetch_hot_artists([1001, 1002, 1003], 'conf/hot-artists-id-list.csv')
    #fetch_all_artists([1001, 1002, 1003], 'conf/artists-id-list.csv')

    '''
        fetch english artists
    '''
    # fetch_hot_artists([2001, 2002, 2003], 'conf/hot-en-artists-id-list.csv')
    # fetch_all_artists([2001, 2002, 2003], 'conf/en-artists-id-list.csv')

    '''
        fetch all albums and get the song lists
    '''
    ftype = sys.argv[1] if len(sys.argv) >=2 else 'api'
    start = sys.argv[2] if len(sys.argv) >=3 else ''
    end   = sys.argv[3] if len(sys.argv) >= 4 else ''

    #fetch_all_albums('conf/artists-id-list.csv', ftype, start, end)

    fetch_all_albums('conf/en-artists-id-list.csv', ftype, start, end)

    print("finished crawler......")
