
import logging
import logging.config

class logger:
    logging.config.fileConfig("conf/log.ini")

    # create logger
    logger_name = "test"
    log = logging.getLogger(logger_name)

    @classmethod
    def info(cls, msg):
        cls.log.info(msg)

    @classmethod
    def error(cls, msg):
        cls.log.error(msg)

    @classmethod
    def exception(cls, msg):
        cls.log.exception(msg)

    @classmethod
    def test(cls):
        cls.log.debug('debug message')
        cls.log.info('info message')
        cls.log.warn('warn message')
        cls.log.error('error message')
        cls.log.critical('critical message')
        try:
            1/0
        except:
            cls.log.exception('exception message')

if __name__ == '__main__':
    logger.test()
