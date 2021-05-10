
from ldif import LDIFParser
import re
import gzip


_RE_WRONG = re.compile(r'^[a-z,A-Z]+:\s[0-9,a-z,A-Z,.,@]+\,.*$')


class ParseLDIF(LDIFParser):
    def __init__(self, input_file, output_file, logger):
        LDIFParser.__init__(self, input_file)
        self.output_file = output_file
        self.logger = logger

    def handle(self, dn, entry):
        self.process_entry(dn, entry)

    def process_entry(self, dn, entry):
        self.logger.debug('Start processing of dn ' + dn)
        self.logger.debug(entry)

        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            address = entry['cn'][0].decode("utf-8")
            for field in entry:
                decode_field = field[0].decode("utf-8")
                try:
                    wrong_field = _RE_WRONG.findall(decode_field)[0]
                except IndexError:
                    continue
                else:
                    self.logger.debug('Address {} has wrong field: {}'.format(address, wrong_field))
                    self.output_file.write(address + ' ' + wrong_field + '\n')
        else:
            self.logger.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return


def detect_wrong_format(dump_file, logger):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')

    parser = ParseLDIF(input_file, output_file, logger=logger)
    parser.parse()
