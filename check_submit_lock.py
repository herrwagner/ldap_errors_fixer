
import gzip
import logging
import pymysql.cursors
from logging.handlers import SysLogHandler

from common import MARIA_DB_CONFIGURATION
import process_ldap_file


# logging:
#logger = logging.getLogger('free_submit_log')
#log_handler = SysLogHandler('/dev/log')
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#log_handler.setFormatter(formatter)
#logger.addHandler(log_handler)
#logger.setLevel(logging.DEBUG)


class DBError(Exception):
    """Base error class for API stuff."""

    def __init__(self, message=''):
        self.message = message


def open_mdb_connection(logger):
    for host in MARIA_DB_CONFIGURATION['hosts']:
        try:
            connection = pymysql.connect(
                user=MARIA_DB_CONFIGURATION['user'],
                password=MARIA_DB_CONFIGURATION['password'],
                database=MARIA_DB_CONFIGURATION['database'],
                host=host,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        except:
            if host == MARIA_DB_CONFIGURATION['hosts'][-1]:
                log_str = "Failed to connect to any MariaDB host"
                logger.exception(log_str, exc_info=True)
                raise DBError(log_str)
            else:
                logger.warning('Failed to connect to MariaDB on host {}. Trying next host.'.format(host))
        else:
            if connection.open:
                logger.debug('mariadb connection to host {} successful.'.format(host))
                return connection
            else:
                err_str = 'Connection to MariaDB failed.'
                logger.error(err_str)
                raise DBError(err_str)


def check_submit_locks(dump_file, logger):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('lock_submit_accounts.txt', 'w')

    parser = process_ldap_file.ParseLDIF(input_file, output_file,
                                         mariadb_connection=open_mdb_connection(logger),
                                         logger=logger)
    parser.parse()

