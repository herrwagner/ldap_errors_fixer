
import re
import gzip

import ldap_parser

#_RE_WRONG = re.compile(r'[0-9,a-z,A-Z,.,@]+\,.*$')


class PatternHandler:
    def __init__(self, pattern_dict: dict):
        self.pattern_dict = pattern_dict

    def execute(self, value):
        pass


class PatternHandlerRegEx(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.reg_ex = re.compile(pattern_dict['value'])

    def execute(self, value):
        return self.reg_ex.findall(value)[0]


class PatternHandlerString(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.pattern = re.compile(pattern_dict['value'])

    def execute(self, value):
        return self.pattern == value


class PatternHandlerFactory:
    def __init__(self, pattern_dict):
        self.pattern_dict = pattern_dict

    def factory(self):
        if self.pattern_dict['regex'] is True:
            return PatternHandlerRegEx(self.pattern_dict)
        else:
            return PatternHandlerString(self.pattern_dict)


class ProblemsDetector:
    def __init__(self, output_file, handler: PatternHandler, logger):
        self.output_file = output_file
        self.logger = logger
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
                if field == 'dn':
                    continue
                for value in entry[field]:
                    try:
                        decode_value = value.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    try:
                        wrong_field = self.handler.execute(decode_value)
                    except IndexError:
                        continue
                    else:
                        self.logger.debug('Address {} has wrong field: {}: {}'.format(address, field,
                                                                                      wrong_field))
                        self.output_file.write(address + ' ' + field + ': ' + decode_value + '\n')


def detect_wrong_format(pattern_dict: dict, dump_file, logger):
    handler = PatternHandlerFactory(pattern_dict).factory()
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')
    processing_object = ProblemsDetector(output_file, handler, logger=logger)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
