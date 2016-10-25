import os
import sys
import gnupg
import getpass
import requests


import suds_requests
from suds.client import Client
from suds.wsse import *

from passlib.hash import sha256_crypt

class  gpgkey(object):

    def __init__(self, p_opt):

        self.gpghome = p_opt['gnupghome']
        self.log = p_opt['log_path']

        if not os.path.exists(self.gpghome):
            err = 'No path/file to gnupghome: \'%s\'' % self.gpghome
            if self.log:
                self.log.error(err)
            raise Exception(err)

        self.gpg = gnupg.GPG(gnupghome = self.gpghome)

    def __del__(self):
        if self.gpg:
            del self.gpg

    def import_keyfile(self, key_file_path):
        key_data = None
        try:
            with open(key_file_path, 'r') as f:
                key_data = f.read()
            if key_data:
                result = self.gpg.import_keys(key_data)
                if self.log:
                    self.log.info( 'Imported %d key(s) successfully from %s' % (result.count, key_file_path) )
        except IOError as err:
            if self.log:
                self.log.error('IO error({0}): {1}\n'.format(err.errno, err.strerror))
            raise Exception(err.strerror)


    def validate(self, in_path, out_path):
        q_dir = out_path
        p_dir, p_file = os.path.split(in_path)

        ## get the filename / extension
        q_file = os.path.splitext(p_file)

        if not os.path.isdir(out_path):
            q_dir = p_dir

        return q_dir, q_file

    def decrypt(self, in_path, out_path):

        q_dir, q_file = self.validate(in_path, out_path)

        ## by default keep filename the same
        out_file = os.path.join(q_dir, q_file[0])
        key = None
        status = None
        key = getpass.getpass('Enter cipher key for decrypting \"%s\": ' % in_path) if key is None else key

        try:
            with open(in_path, 'rb') as f:
                status = self.gpg.decrypt_file(f, passphrase = key, output = out_file, always_trust = True)
        except IOError as err:
            if self.log:
                self.log.error('IO error({0}): {1}\n'.format(err.errno, err.strerror))
            raise Exception(err.strerror)

        return status, out_file

    def encrypt(self, in_path, out_path, rec):

        q_dir, q_file = self.validate(in_path, out_path)
        ext = '.gpg'
        out_file = os.path.join ( q_dir, q_file[0] + q_file[1] ) + ext
        status = None
        try:
            with open(in_path, 'rb') as f:
                status = self.gpg.encrypt_file ( f, recipients = rec, output = out_file, always_trust = True )
        except IOError as err:
            if self.log:
                self.log.error('IO error({0}): {1}\n'.format(err.errno, err.strerror))
            raise Exception(err.strerror)

        return status, out_file




class wsdl_client(object):

    def __init__(self, p_opt):

        self.url = 'http://' + p_opt['server'] + ':' + p_opt['port'] + '/PatientEJB/PatientEJBService?wsdl'
        self.log = p_opt['log_path']
        self.user_name = p_opt['user']
        self.add_sec = p_opt['add_security_header']
        self.client = self.http_client()

    ## authenticate module
    def authenticate(self):
        key = 'password1'
        #key = getpass.getpass('Enter password for user \"%s\": ' % self.user_name) if key is None else key
        return key


    ## http session
    def http_client(self):
        http_session = requests.session()
        response = http_session.get(self.url)
        try:
            if response.status_code != 503:
                response.raise_for_status()
        except requests.exception.HTTPError as e:
            sys.stderr.write(e)
            sys.exit(1)
        http_session.auth = (self.user_name, self.authenticate())
        self.client = Client(self.url, faults=False, cachingpolicy=1, location = self.url, transport = suds_requests.RequestsTransport(http_session) )
        if self.add_sec:
            self.add_security_header()
        return self.client



    ## add security header to client
    def add_security_header(self):
        self.security=Security()
        userNameToken=UsernameToken(self.user_name, self.authenticate())
        timeStampToken=Timestamp(validity=600)
        self.security.tokens.append(userNameToken)
        self.security.tokens.append(timeStampToken)
        self.client.set_options(wsse = self.security)

