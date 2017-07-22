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
from bs4 import BeautifulSoup
import socket

headers = {
    'Referer':'http://music.163.com/',
    'Host':'music.163.com',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

atdict = {}

def fetch_artist(group_id, initial, fout):
    params = {'id': group_id, 'initial': initial}
    print('params: ', params)
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
                print("[error] duplicate artist id: ", artist_id, group_id, initial)
            else:
                atdict[artist_id] = 1
                fout.write('%s, %s\n' % (artist_id, artist_name))
                print('%s, %s' % (artist_id, artist_name))
        except Exception as e:
            # 打印错误日志
            print("[error] duplicate artist id: ", artist_id, group_id, initial)
            print(e)

    for artist in artists:
        artist_id = artist['href'].replace('/artist?id=', '').strip()
        artist_name = artist['title'].replace('的音乐', '')
        try:
            if artist_id in atdict:
                print("[error] duplicate artist id: ", artist_id, group_id, initial)
            else:
                atdict[artist_id] = 1
                fout.write('%s, %s\n' % (artist_id, artist_name))
                print('%s, %s' % (artist_id, artist_name))
        except Exception as e:
            # 打印错误日志
            print("[error] duplicate artist id: ", artist_id, group_id, initial)
            print(e)

def fetch_songs(album_id, fout):
    params = {'id': album_id}
    print('start fetch_songs_id params: ', params)
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
        print('\t\t%s, %s' % (music_id, music_name))

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
    print('start fetch_songs params: ', params)
    # 获取专辑对应的页面
    try:
        r = requests.get('http://localhost:3000/album', params = params)
        j = json.loads(r.text)
        if j['code'] == 200:
            for s in j['songs']:
                fout.write('%s, %s\n' %(s['id'], s['name']))
                print('\t\t%s, %s' %(s['id'], s['name']))
        else :
            print('[error] fetch songs failed, album_id = %s' % album_id)
    except Exception as e:
        print('[unknown error] fetch_songs_using_nodejs_api : ', e)
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
                print('start fetch_album params: ', params)
                r = requests.get('http://localhost:3000/artist/album', params = params)
                j = json.loads(r.text)
                if j['code'] == 200:
                    more = j['more']
                    for al in j['hotAlbums']:
                        fetch_songs_using_nodejs_api(al['id'], fout)
                        sleep_time = random.random() / 8
                        print('\talbum: (%s, %s, sleeping = %f ms)' % (al['id'], al['name'], sleep_time))
                        time.sleep(sleep_time)
                else :
                    print('[error] fetch albums failed, artist_id = %s' % artist_id)
                offset += limit
    except Exception as e:
        print('[unknown error] fetch_albums_using_nodejs_api :', e)
        raise e

def fetch_all_artists():
    id_arr = [1001, 1002, 1003]

    with open('artists-id-list.csv', 'w') as fout:
        for gg in id_arr:
            for i in range(65, 91):
                fetch_artist(gg, i, fout)
            fetch_artist(gg, 0, fout)

def health_check(ftype = 'web'):
    try:
        if ftype == 'web':
            fetch_albums(805076)
        else :
            fetch_albums_using_nodejs_api(805076)
        print("health_check: Everything is alive. ")
        return True
    except Exception as e:
        print('health_check: It maybe dead', e)
        return False

def fetch_all_albums(ftype = 'api', start = '', end = ''):
    run = start == ''
    print("start fetch_all_albums, from %s to %s" % (start, end))
    with open('conf/artists-id-list.csv', 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            print('==============', l[0], l[1].strip(), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if l[0] == start:
                run = True
                print('start run.........')

            if not run:
                continue

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
                        print('[albums format error] atist_id: %s' % l[0])
                        nt = num_retries
                    else :
                        print('[unknown error] fetch_all_albums atist_id: %s, has tried %d times, sleep %d s : ' % (l[0], nt, sleep_time), e)
                        time.sleep(sleep_time)

            if l[0] == end:
                print('************ Finished the download, from %s to %s' % (start, end))
                break

def fetch_test(ftype = 'web', artist_id):
    try:
        if ftype == 'web':
            fetch_albums(artist_id)
        else :
            fetch_albums_using_nodejs_api(artist_id)
        print("fetch_test: Everything is alive. ")
    except Exception as e:
        print('fetch_test: It maybe dead', e)

if __name__ == '__main__':
    fetch_all_artists()
    socket.setdefaulttimeout(30)
    ftype = sys.argv[1] if len(sys.argv) >=2 else 'api'
    start = sys.argv[2] if len(sys.argv) >=3 else ''
    end   = sys.argv[3] if len(sys.argv) >= 4 else ''

    #fetch_all_albums(ftype, start, end)

    print("finished crawler......")
