
import re
import gzip

import ldap_parser

_RE_WRONG = re.compile(r'[0-9,a-z,A-Z,.,@]+\,.*$')


class ProblemsDetector:
    def __init__(self, output_file, logger):
        self.output_file = output_file
        self.logger = logger

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
                if field == 'dn':
                    continue
                for value in entry[field]:
                    try:
                        decode_value = value.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    try:
                        wrong_field = _RE_WRONG.findall(decode_value)[0]
                    except IndexError:
                        continue
                    else:
                        self.logger.debug('Address {} has wrong field: {}: {}'.format(address, field,
                                                                                      wrong_field))
                        self.output_file.write(address + ' ' + field + ': ' + decode_value + '\n')


def detect_wrong_format(dump_file, logger):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')
    processing_object = ProblemsDetector(output_file, logger=logger)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
