import sys
import gzip
import time

import ldap_parser
from common import *
from fn_pymapi.errors import PymapiError


class UserPasswordCramDetector:
    def __init__():
        errors_file = 'errors_deleting_cram.txt'
        ef = open(errors_file, 'w')

    def process_entry(self, dn, entry):
        try:
            address = entry['cn'][0].decode("utf-8")
        except KeyError:
            return
        if 'userPasswordCram' in entry:
            LOGGER.info('Object {} has userpasswordcram! Deleting userpasswordcram...'.format(address))
            try:
                route = address_field_route(address, 'userpasswordcram')
            except:
                try:
                    route = domain_route(address)
                except:
                    LOGGER.info('Account {} is not type mailbox, alias or domain. Skipped.'.format(address))
                    self.ef.write('Account {} is not type mailbox, alias or domain. Skipped.'.format(address))
                    self.ef.write('\n')
                    return
                else:
                    account_type = 'domain'
            else:
                account_type = 'address'
            try:
                if account_type == 'address':
                    pmapi_client.make_request('delete', route)
                else:
                    payload = dict()
                    payload['userpasswordcram'] = ""
                    pmapi_client.make_request('patch', route, payload=payload)
            except PymapiError as err:
                LOGGER.error('PMAPI error: {}'.format(err))
                self.ef.write(address)
                self.ef.write('\n')
            else:
                LOGGER.info('userpasswordcram was deleted for account {}'.format(address))
            time.sleep(0.1)


def delete_userpassword_cram(dump_file):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')
    processing_object = UserPasswordCramDetector()
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
