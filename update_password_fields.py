
import sys
import gzip

from fn_pymapi.errors import PymapiError
import ldap_parser
from common import *


class PasswordUpdater:
    def __init__(self, number_of_accounts, first_account=0):
        self.number_of_accounts = int(number_of_accounts) if number_of_accounts is not None else None
        self.actual_account = 0
        self.first_account = int(first_account)

    def process_entry(self, dn, entry):
        if self.actual_account >= self.first_account:
            if self.number_of_accounts is not None and self.actual_account >= \
                    self.number_of_accounts + self.first_account:
                sys.exit(0)
            try:
                address = entry['cn'][0].decode("utf-8")
            except KeyError:
                return
            if 'userpassword' not in entry:
                return
            payload = dict()
            try:
                payload['userpassword'] = entry['userpassword'][0].decode('utf-8')
            except UnicodeDecodeError:
                payload['userpassword'] = entry['userpassword'][0].decode('latin-1')
            if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
                route = address_route(address)
            elif entry['objectClass'][-1].decode("utf-8") == 'maildomain':
                route = domain_route(address)
            elif entry['objectClass'][-1].decode("utf-8") == 'mailinglist':
                route = mailing_list_route(address)
            else:
                return
            try:
                pmapi_client.make_request('patch', route, payload=payload)
            except PymapiError as err:
                LOGGER.error('PMAPI error: {}'.format(err))
                sys.exit(1)
            else:
                LOGGER.debug('Password fields were modified for account {}'.format(address))
        self.actual_account += 1


def update(dump_file, number_of_accounts=None, first_account=0):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    processing_object = PasswordUpdater(number_of_accounts, first_account)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
