
import sys
import gzip
import ldap_parser

from common import LOGGER
from pattern_handler import PatternHandlerFactory
from problems_detector import *
from check_entry_mariadb import open_mdb_connection


def processing_object_builder(type, output_file, handler):
    if type == 'general':
        return ProblemsDetectorGeneral(output_file, handler)
    elif type == 'lock_submit':
        return SubmitLockDetector(output_file, handler, mariadb_connection=open_mdb_connection())
    else:
        LOGGER.error("Introduce a defined type in the configuration file!")
        sys.exit(1)


def detect_wrong_format(pattern_dict: dict, dump_file):
    try:
        type = pattern_dict['type']
    except KeyError:
        LOGGER.error("Introduce a type in the configuration file!")
        sys.exit(1)

    handler = PatternHandlerFactory(pattern_dict).factory()
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('ldap_wrong_format.txt', 'w')
    processing_object = processing_object_builder(type, output_file, handler)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
