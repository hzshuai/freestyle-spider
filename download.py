"""
通过网易云英语NodJsApi获取所有歌曲的歌词和音频文件
"""
import requests
import json
import os
import sys
import time
import random
from contextlib import closing

def sleeping(str = ''):
    sleep_time = random.random() / 8
    print('\t.......... sleeping = %f s, %s)' % (sleep_time, str))
    time.sleep(sleep_time)

def download_file(mp3_url, mp3_path):
    with closing(requests.get(mp3_url, stream=True)) as response:
        chunk_size = 1024
        content_size = int(response.headers['content-length'])
        cur_size = 0
        with open(mp3_path, "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                cur_size += len(data)
                print('\t....... downloading %f%%' % (cur_size * 100. / content_size), end='\r')
        print('\t....... saved mp3 to %s' % mp3_path)

def fetch_lyric_using_nodejs_api(artist_id, song_id):
    params = {'id': song_id}
    print('\tstart fetch lyric params: ', params)
    # 获取专辑对应的页面
    try:
        r = requests.get('http://localhost:3000/lyric', params = params)
        j = json.loads(r.text)
        if j['code'] == 200:
            if 'lrc' not in j or 'lyric' not in j['lrc']:
                print('[error] lyric is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
            else :
                lyric = j['lrc']['lyric']
                lrc_path = 'musics/at-%s/%s.lrc' % (artist_id, song_id)
                with open(lrc_path, 'w') as fout:
                    fout.write('%s' % lyric)
                    print('\t....... lrc saved to %s' % lrc_path)
                    sleeping("after finished download lrc artist_id = %s, song_id = %s, " % (artist_id, song_id))
        else :
            print('[error] fetch lyric failed, artist_id = %s, song_id = %s' % (artist_id, song_id))
    except Exception as e:
        print('[unknown error] fetch_lyric_using_nodejs_api artist_id = %s, song_id = %s: ' % (artist_id, song_id), e)

def fetch_mp3_using_nodejs_api(artist_id, song_id):
        params = {'id': song_id}
        print('\tstart fetch mp3 params: ', params)
        # 获取专辑对应的页面
        try:
            lrc_path = 'musics/at-%s/%s.lrc' % (artist_id, song_id)
            if not os.path.exists(lrc_path):
                print('[error] quit download mp3, lyric is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
                return
            r = requests.get('http://localhost:3000/music/url', params = params)
            j = json.loads(r.text)
            print('r = ', r.text)
            if j['code'] == 200 and len(j['data']) > 0:
                if 'url' not in j:
                    print('[error] mp3 url is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
                else :
                    mp3_url = j['data'][0]['url']
                    mp3_path = 'musics/at-%s/%s.mp3' % (artist_id, song_id)
                    download_file(mp3_url, mp3_path)
                    sleeping('finished download mp3 file artist_id = %s, song_id = %s' % (artist_id, song_id))
            else :
                print('[error] fetch mp3 failed, artist_id = %s, song_id = %s' % (artist_id, song_id))
        except Exception as e:
            print('[unknown error] fetch_mp3_using_nodejs_api artist_id = %s, song_id = %s: ' % (artist_id, song_id), e)

def fetch_all_songs(ftype = 'lyric', start = '', end = ''):
    run = start == ''
    with open('conf/all-artists-songs.txt', 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            artist_id = l[0]
            song_list_path = l[1].strip()
            print('==============', l[0], l[1].strip(), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if start == artist_id:
                print('start run ....')
                run = True
            if not run:
                continue

            if not os.path.exists(song_list_path):
                print('not extists of %s, %s' % (artist_id, song_list_path))
                continue
            print('start fetch %ss of %s, %s' % (ftype, artist_id, song_list_path))
            with open(song_list_path, 'r') as fin_s:
                for s in fin_s.readlines():
                    sp = s.split(',')
                    song_id = sp[0]
                    song_name = sp[1].strip()
                    print('  >>>> start fetch %s of %s, %s' % (ftype, song_id, song_name))
                    if ftype == 'lyric' or ftype == 'both':
                        fetch_lyric_using_nodejs_api(artist_id, song_id)
                    if ftype == 'mp3' or ftype == 'both':
                        fetch_mp3_using_nodejs_api(artist_id, song_id)

            if end == artist_id:
                print('************ Finished the download, from %s to %s' % (start, end))
                break

def test(artist_id, song_id):
    fetch_lyric_using_nodejs_api(artist_id, song_id)
    fetch_mp3_using_nodejs_api(artist_id, song_id)

def gen_song_list_path():
    artist = {}
    with open('conf/all-artists-songs.txt', 'w') as fout:
        with open('conf/artists-id-list.csv', 'r') as fin:
            for line in fin.readlines():
                l = line.split(',')
                artist_id = l[0].strip()
                artist_name = l[1].strip()
                songs_path = 'musics/at-%s/songs-id-list.csv' % artist_id
                if not os.path.exists(songs_path):
                    print("not extists: ", songs_path)
                else:
                    fout.write('%s, %s\n' % (artist_id, songs_path))
                    count = len(open(songs_path,'rU').readlines())
                    artist[l[0]] = [artist_name, count, songs_path]
    need = 0
    with open('conf/sorted-artists-songs.txt', 'w') as fout:
        for (k, v) in sorted(artist.items(), key = lambda e: e[1][1], reverse=True):
            fout.write('%s,%s,%d,%s\n' % (k, v[0], v[1], v[2]))
            if v[1] > 0:
                need += 1
    print('need download: ', need)

def run_test():
    test('1876', '410628763')
    test('1876', '410628762')
    test('1876', '410629742')
    test('1876', '32682099')
    test('1876', '476254045')

if __name__ == '__main__':
    gen_song_list_path()
    #run_test()

    ftype = sys.argv[1] if len(sys.argv) >=2 else 'lyric'
    start = sys.argv[2] if len(sys.argv) >=3 else ''
    end = sys.argv[3] if len(sys.argv) >=4 else ''
    #fetch_all_songs(ftype, start, end)
