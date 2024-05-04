"""
Goal: Learn to interface with postgres database, and (additionally) encrypt/decrypt data. Potential expansion: Create an API
"""

import os
import pandas as pd
from pangres import upsert
import psycopg2
import secrets
import string
from sqlalchemy import text, create_engine
import sys

from dotenv import load_dotenv
load_dotenv(override=True)

class Bank:
    def __init__(self, db_credentials):
        self.db_credentials = db_credentials
        self.connection_url = f"postgresql+psycopg2://{self.db_credentials['db_username']}:{self.db_credentials['db_password']}@{self.db_credentials['db_host']}:{self.db_credentials['db_port']}/{self.db_credentials['db_name']}"
        # TODO DELETE?  self.action = None
        self.connection = None
        self.entry = None 

    def connect(self):
        self.db_engine = create_engine(self.connection_url, pool_recycle=3600)
        self.connection = self.db_engine.connect()
        return self.connection

    def find_account(self, account='') -> list:
        # Using parameterized query to avoid SQL injection
        query = '''SELECT account, username, password
                FROM gucci.accounts
                WHERE account = %s;'''
        df = pd.read_sql(query, self.connection, params=(account,))
        self.entry = df

    def gather_info(self):
        account = get_account()
        username = get_username()
        password = get_password()

        data = {'account': [account], 'username': [username], 'password': [password]}
        df = pd.DataFrame(data)
        df.set_index('account', inplace=True)
        return df

    def set_entry(self):
        self.entry = self.gather_info()

    def upsert(self, schema='gucci', table_name='accounts', if_row_exists='update'):
        self.entry = self.gather_info()
        if self.entry is not None:
            upsert(con=self.connection, df=self.entry, schema=schema, table_name=table_name, create_table=True, create_schema=True, if_row_exists=if_row_exists)
            self.connection.commit()  # Commit the transaction
        else:
            print("No entry to upsert.")
   
    def get_mode(self):
        '''
        Let user select if they wish to read or write information.
        '''
        modes = ['Add', 'View']
        print('What would you like to do?')
        for num, option in enumerate(modes):
            print(f'{num + 1}. {option}')
        response = input('')
        match response:
            case '1':
                self.upsert()
            case '2':
                #TODO print list of accounts
                account = input('Which account do you wish to view? ')
                self.find_account(account)

def in_venv(): # Set up test file to move this function
    '''
    Compare with the purpose of ensuring that virtual environment is active.
    Works by confirming base environment is not the current environment
    True = Good, venv is active
    '''
    return sys.prefix != sys.base_prefix

def dev_interface(): # Set up test file to move this function
    '''
    Interface with functions designed for testing the environment
    '''
    root_options = ['Test Virtual Environment', 'Blank']

    print('Make a selection:')
    for num, option in enumerate(root_options):
        print(f'{num+1}. {option}')

    user_choice = input().strip()
    user_choice_sanitized = int(user_choice) if user_choice.isdigit() else -1

    match user_choice_sanitized:
        case 1:
            if in_venv():
                response = 'Virtual environment ACTIVE'
            else:
                response = 'Virtual environment ERROR'
        case 2:
            response = 'Placeholder found'
        case _:
            response = dev_interface()
    return response

def get_account() -> str:
    '''
    Specifically asking for the name of the website/business the account is with, NOT username.
    '''
    account = input(("Please enter the name of the website or business you have an account with: "))
    return account

def get_username():
    username = input("Username: ")
    return username

def generate_password() -> str:
    '''
    Generate a random alphanumeric password
    '''
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password

def get_password():
    password = ''
    response = input('Would you like to generate a password? y/n: ')
    match response:
        case 'y':
            password = generate_password()
        case 'n': #TODO Add pw match checking
            password = input('Password: ')
        case _:
            password = get_password()
    return password

# test = dev_interface()
# print(test )

db_credentials = {
    'db_username': os.environ.get('db_username'),
    'db_password': os.environ.get('db_password'),
    'db_host': os.environ.get('db_host'),
    'db_port': os.environ.get('db_port'),
    'db_name': os.environ.get('db_name')
}

passbank = Bank(db_credentials)
db = passbank.db_credentials['db_name']

passbank.connect()
print(f'Connecting to {db}')
if passbank.connection != None:
    print(f'{db} connection successful')
else: print(f'Error connecting to {db}')

passbank.get_mode()

print('\n')
print(passbank.entry)

passbank.connection.close()
print(f'Disconnected from {db}')
