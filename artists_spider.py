import threading
import time
import queue
from queue import Queue

import requests
import json
import os
import sys
import random
import logging
import logging.config
from contextlib import closing

from DbClient import DbClient, CrawlStatus
import NetEaseApi

logging.config.fileConfig("conf/log.ini")
logger_name = "test"
logger = logging.getLogger(logger_name)

def sleeping(str = ''):
    sleep_time = random.random() / 8
    # logger.info('\t.......... sleeping = %f s, %s)' % (sleep_time, str))
    # time.sleep(sleep_time)

class Crawler(threading.Thread):
    def __init__(self, task_que, res_que):
        threading.Thread.__init__(self)
        self.task_que = task_que
        self.res_que = res_que
        self.proxies = {'http': '120.83.13.53:8080',
        'http': '180.109.139.109:8888','http': '211.143.155.172:80',
        'http': '117.135.251.209:80','http': '112.74.52.60:8888' }
        logger.info("start thread: %s" % self.name)

    def fetch_songs_using_nodejs_api(self, album_id, fout):
        params = {'id': album_id}
        logger.info('start fetch_songs_id params: album_id = %s' % album_id)
        # 获取专辑对应的页面
        try:
            # print('http://localhost:3000/album', params, headers, proxies)
            # r = requests.get('http://localhost:3000/album', params = params, headers = headers, proxies = proxies)
            # j = json.loads(r.text)
            j = NetEaseApi.get_album(album_id, proxies = self.proxies)
            if j['code'] == 200:
                for s in j['songs']:
                    fout.write('%s, %s\n' %(s['id'], s['name']))
                    logger.info('\t%s, %s' %(s['id'], s['name']))
                return CrawlStatus.CRAWLED
            else :
                logger.warn('fetch songs failed, album_id = %s' % album_id)
                return CrawlStatus.FAILED
        except Exception as e:
            logger.warn('[unknown error] fetch_songs_using_nodejs_api : %s' % e)
            return CrawlStatus.FAILED

    def fetch_albums_using_nodejs_api(self, artist_id):
        offset = 0
        limit = 12
        more = False
        # 获取歌手个人主页
        try:
            artist_dir = ('en-musics/at-%s' % artist_id)
            if not os.path.exists(artist_dir):
                os.mkdir(artist_dir)
            with open(artist_dir + '/songs-id-list.csv', 'w') as fout:
                while offset == 0 or more:
                    params = {'id': artist_id, 'limit': limit, 'offset': offset}
                    logger.info('start fetch_album params: {id : %s, limit: %s, offset: %s' %(artist_id, limit, offset))
                    # r = requests.get('http://localhost:3000/artist/album', params = params)
                    #j = json.loads(r.text)
                    j = NetEaseApi.get_artist_albums(artist_id, limit, offset, proxies = self.proxies)
                    if j['code'] == 200:
                        more = j['more']
                        for al in j['hotAlbums']:
                            status = self.fetch_songs_using_nodejs_api(al['id'], fout)
                            if status != CrawlStatus.CRAWLED:
                                return status
                            sleeping('\talbum: (%s, %s)' % (al['id'], al['name']))
                    else :
                        logger.warn('fetch albums failed, artist_id = %s' % artist_id)
                        return CrawlStatus.FAILED
                    offset += limit
            logger.info('....... save to file: %s' % (artist_dir + '/songs-id-list.csv'))
            return CrawlStatus.CRAWLED
        except Exception as e:
            logger.warn('[unknown error] fetch_albums_using_nodejs_api: %s' % e)
            return CrawlStatus.FAILED

    def run(self):
        while True:
            try:
                (artist_id, status) = task_que.get_nowait()
                logger.info('>>>>>> start processing: (artist_id = %s)' % (artist_id))

                # get proxies
                # self.proxies = {'http': '110.73.31.223:8123'}

                status = self.fetch_albums_using_nodejs_api(artist_id)
                # should be format at (status, comment, artist_id)
                self.res_que.put((status, '', artist_id))
            except queue.Empty:
                logger.info('task queue is empty, sleeping 5s ....')
                time.sleep(5)


class Scheduler():
    def __init__(self, db_client, task_que, res_que, threads, num):
        self.db_client = db_client
        self.task_que = task_que
        self.res_que = res_que
        self.threads = threads
        self.num = num
        self.crawled_cnt = 0
        self.db_client.restore_artist_jobs()

    def produce(self, num):
        while task_que.full():
            logger.info('====== Scheduler tasks queue is full, sleeping 3s')
            time.sleep(3)

        query = db_client.query_need_crawl_artist_jobs(num)
        tasks = []
        for e in query:
            if not task_que.full():
                task_que.put(e)
                tasks.append((CrawlStatus.IN_CRAWLING, '', e[0]))
            else :
                logger.info('====== Scheduler produce tasks queue fulled, %d threads has alive.' % self.num_alive())
                break
        if len(tasks) > 0:
            # should be format at [(status, comment, artist_id)]
            db_client.update_batch_artist_jobs(tasks)
            logger.info('====== Scheduler produce %d tasks' % (len(tasks)))

    def collect(self):
        res = []
        while not res_que.empty():
            r = res_que.get()
            res.append(r)
            if r[0] == CrawlStatus.CRAWLED:
                self.crawled_cnt += 1
                if self.crawled_cnt % 200 == 0:
                    logger.critical('artists_spider has crawled %d artists' % self.crawled_cnt)
        if len(res) > 0:
            # should be format at [(status, comment, artist_id)]
            db_client.update_batch_artist_jobs(res)
            logger.info('====== Scheduler collect %d result, total success: %d' % (len(res), self.crawled_cnt))

    def num_alive(self):
        num = 0
        for t in threads:
            if t.is_alive():
                num += 1
        return num

    def has_alive(self):
        for t in threads:
            if t.is_alive():
                return True
        logger.critical('All worker threads have down, total crawled %d artists.' % self.crawled_cnt)
        return False

    def run(self):
        while self.has_alive():
            try:
                self.produce(self.num)
                self.collect()
            except Exception as e:
                logger.error("[unknow error] Scheduler has encountered, e = %s" % e)

if __name__ == '__main__':
    # test multiple threading
    task_que = Queue(maxsize = 100)
    res_que = Queue()
    db_client = DbClient('artists.db')

    threads = []
    for i in range(2):
        t = Crawler(task_que, res_que)
        t.start()
        threads.append(t)

    s = Scheduler(db_client, task_que, res_que, threads, 2)
    s.run()
