
import re
import gzip
import ldap_parser

from common import LOGGER


class PatternHandler:
    def __init__(self, pattern_dict: dict):
        self.pattern_dict = pattern_dict

    def execute(self, value):
        pass

    def is_all_not_excluded(self, field):
        if self.pattern_dict['field'] == 'All':
            try:
                exclude = self.pattern_dict['exclude']['field']
            except KeyError:
                return True
            else:
                return exclude != field
        else:
            return False

    def check_field(self, field):
        if self.is_all_not_excluded(field) or self.pattern_dict['field'] == field:
            return True
        else:
            return False


class PatternHandlerRegEx(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.reg_ex = re.compile(pattern_dict['value'])

    def execute(self, value):
        return self.reg_ex.findall(value)[0]


class PatternHandlerString(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.pattern = pattern_dict['value']

    def execute(self, value):
        return self.pattern == value


class PatternHandlerFactory:
    def __init__(self, pattern_dict):
        self.pattern_dict = pattern_dict

    def factory(self):
        if self.pattern_dict['regex']:
            return PatternHandlerRegEx(self.pattern_dict)
        else:
            return PatternHandlerString(self.pattern_dict)


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
