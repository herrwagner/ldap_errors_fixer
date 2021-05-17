
import sys
import gzip

from fn_pymapi.errors import PymapiError
import ldap_parser
from common import *


class PasswordUpdater:
    def __init__(self, number_of_accounts):
        self.number_of_accounts = int(number_of_accounts) if number_of_accounts is not None else None
        self.actual_account = 0

    def process_entry(self, dn, entry):
        if self.number_of_accounts is not None:
            if self.actual_account >= self.number_of_accounts:
                sys.exit(0)
            else:
                self.actual_account += 1
        try:
            address = entry['cn'][0].decode("utf-8")
        except KeyError:
            return
        if 'userpassword' not in entry:
            return
        payload = dict()
        payload['userpassword'] = entry['userpassword'][0].decode()
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


def update(dump_file, number_of_accounts=None):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    processing_object = PasswordUpdater(number_of_accounts)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
