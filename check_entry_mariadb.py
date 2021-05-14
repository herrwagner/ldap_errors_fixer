
import pymysql.cursors

from common import MARIA_DB_CONFIGURATION, LOGGER


class DBError(Exception):
    """Base error class for API stuff."""

    def __init__(self, message=''):
        self.message = message


def open_mdb_connection():
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
                LOGGER.exception(log_str, exc_info=True)
                raise DBError(log_str)
            else:
                LOGGER.warning('Failed to connect to MariaDB on host {}. Trying next host.'.format(host))
        else:
            if connection.open:
                LOGGER.debug('mariadb connection to host {} successful.'.format(host))
                return connection
            else:
                err_str = 'Connection to MariaDB failed.'
                LOGGER.error(err_str)
                raise DBError(err_str)


def check_account_history(address, mariadb_connection):
    LOGGER.debug('Checking account: {}'.format(address))
    cursor = mariadb_connection.cursor()
    query_string = 'SELECT ts FROM {} WHERE account=\'{}\''.format(MARIA_DB_CONFIGURATION['table'], address)
    LOGGER.debug('Mariadb query: ' + query_string)
    mariadb_hits = cursor.execute(query_string)

    if mariadb_hits == 0:
        LOGGER.debug('Account not found in mariadb during policy period.')
        return 'Not found'
    else:
        result = cursor.fetchone()
        LOGGER.debug('MariaDB first result: \n{}'.format(result))
        return result['ts'].strftime("%m/%d/%Y, %H:%M:%S")
