import sys
import gzip

import ldap_parser
from common import *
from fn_pymapi.errors import PymapiError

class UserPasswordCramDetector:

    def process_entry(self, dn, entry):
        try:
            address = entry['cn'][0].decode("utf-8")
        except KeyError:
            return
        if 'userPasswordCram' in entry:
            LOGGER.info('Object {} has userpasswordcram! Deleting userpasswordcram...'.format(address))
            payload = dict()
            payload['userpasswordcram'] = ""
            try:
                route = address_route(address)
                pmapi_client.make_request('patch', route, payload=payload)
            except PymapiError as err:
                LOGGER.error('PMAPI error: {}'.format(err))
                sys.exit(1)
            else:
                LOGGER.info('userpasswordcram was deleted for account {}'.format(address))


def delete_userpassword_cram(dump_file):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')
    processing_object = UserPasswordCramDetector()
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
