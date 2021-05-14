
import gzip
import ldap_parser

from common import LOGGER
from pattern_handler import PatternHandler, PatternHandlerFactory


class ProblemsDetector:
    def __init__(self, output_file, handler: PatternHandler):
        self.output_file = output_file
        self.handler = handler

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


def detect_wrong_format(pattern_dict: dict, dump_file):
    handler = PatternHandlerFactory(pattern_dict).factory()
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')
    processing_object = ProblemsDetector(output_file, handler)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
