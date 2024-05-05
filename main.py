"""
Goal: Learn to interface with postgres database, and (additionally) encrypt/decrypt data. Potential expansion: Create an API
"""


from cryptography.fernet import Fernet
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

    def connect(self, db):
        print(f'Connecting to {db}')
        self.db_engine = create_engine(self.connection_url, pool_recycle=3600)
        self.connection = self.db_engine.connect()

        if passbank.connection != None:
            print(f'{db} connection successful')
        else: print(f'Error connecting to {db}')

        return self.connection

    def find_account(self, account=''):
        # Using parameterized query to avoid SQL injection
        query = '''SELECT account, username, password
                FROM accounts.userpws
                WHERE account = %s;'''
        df = pd.read_sql(query, self.connection, params=(account,))
        
        if not df.empty:
            token = df['password'].iloc[0]  # Extracting the token from the DataFrame
            f = Fernet(load_key())
            decrypted_password = f.decrypt(token.encode()).decode()  # Decrypting the password and decoding from bytes to string
            df['password'] = decrypted_password  # Replace the encrypted password with the decrypted one
            df.index += 1
            df.columns = ['Account', 'Username', 'Password']
            self.entry = df
        else:
            print(f"No account found with the name '{account}'")

    def gather_info(self):
        account = get_account()
        username = get_username()
        token = get_password()
        token_str = token.decode()

        data = {'account': [account], 'username': [username], 'password': [token_str]}
        df = pd.DataFrame(data)
        df.set_index('account', inplace=True)
        return df

    def set_entry(self):
        self.entry = self.gather_info()

    def upsert(self, schema='accounts', table_name='userpws', if_row_exists='update'):
        self.entry = self.gather_info()

        if self.entry is not None:
            upsert(con=self.connection, df=self.entry, schema=schema, table_name=table_name, create_table=True, create_schema=True, if_row_exists=if_row_exists)
            self.connection.commit()  # Commit the transaction
        else:
            print("No entry to upsert.")
   
    def user_interface(self):
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

def write_key(override = False):
    if override == True:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)
    else:
        print('no authorization')

def load_key():
    file = open('key.key', 'rb')
    key = file.read()
    file.close()
    return key

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

def encrypt_pw(password):
    key = load_key()
    f = Fernet(key)
    token = f.encrypt(f'{password}'.encode()) # Encrypt password, creating a Fernet Token object
    return token

def decrypt_pw(token):
    key = load_key()
    f = Fernet(key)
    password = f.decrypt(token) # Decrypt token, creating the original password
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

    token = encrypt_pw(password)
    return token

# test = dev_interface()
# print(test )

db_credentials = {
    'db_username': os.environ.get('db_username'),
    'db_password': os.environ.get('db_password'),
    'db_host': os.environ.get('db_host'),
    'db_port': os.environ.get('db_port'),
    'db_name': os.environ.get('db_name')
}

passbank = Bank(db_credentials) # Create instance of Bank using db_credentials
db = passbank.db_credentials['db_name'] # Assign .env's db_name to db

passbank.connect(db)

passbank.user_interface() # 

print(f'\n{passbank.entry}')

passbank.connection.close()
print(f'\nDisconnected from {db}')
