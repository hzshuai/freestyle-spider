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
    def __init__(self, task_que, res_que, ftype):
        threading.Thread.__init__(self)
        self.task_que = task_que
        self.res_que = res_que
        self.ftype = ftype
        self.proxies = {}
        logger.info("start thread: %s" % self.name)

    def fetch_lyric_using_nodejs_api(self, artist_id, song_id):
        params = {'id': song_id}
        logger.info('\tstart fetch lyric params: song_id = %s' % song_id)
        # 获取专辑对应的页面
        try:
            # r = requests.get('http://localhost:3000/lyric', params = params)
            # j = json.loads(r.text)
            j = NetEaseApi.get_lyric(song_id, self.proxies)
            if j['code'] == 200:
                if 'lrc' not in j or 'lyric' not in j['lrc']:
                    logger.warn('[error] lyric is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
                    return CrawlStatus.NOT_FOUND
                else :
                    lyric = j['lrc']['lyric']
                    lrc_path = 'musics/at-%s/%s.lrc' % (artist_id, song_id)
                    with open(lrc_path, 'w') as fout:
                        fout.write('%s' % lyric)
                        logger.info('\t....... lrc saved to %s' % lrc_path)
                        sleeping("after finished download lrc artist_id = %s, song_id = %s" % (artist_id, song_id))
                    return CrawlStatus.CRAWLED
            else :
                logger.error('fetch lyric failed, artist_id = %s, song_id = %s' % (artist_id, song_id))
                return CrawlStatus.FAILED
        except Exception as e:
            logger.error('[unknown error] fetch_lyric_using_nodejs_api artist_id = %s, song_id = %s, e = %s' % (artist_id, song_id, e))
            return CrawlStatus.FAILED

    def download_file(self, mp3_url, mp3_path):
        try:
            with closing(requests.get(mp3_url, stream=True, proxies=self.proxies)) as response:
                chunk_size = 1024
                content_size = int(response.headers['content-length'])
                cur_size = 0
                with open(mp3_path, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        cur_size += len(data)
                        # logger.info('\t....... downloading %f%%' % (cur_size * 100. / content_size), end='\r')
                logger.info('\t....... saved mp3 to %s' % mp3_path)
                return CrawlStatus.CRAWLED
        except Exception as e:
            logger.error('[unknown error] download file of song_file = %s, e = %s' % (mp3_path, e))
            return CrawlStatus.FAILED
        except BaseException as e:
            logger.error('[unnormal error] download file of song_file = %s, e = %s' % (mp3_path, e))
            return CrawlStatus.FAILED

    def fetch_mp3_using_nodejs_api(self, artist_id, song_id):
            params = {'id': song_id}
            logger.info('\tstart fetch mp3 params: artist_id = %s, song_id = %s' % (artist_id, song_id))
            # 获取专辑对应的页面
            try:
                lrc_path = 'musics/at-%s/%s.lrc' % (artist_id, song_id)
                if not os.path.exists(lrc_path):
                    logger.warn('quit download mp3, lyric is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
                    return CrawlStatus.FAILED
                # r = requests.get('http://localhost:3000/music/url', params = params)
                # j = json.loads(r.text)
                j = NetEaseApi.get_mp3url(song_id, self.proxies)
                # print('r = ', r.text)
                if j['code'] == 200 and len(j['data']) > 0:
                    if 'url' not in j['data'][0] or j['data'][0]['url'] is None:
                        logger.warn('mp3 url is not exists, artist_id = %s, song_id = %s' % (artist_id, song_id))
                        return CrawlStatus.NOT_FOUND
                    else :
                        mp3_url = j['data'][0]['url']
                        mp3_path = 'musics/at-%s/%s.mp3' % (artist_id, song_id)
                        status = self.download_file(mp3_url, mp3_path)
                        sleeping('finished download mp3 file artist_id = %s, song_id = %s' % (artist_id, song_id))
                        return status
                else :
                    logger.error('fetch mp3 failed, artist_id = %s, song_id = %s' % (artist_id, song_id))
                    return CrawlStatus.FAILED
            except Exception as e:
                logger.exception('[unknown error] fetch_mp3_using_nodejs_api artist_id = %s, song_id = %s, e = %s' % (artist_id, song_id, e))
                return CrawlStatus.FAILED
            except BaseException as e:
                logger.exception('[unnormal error] fetch_mp3_using_nodejs_api artist_id = %s, song_id = %s, e = %s' % (artist_id, song_id, e))
                return CrawlStatus.FAILED

    def run(self):
        while True:
            try:
                (artist_id, song_id, lyric_status, mp3_status) = task_que.get_nowait()
                logger.info('>>>>>> start processing: (artist_id = %s, song_id = %s)' % (artist_id, song_id))

                # get proxies
                # self.proxies = {'http': '110.73.31.223:8123'}

                if lyric_status != CrawlStatus.CRAWLED and (self.ftype == 'lyric' or self.ftype == 'both'):
                    lyric_status = self.fetch_lyric_using_nodejs_api(artist_id, song_id)
                if mp3_status != CrawlStatus.CRAWLED and lyric_status == CrawlStatus.CRAWLED and \
                  (self.ftype == 'mp3' or self.ftype == 'both'):
                    mp3_status = self.fetch_mp3_using_nodejs_api(artist_id, song_id)
                # should be format at (lyric_status, mp3_status, comment, song_id)
                self.res_que.put((lyric_status, mp3_status, '', song_id))
            except queue.Empty:
                logger.info('task queue is empty, sleeping 5s ....')
                time.sleep(5)


class Scheduler():
    def __init__(self, db_client, task_que, res_que, threads, num, ftype):
        self.db_client = db_client
        self.task_que = task_que
        self.res_que = res_que
        self.threads = threads
        self.num = num
        self.ftype = ftype
        self.crawled_cnt = 0
        self.db_client.restore_lyric_jobs()
        self.db_client.restore_mp3_jobs()

    def produce(self, num):
        while task_que.full():
            logger.info('====== Scheduler tasks queue is full, sleeping 3s')
            time.sleep(3)
        query = []
        if self.ftype == 'both':
            query = db_client.query_can_crawl_music_jobs(num)
        elif self.ftype == 'lyric':
            query = db_client.query_can_crawl_lyric_jobs(num)
        elif self.ftype == 'mp3':
            query = db_client.query_can_crawl_mp3_jobs(num)

        tasks = []
        for e in query:
            if not task_que.full():
                task_que.put(e)
                if self.ftype == 'both':
                    tasks.append((CrawlStatus.IN_CRAWLING, CrawlStatus.IN_CRAWLING, '', e[1]))
                elif self.ftype == 'lyric':
                    tasks.append((CrawlStatus.IN_CRAWLING, e[3], '', e[1]))
                elif self.ftype == 'mp3':
                    tasks.append((e[2], CrawlStatus.IN_CRAWLING, '', e[1]))
            else :
                logger.info('====== Scheduler produce tasks queue fulled, %d threads has alive.' % self.num_alive())
                break
        if len(tasks) > 0:
            # should be format at [(lyric_status, mp3_status, comment, song_id)]
            db_client.update_batch_music_jobs(tasks)
            logger.info('====== Scheduler produce %d tasks' % (len(tasks)))

    def collect(self):
        res = []
        while not res_que.empty():
            r = res_que.get()
            res.append(r)
            if (self.ftype == 'both' and r[0] == CrawlStatus.CRAWLED and r[1] == CrawlStatus.CRAWLED)  \
              or (self.ftype == 'lyric' and r[0] == CrawlStatus.CRAWLED) \
              or (self.ftype == 'mp3' and r[1] == CrawlStatus.CRAWLED):
                self.crawled_cnt += 1
                if self.crawled_cnt % 1000 == 0:
                    logger.critical('music_spider has crawled %d musics' % self.crawled_cnt)
        if len(res) > 0:
            # should be format at [(lyric_status, mp3_status, comment, song_id)]
            db_client.update_batch_music_jobs(res)
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
        logger.critical('All worker threads have down, total crawled %d songs.' % self.crawled_cnt)
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
    task_que = Queue(maxsize = 200)
    res_que = Queue()
    db_client = DbClient('free.db')
    ftype = 'mp3'

    threads = []
    for i in range(10):
        t = Crawler(task_que, res_que, ftype)
        t.start()
        threads.append(t)

    s = Scheduler(db_client, task_que, res_que, threads, 20, ftype)
    s.run()
