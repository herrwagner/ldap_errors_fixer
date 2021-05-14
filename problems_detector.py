
from common import LOGGER
from pattern_handler import PatternHandler
from check_entry_mariadb import check_account_history


class ProblemsDetector:
    def __init__(self, output_file, handler: PatternHandler):
        self.output_file = output_file
        self.handler = handler


class ProblemsDetectorGeneral(ProblemsDetector):
    def __init__(self, output_file, handler: PatternHandler):
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
                        continue
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
    def __init__(self, output_file, handler: PatternHandler, mariadb_connection):
        super().__init__(output_file, handler)
        self.mariadb_connection = mariadb_connection

    def process_entry(self, dn, entry):
        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            object_class = 'mailaccount'
            address = entry['cn'][0].decode("utf-8")
            if 'forwardto' in entry:
                #LOGGER.debug('Skipping alias account {}'.format(address))
                return
        else:
            #LOGGER.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return

        if 'lock' in entry:
            lock = entry['lock'][0].decode("utf-8")
            if lock == 'submit':
                LOGGER.debug('Address {} has lock = submit!'.format(address, self.mariadb_connection))
                locking_date = check_account_history(address, self.mariadb_connection)
                self.output_file.write(address + ' ' + object_class + ' locking date in MariaDB: ' +
                                       locking_date + '\n')
