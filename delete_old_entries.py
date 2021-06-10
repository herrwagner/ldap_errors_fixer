
import sys
import re
from datetime import datetime, timedelta

from fn_pymapi.errors import PymapiError
from common import *


def check_if_is_older(mariaDB_history_entry, limit_days_ago):
    entry_datetime = datetime.strptime(mariaDB_history_entry, '%d/%m/%Y, %H:%M:%S')
    date_limit = datetime.now() - timedelta(days=int(limit_days_ago))
    if entry_datetime < date_limit:
        LOGGER.debug('MariadDB entry: {} is older than limit!'.format(entry_datetime))
        return True
    else:
        LOGGER.debug('MariadDB entry: {} is newer than limit!'.format(entry_datetime))
        return False


def delete_old_entries(input_file, number_of_accounts=None, limit_days_ago=None):
    accounts_deleted_file = re.sub(r'\..*', '', input_file)
    accounts_deleted_file += '_deleted_accounts.txt'
    with open(input_file, 'r') as f:
        lines = f.readlines()
    with open(input_file, "w") as f, open(accounts_deleted_file, 'w') as b:
        delete_counter = 0
        for line in lines:
            if number_of_accounts is not None and delete_counter >= int(number_of_accounts):
                f.write(line)
            else:
                delete_counter += 1
                address = line.split(' ')[0]
                mariaDB_history_entry = line.split('MariaDB: ')[1]
                LOGGER.info('Checking account {} with MariaDB history entry {}'.format(address, mariaDB_history_entry))
                if mariaDB_history_entry.strip() != 'Not found':
                    if limit_days_ago is None or check_if_is_older(mariaDB_history_entry, int(limit_days_ago)) is False:
                        continue
                LOGGER.info('Proceeding to remove lock for account {}'.format(address))

                try:
                    route = address_route(address)
                except ValueError as err:
                    LOGGER.error('ERROR: {}'.format(err))
                    return
                # Double check to be sure that it is not an alias account
                try:
                    ret = pmapi_client.make_request('get', route)
                except PymapiError as err:
                    print('PMAPI error: {}'.format(err))
                    continue
                else:
                    data = ret.json()['data']
                    if 'forwardto' in data:
                        LOGGER.warning('Address {} is an alias account!'.format(address))
                        continue
                payload = dict()
                payload['lock'] = ""
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    LOGGER.error('PMAPI error: {}'.format(err))
                    sys.exit(1)
                else:
                    LOGGER.info('Lock -> Submit was deleted for account {}'.format(address))
                    b.write(line)
