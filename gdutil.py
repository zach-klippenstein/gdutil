#!/usr/bin/env python
# coding=utf-8

# Requirements (pip):
#   - google-api-python-client
#   - httplib2
#   - python-gflags
#   - keyring

import sys
import gflags
import os
import httplib2
import pdb   # pdb.set_trace()

class Command:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.service = None

    def print_description(self):
        print '\t', self.name, '\t', self.description

    def init_service(self):
        if self.service is None:
            self.service = get_drive_service()

    def run(self):
        raise Exception('Command not implemented')

class Help(Command):
    def __init__(self):
        Command.__init__(self, name='help', description='Show this help')

    def run(self):
        commands = build_commands_list()
        print "Commands:"
        for name in sorted(commands.keys()):
            commands[name].print_description()
        print "Run with -? or --help for other flags."

def get_drive_service():
    """Authenticate to the Google Drive API and return a service object."""
    # See https://developers.google.com/api-client-library/python/guide/aaa_oauth#oauth2client
    import oauth2client
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.keyring_storage import Storage as CredentialStorage
    from oauth2client.tools import run
    from apiclient.discovery import build as build_service

    # For keyring credential storage
    APP_NAME = 'gdutil'
    USER_NAME = os.environ['USER'] or 'default_user'

    CLIENT_SECRETS_FILE = 'client_secrets.json'

    # Check https://developers.google.com/drive/scopes for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
    
    storage = CredentialStorage(APP_NAME, USER_NAME)
    credentials = storage.get()

    if credentials is None:
        try:
            # See https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
            flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, OAUTH_SCOPE)
        except oauth2client.clientsecrets.InvalidClientSecretsError, e:
            print "error: couldn't read client secrets: ", e
            exit(1)

        # See https://developers.google.com/api-client-library/python/guide/aaa_oauth#oauth2client
        credentials = run(flow, storage)

    if credentials is None:
        print "error: couldn't get authorization from Google Drive"
        exit(1)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    drive_service = build_service('drive', 'v2', http=http)
    return drive_service

def find_subclasses_of(base_class):
    import types

    for name in globals():
        obj = globals()[name]
        # Find all subclasses of 
        if obj != Command and type(obj) == types.ClassType and issubclass(obj, Command):
            yield obj

def build_commands_list():
    """Search the global namespace for Command classes, and return them in a dictionary keyed on their names."""
    commands = [command_class() for command_class in find_subclasses_of(Command)]
    return {command.name: command for command in commands}

def main(argv):
    COMMANDS = build_commands_list()

    # Define command-line flags
    # See http://python-gflags.googlecode.com/svn/trunk/gflags.py
    flags = gflags.FLAGS
    gflags.DEFINE_enum('command', 'help', COMMANDS.keys(), "Command to execute. Use 'help' for more info.")
    gflags.MarkFlagAsRequired('command')
    gflags.DECLARE_key_flag('command')

    # Parse flags
    try:
        # Required for oauth2client.tools.run()
        argv = flags(argv)
    except gflags.FlagsError, e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], flags)
        exit(1)

    command = COMMANDS[flags.command]
    command.run()

if __name__ == '__main__':
    main(sys.argv)
