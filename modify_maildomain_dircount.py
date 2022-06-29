import sys
import ldap_parser

from common import LOGGER, open_file, domain_route, pmapi_client
from fn_pymapi.errors import PymapiError


NEW_MDBOX = 'mdbox128.freenet.de'


class DircountUpdater:
    def __init__(self, number_of_accounts, first_account=0):
        self.number_of_accounts = int(number_of_accounts) if number_of_accounts is not None else None
        self.actual_account = 0
        self.first_account = int(first_account)
        self.tracking_file = 'password_modified_accounts.txt'

        def process_entry(self, dn, entry):
            if self.actual_account >= self.first_account:
                if self.number_of_accounts is not None and self.actual_account >= \
                        self.number_of_accounts + self.first_account:
                    sys.exit(0)
                with open(self.tracking_file, 'w') as tf:
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
                        mdbox = entry['dircount'][0].decode('utf-8')
                    except UnicodeDecodeError:
                        mdbox = entry['dircount'][0].decode('latin-1')
                    if mdbox == NEW_MDBOX:
                        return
                    payload['dircount'] = {'mailbox': NEW_MDBOX}
                    try:
                        #pmapi_client.make_request('patch', route, payload=payload)
                        pass
                    except PymapiError as err:
                        LOGGER.error('PMAPI error: {}'.format(err))
                        sys.exit(1)
                    else:
                        LOGGER.debug('Password fields were modified for account {}'.format(address))
                        tf.write(address)
                        tf.write("\n")
            self.actual_account += 1


def update(dump_file, number_of_accounts=None, first_account=0):
    input_file = open_file(dump_file)
    processing_object = DircountUpdater(number_of_accounts, first_account)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
