
from ldif import LDIFParser
import re
import gzip
import sys

from fn_pymapi.errors import PymapiError
from common import *

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


def fix_wrong_format(input_file, logger, number_of_accounts):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    with open(input_file, "w") as f:
        delete_counter = 0
        error = False
        for line in lines:
            if delete_counter >= number_of_accounts or error is True:
                f.write(line)
            else:
                delete_counter += 1
                address = line.split(' ')[0]
                parameter = line.split(' ')[1]
                parameter = parameter.replace(':', '')
                logger.debug('Fixing parameter {} from account {}'.format(parameter, address))
                try:
                    route = address_route(address)
                except ValueError as err:
                    logger.error('ERROR: {}'.format(err))
                    return
                # Get the data from the parameter from LDAP insteod of the file to be sure that
                # is still broken
                try:
                    ret = pmapi_client.make_request('get', route)
                except PymapiError as err:
                    print('PMAPI error: {}'.format(err))
                    continue
                else:
                    data = ret.json()['data']
                    if parameter not in data:
                        logger.warning('Address {} does not have parameter {}!'.format(address, parameter))
                        continue
                broken_value = data[parameter]
                payload = dict()
                payload[parameter] = list()
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    logger.error('PMAPI error: {}'.format(err))
                    error = True
                    continue
                else:
                    logger.debug('Parameter {} was cleaned for address {}'.format(parameter, address))
                payload[parameter] = broken_value
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    logger.error('PMAPI error: {}'.format(err))
                    error = True
                    continue
                else:
                    logger.debug('Parameter {} was modified for address {}'.format(parameter, address))
