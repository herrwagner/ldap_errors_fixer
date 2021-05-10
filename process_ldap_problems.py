
from ldif import LDIFParser
import re
import gzip


_RE_WRONG = re.compile(r'[0-9,a-z,A-Z,.,@]+\,.*$')


class ParseLDIF(LDIFParser):
    def __init__(self, input_file, output_file, logger):
        LDIFParser.__init__(self, input_file)
        self.output_file = output_file
        self.logger = logger

    def handle(self, dn, entry):
        self.process_entry(dn, entry)

    def process_entry(self, dn, entry):
        self.logger.debug('Start processing of dn ' + dn)
        try:
             address = entry['cn'][0].decode("utf-8")
        except KeyError:
            return
        else:
            try:
                forwardto = entry['forwardto']
            except KeyError:
                return
            else:
                for _forwardto in forwardto:
                    decode_value = _forwardto.decode("utf-8")
                    try:
                        wrong_field = _RE_WRONG.findall(decode_value)[0]
                    except IndexError:
                        continue
                    else:
                        self.logger.debug('Address {} has wrong field: {}: {}'.format(address, 'forwardto', wrong_field))
                        self.output_file.write(address + ' ' + 'forwardto' + ': ' + decode_value + '\n')


def detect_wrong_format(dump_file, logger):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')

    parser = ParseLDIF(input_file, output_file, logger=logger)
    parser.parse()
