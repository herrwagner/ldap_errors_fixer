import sys
import ldap_parser

from common import LOGGER, open_file, domain_route, pmapi_client
from fn_pymapi.errors import PymapiError


NEW_MDBOX = 'mdbox214.freenet.de'


class DircountUpdater:
    def __init__(self, number_of_accounts, first_account=0):
        self.number_of_accounts = int(number_of_accounts) if number_of_accounts is not None else None
        self.actual_account = 0
        self.first_account = int(first_account)
        self.last_account = self.first_account
        self.errors_file = 'errors_file.txt'

    def process_entry(self, dn, entry):
        if self.actual_account >= self.first_account:
            if self.number_of_accounts is not None and self.actual_account >= \
                    self.number_of_accounts + self.first_account:
                sys.exit(0)
            with open(self.errors_file, 'a') as ef:
                try:
                    address = entry['cn'][0].decode("utf-8")
                except KeyError:
                    return
                if entry['objectClass'][-1].decode("utf-8") == 'maildomain':
                    route = domain_route(address)
                else:
                    return
                payload = dict()
                try:
                    dircount = entry['dircount'][0].decode('utf-8')
                except UnicodeDecodeError:
                    dircount = entry['dircount'][0].decode('latin-1')
                if dircount.split()[0] == NEW_MDBOX:
                    return
                payload['dircount'] = {'mailbox': NEW_MDBOX}
                try:
                    #LOGGER.debug('patch {} with payload: {}'.format(route, payload))
                    pmapi_client.make_request('patch', route, payload=payload)
                    pass
                except PymapiError as err:
                    LOGGER.error('PMAPI error: {}'.format(err))
                    ef.write('Account {} failed with error {}'.format(address, err))
                    ef.write("\n")
                else:
                    LOGGER.info('Dircount mdbox was modified for account {}'.format(address))
        self.actual_account += 1
        self.last_account += 1


def update(dump_file, number_of_accounts=None, first_account=0):
    input_file = open_file(dump_file)
    processing_object = DircountUpdater(number_of_accounts, first_account)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
    LOGGER.info('Last account was the number: {}'.format(processing_object.last_account))


