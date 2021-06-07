
import sys
import gzip
import hashlib
from base64 import b64encode

from fn_pymapi.errors import PymapiError
import ldap_parser
from common import *


def generate_salt(nbytes):
    with open("/dev/urandom", "rb") as rand:
        return rand.read(nbytes)
    # this will start working in python 3.6
    # return secrets.token_bytes(nbytes)


def _cut_base64_padding(byte_str):
    while byte_str.endswith(b'='):
        byte_str = byte_str[:-1]
    return byte_str


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
                user_password = entry['userpassword'][0].decode('utf-8')
            except UnicodeDecodeError:
                user_password = entry['userpassword'][0].decode('latin-1')
            payload['userpasswordssha512'] = self.salted_sha512_pw(user_password)
            payload['userpasswordpdkdf2'] = self.pbkdf2(user_password)
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

    @staticmethod
    def pbkdf2(pwd, salt=None, rounds=10000):
        if isinstance(pwd, str):
            pwd = pwd.encode()
        if not salt:
            salt = generate_salt(16)
        hpw = '{PBKDF2-SHA512}'
        hpw += str(rounds)
        hpw += '$' + _cut_base64_padding(b64encode(salt)).decode()
        hpw += '$' + _cut_base64_padding(b64encode(hashlib.pbkdf2_hmac('sha512', pwd, salt, rounds))).decode()
        return hpw

    @staticmethod
    def salted_sha512_pw(pwd, salt=None):
        if isinstance(pwd, str):
            pwd = pwd.encode()
        salt_len = 8
        if not salt:
            salt = generate_salt(salt_len)
        hpw = '{SSHA512}'
        hpw += b64encode(hashlib.sha512(pwd + salt).digest() + salt).decode()
        return hpw


class PasswordDetector:
    def __init__(self, output_file):
        self.output_file = output_file

    def process_entry(self, dn, entry):
        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            object_class = 'mailaccount'
            address = entry['cn'][0].decode("utf-8")
        else:
            return
        absent_passwords = list()
        if 'userPasswordSsha512' not in entry:
            absent_passwords.append('userPasswordSsha512')
        if 'userPasswordPdkdf2' not in entry:
            absent_passwords.append('userPasswordPdkdf2')
        if len(absent_passwords) > 0:
            LOGGER.debug('Address {} does not have password: {}'.format(address, absent_passwords))
            self.output_file.write('Address {} does not have password: {}'.format(address, absent_passwords))


def open_file(dump_file):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')
    return input_file


def update(dump_file, number_of_accounts=None, first_account=0):
    input_file = open_file(dump_file)
    processing_object = PasswordUpdater(number_of_accounts, first_account)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()


def detect(dump_file):
    input_file = open_file(dump_file)
    output_file = open('address_absent_password.txt', 'w')
    processing_object = PasswordDetector(output_file)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
