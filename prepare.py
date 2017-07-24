
from DbClient import DbClient, CrawlStatus
import os


def add_crawl_jobs(db_client, inputfile, hotfile):

    hot_artists = {}
    max_priority = 199999
    with open(hotfile, 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            artist_id = l[0]
            hot_artists[artist_id] = str(max_priority)
            max_priority -= 10

    with open(inputfile, 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            artist_id = l[0]
            artist_name = l[1]
            priority = hot_artists[artist_id] if artist_id in hot_artists else l[2]
            song_list_path = l[3].strip()

            print('======', priority, line.strip())

            if not os.path.exists(song_list_path):
                print('not extists of %s, %s' % (artist_id, song_list_path))
                continue

            rows = []
            with open(song_list_path, 'r') as fin_s:
                for s in fin_s.readlines():
                    sp = s.split(',')
                    song_id = sp[0]
                    song_name = sp[1].strip()
                    rows.append((artist_id, song_id, song_name, priority, CrawlStatus.INIT, CrawlStatus.INIT))

            db_client.add_music_jobs(rows)

    print('finish add jobs: ', inputfile, hotfile)

def prepare_mp3_jobs():

    # test crawl status
    # print('status = ', CrawlStatus.INIT)
    '''
    create sqlite3 db
    '''
    db_client = DbClient('free.db')
    db_client.create_table_music_jobs()

    '''
    test add jobs
    '''
    # db_client.add_music_jobs([('12', '12', '10000', CrawlStatus.INIT, CrawlStatus.INIT)])

    '''
    add crawl jobs
    '''
    add_crawl_jobs(db_client, 'conf/sorted-artists-songs.txt', 'conf/hot-artists-id-list.csv')

    '''
    test query
    '''
    res = db_client.query_music_jobs(CrawlStatus.INIT, CrawlStatus.INIT, 3)
    print(res)

    '''
    test update
    '''
    db_client.update_single_music_job('415792916', CrawlStatus.CRAWLED, CrawlStatus.CRAWLED, 'test')
    db_client.update_batch_music_jobs([(CrawlStatus.CRAWLED, CrawlStatus.CRAWLED, 'test', '418602084'),
                                   (CrawlStatus.CRAWLED, CrawlStatus.CRAWLED, 'test', '418603076')])

    res = db_client.query_music_jobs(CrawlStatus.CRAWLED, CrawlStatus.CRAWLED, 10)
    print(res)

    db_client.update_batch_music_jobs([(CrawlStatus.INIT, CrawlStatus.INIT, '', '415792916'),
                             (CrawlStatus.INIT, CrawlStatus.INIT, '', '418602084'),
                             (CrawlStatus.INIT, CrawlStatus.INIT, '', '418603076')])

    db_client.close_conn()


def add_artist_jobs(db_client, infile):
    rows = []
    with open(infile, 'r') as fin:
        for line in fin.readlines():
            l = line.split(',')
            artist_id = l[0]
            artist_name = l[1]
            rows.append((artist_id, artist_name, '999', CrawlStatus.INIT))
    db_client.add_artist_jobs(rows)


def prepare_artist_jobs():
    db_client = DbClient('artists.db')
    db_client.create_table_artist_jobs()
    add_artist_jobs(db_client, 'conf/en-artists-id-list.csv')
    db_client.close_conn()

if __name__ == '__main__':
    # prepare_mp3_jobs()
    prepare_artist_jobs()
