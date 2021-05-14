
from fn_pymapi.errors import PymapiError
from common import *


def fix_wrong_format(input_file, number_of_accounts):
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
                LOGGER.debug('Fixing parameter {} from account {}'.format(parameter, address))
                try:
                    route = address_route(address)
                except ValueError as err:
                    LOGGER.error('ERROR: {}'.format(err))
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
                        LOGGER.warning('Address {} does not have parameter {}!'.format(address, parameter))
                        continue
                broken_value = data[parameter]
                payload = dict()
                payload[parameter] = list()
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    LOGGER.error('PMAPI error: {}'.format(err))
                    error = True
                    continue
                else:
                    LOGGER.debug('Parameter {} was cleaned for address {}'.format(parameter, address))
                payload[parameter] = broken_value
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    LOGGER.error('PMAPI error: {}'.format(err))
                    error = True
                    continue
                else:
                    LOGGER.debug('Parameter {} was modified for address {}'.format(parameter, address))
