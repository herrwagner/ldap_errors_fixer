
import sys

from common import LOGGER
from pattern_handler import PatternHandlerFactory
from check_entry_mariadb import check_entry_mariadb


class ProblemsDetector:
    def __init__(self, output_file, handler: PatternHandlerFactory):
        self.output_file = output_file
        if handler is not None:
            self.handler = handler.factory()


class ProblemsDetectorGeneral(ProblemsDetector):
    def __init__(self, output_file, handler: PatternHandlerFactory):
        super().__init__(output_file, handler)

    def process_entry(self, dn, entry):
        try:
            address = entry['cn'][0].decode("utf-8")
        except KeyError:
            try:
                address = entry['dn'][0].decode("utf-8")
            except KeyError:
                return
        else:
            for field in entry:
                if self.handler.check_field(field) is False:
                    continue
                for value in entry[field]:
                    try:
                        decode_value = value.decode("utf-8")
                    except UnicodeDecodeError:
                        decode_value = value.decode('latin-1')
                    try:
                        if self.handler.execute(decode_value) is False:
                            continue
                    except IndexError:
                        continue
                    else:
                        LOGGER.debug('Address {} has wrong field: {}: {}'.format(address, field,
                                                                                 decode_value))
                        self.output_file.write(address + ' ' + field + ': ' + decode_value + '\n')


class SubmitLockDetector(ProblemsDetector):
    def __init__(self, output_file, handler: PatternHandlerFactory, mariadb_connection):
        super().__init__(output_file, handler)
        self.mariadb_connection = mariadb_connection
        try:
            self.query = self.handler.pattern_dict['mariadb_query']
        except KeyError:
            LOGGER.error('Provide a MariaDB query!')
            sys.exit(1)

    def process_entry(self, dn, entry):
        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            object_class = 'mailaccount'
            address = entry['cn'][0].decode("utf-8")
            if 'forwardto' in entry:
                LOGGER.debug('Skipping alias account {}'.format(address))
                return
        else:
            LOGGER.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return

        if 'lock' in entry:
            lock = entry['lock'][0].decode("utf-8")
            if lock == 'submit':
                LOGGER.info('Address {} has lock = submit!'.format(address, self.mariadb_connection))
                locking_date = check_entry_mariadb(address, self.mariadb_connection, self.query)
                self.output_file.write(address + ' ' + object_class + ' locking date in MariaDB: ' +
                                       locking_date + '\n')


class AliasDomainDetector(ProblemsDetector):
    def __init__(self, output_file, handler: PatternHandlerFactory):
        super().__init__(output_file, handler)

    def process_entry(self, dn, entry):
        if entry['objectClass'][-1].decode("utf-8") == 'maildomain':
            domain = entry['cn'][0].decode("utf-8")
            if 'forwardto' in entry:
                forward_to = entry['forwardto'][0].decode("utf-8")
                LOGGER.info('Domain account {} is an alias to {}!'.format(domain, forward_to))
                self.output_file.write(domain + ' is an alias to ' + forward_to + '\n')
        else:
            #LOGGER.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return
