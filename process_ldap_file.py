
from ldif import LDIFParser

from common import MARIA_DB_CONFIGURATION


class ParseLDIF(LDIFParser):
    def __init__(self, input_file, output_file, mariadb_connection, logger):
        LDIFParser.__init__(self, input_file)
        self.output_file = output_file
        self.logger = logger
        self.mariadb_connection = mariadb_connection

    def handle(self, dn, entry):
        self.process_entry(dn, entry)

    def process_entry(self, dn, entry):
        self.logger.debug('Start processing of dn ' + dn)
        self.logger.debug(entry)

        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            object_class = 'mailaccount'
            address = entry['cn'][0].decode("utf-8")
            if 'forwardto' in entry:
                self.logger.debug('Skipping alias account {}'.format(address))
                return
        else:
            self.logger.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return

        if 'lock' in entry:
            lock = entry['lock'][0].decode("utf-8")
            if lock == 'submit':
                self.logger.debug('Address {} has lock = submit!'.format(address))
                locking_date = self.check_account_history(address)
                self.output_file.write(address + ' ' + object_class + ' locking date in MariaDB: ' +
                                       locking_date + '\n')

    def check_account_history(self, address):
        self.logger.debug('Checking account: {}'.format(address))
        cursor = self.mariadb_connection.cursor()
        query_string = 'SELECT ts FROM {} WHERE account=\'{}\''.format(MARIA_DB_CONFIGURATION['table'], address)
        self.logger.debug('Mariadb query: ' + query_string)
        mariadb_hits = cursor.execute(query_string)

        if mariadb_hits == 0:
            self.logger.debug('Account not found in mariadb during policy period.')
            return 'Not found'
        else:
            result = cursor.fetchone()
            self.logger.debug('MariaDB first result: \n{}'.format(result))
            return result['ts'].strftime("%m/%d/%Y, %H:%M:%S")
