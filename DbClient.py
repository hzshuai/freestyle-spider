import sqlite3

class CrawlStatus:
    INIT = 'INIT'
    IN_CRAWLING = 'IN_CRAWLING'
    NOT_FOUND = 'NOT_FOUND'
    CRAWLED = 'CRAWLED'
    FAILED = 'FAILED'

class DbClient:

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)

    def close_conn(self):
        self.conn.close()

    def create_table_music_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute('drop table if exists music_jobs')
        cursor.execute('''
                create table music_jobs
                (artist_id varchar(20),
                song_id varchar(20) primary key,
                song_name varchar(255),
                priority int,
                lyric_status varchar(20),
                mp3_status varchar(20),
                comment varchar(255),
                updated varchar(255))
                '''
                )
        cursor.close()
        self.conn.commit()
        print("create table music_jobs .....")

    def add_music_jobs(self, rows):
        cursor = self.conn.cursor()
        sql = '''
            insert into music_jobs (artist_id, song_id, song_name, priority, lyric_status, mp3_status, comment, updated) values
            (?, ?, ?, ?, ?, ?, "", datetime("now"))
            '''
        cursor.executemany(sql, rows)
        cursor.close()
        self.conn.commit()

    def create_table_artist_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute('drop table if exists artist_jobs')
        cursor.execute('''
                create table artist_jobs
                (artist_id varchar(32) primary key,
                artist_name varchar(255),
                priority int,
                status varchar(32),
                comment varchar(255),
                updated varchar(255))
                '''
                )
        cursor.close()
        self.conn.commit()
        print("create table artist_jobs .....")

    def add_artist_jobs(self, rows):
        cursor = self.conn.cursor()
        sql = '''
            insert into artist_jobs (artist_id, artist_name, priority, status, comment, updated) values
            (?, ?, ?, ?, "", datetime("now"))
            '''
        cursor.executemany(sql, rows)
        cursor.close()
        self.conn.commit()

    def restore_artist_jobs(self):
        cursor = self.conn.cursor()
        sql = '''
            update artist_jobs set status = 'INIT' where status = 'IN_CRAWLING'
        '''
        cursor.execute(sql % str(limit))
        print('restore_artist_jobs: %d' % cursor.rowcount)
        cursor.close()
        self.conn.commit()

    def query_need_crawl_artist_jobs(self, limit = 2):
        cursor = self.conn.cursor()
        sql = '''
            select artist_id, status from artist_jobs
            where status in ('FAILED', 'INIT')
            order by priority desc
            limit %s
        '''
        cursor.execute(sql % str(limit))
        res = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        return res

    def update_batch_artist_jobs(self, rows):
        cursor = self.conn.cursor()
        sql = '''
            update artist_jobs set status = ?, comment = ?, updated = datetime("now")
            where artist_id = ?
        '''
        cursor.executemany(sql, rows)
        cursor.close()
        self.conn.commit()

    def query_music_jobs(self, lyric_status, mp3_status, limit = 2):
        cursor = self.conn.cursor()
        sql = '''
            select artist_id, song_id, lyric_status, mp3_status from music_jobs
            where lyric_status = ? and mp3_status = ?
            order by priority desc
            limit ?
        '''
        cursor.execute(sql, (lyric_status, mp3_status, str(limit)))
        res = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        return res

    def query_can_crawl_music_jobs(self, limit = 2):
        cursor = self.conn.cursor()
        sql = '''
            select artist_id, song_id, lyric_status, mp3_status from music_jobs
            where lyric_status not in ('NOT_FOUND', 'CRAWLED')
                or (lyric_status = 'CRAWLED' and mp3_status not in  ('NOT_FOUND', 'CRAWLED') )
            order by priority desc
            limit %s
        '''
        cursor.execute(sql % str(limit))
        res = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        return res

    def restore_lyric_jobs(self):
        cursor = self.conn.cursor()
        sql = '''
            update music_jobs set lyric_status = 'INIT', mp3_status = 'INIT'
            where lyric_status = 'IN_CRAWLING'
        '''
        cursor.execute(sql)
        print('restore_lyric_jobs: %d' % cursor.rowcount)
        cursor.close()
        self.conn.commit()

    def restore_mp3_jobs(self):
        cursor = self.conn.cursor()
        sql = '''
            update music_jobs set mp3_status = 'INIT' where mp3_status = 'IN_CRAWLING'
        '''
        cursor.execute(sql)
        print('restore_mp3_jobs: %d' % cursor.rowcount)
        cursor.close()
        self.conn.commit()

    def query_can_crawl_lyric_jobs(self, limit = 2):
        cursor = self.conn.cursor()
        sql = '''
            select artist_id, song_id, lyric_status, mp3_status from music_jobs
            where lyric_status in ('INIT', 'FAILED')
            order by priority desc
            limit %s
        '''
        cursor.execute(sql % str(limit))
        res = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        return res

    def query_can_crawl_mp3_jobs(self, limit = 2):
        cursor = self.conn.cursor()
        sql = '''
            select artist_id, song_id, lyric_status, mp3_status from music_jobs
            where (lyric_status = 'CRAWLED' and mp3_status in ('INIT', 'FAILED') )
            order by priority desc
            limit %s
        '''
        cursor.execute(sql % str(limit))
        res = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        return res

    def update_batch_music_jobs(self, rows):
        cursor = self.conn.cursor()
        sql = '''
            update music_jobs set lyric_status = ?, mp3_status = ?, comment = ?, updated = datetime("now")
            where song_id = ?
        '''
        cursor.executemany(sql, rows)
        cursor.close()
        self.conn.commit()

    def update_single_music_job(self, song_id, lyric_status, mp3_status, comment = ''):
        self.update_batch_music_jobs([(lyric_status, mp3_status, comment, song_id)])


if __name__ == '__main__':
    '''
    create, test and load data, see `prepare.py`
    '''
