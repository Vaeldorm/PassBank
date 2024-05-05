from cryptography.fernet import Fernet
import os
import pandas as pd
from pangres import upsert
import psycopg2
import secrets
import string
from sqlalchemy import create_engine
import sys

from dotenv import load_dotenv
load_dotenv(override=True)

class Bank:
    """
    A class representing a bank with methods to interact with a PostgreSQL database.
    """
    def __init__(self, db_credentials):
        """
        Initializes the Bank object.

        Args:
            db_credentials (dict): A dictionary containing database connection credentials.
        """
        self.db_credentials = db_credentials
        self.connection_url = f"postgresql+psycopg2://{self.db_credentials['db_username']}:{self.db_credentials['db_password']}@{self.db_credentials['db_host']}:{self.db_credentials['db_port']}/{self.db_credentials['db_name']}"
        self.connection = None
        self.entry = None 

    def connect(self, db):
        """
        Connects to the specified PostgreSQL database.

        Args:
            db (str): The name of the database to connect to.

        Returns:
            SQLAlchemy Engine: The database engine.
        """
        print(f'Connecting to {db}')
        self.db_engine = create_engine(self.connection_url, pool_recycle=3600)
        self.connection = self.db_engine.connect()

        if self.connection is not None:
            print(f'{db} connection successful')
        else:
            print(f'Error connecting to {db}')

        return self.connection

    def find_account(self, account=''):
        """
        Finds an account in the database.

        Args:
            account (str): The name of the account to search for.

        Returns:
            DataFrame: A DataFrame containing the account information.
        """
        query = '''SELECT account, username, password
                   FROM accounts.userpws
                   WHERE account = %s;'''
        df = pd.read_sql(query, self.connection, params=(account,))
        
        if not df.empty:
            token = df['password'].iloc[0]
            f = Fernet(load_key())
            decrypted_password = f.decrypt(token.encode()).decode()
            df['password'] = decrypted_password
            df.index += 1
            df.columns = ['Account', 'Username', 'Password']
            self.entry = df
        else:
            print(f"No account found with the name '{account}'")

    def gather_info(self):
        """
        Gathers account information from user input.

        Returns:
            DataFrame: A DataFrame containing the gathered account information.
        """
        account = get_account()
        username = get_username()
        token = get_password()
        token_str = token.decode()

        data = {'account': [account], 'username': [username], 'password': [token_str]}
        df = pd.DataFrame(data)
        df.set_index('account', inplace=True)
        return df

    def set_entry(self):
        """
        Sets the entry attribute with gathered account information.
        """
        self.entry = self.gather_info()

    def upsert(self, schema='accounts', table_name='userpws', if_row_exists='update'):
        """
        Upserts account information into the database.

        Args:
            schema (str): The schema name.
            table_name (str): The table name.
            if_row_exists (str): Specifies the action to take if a row already exists.
        """
        self.entry = self.gather_info()

        if self.entry is not None:
            upsert(con=self.connection, df=self.entry, schema=schema, table_name=table_name, create_table=True, create_schema=True, if_row_exists=if_row_exists)
            self.connection.commit()
        else:
            print("No entry to upsert.")
   
    def user_interface(self):
        """
        Provides a user interface for interacting with the bank.
        """
        modes = ['Add', 'View']
        print('What would you like to do?')
        for num, option in enumerate(modes):
            print(f'{num + 1}. {option}')
        response = input('')
        match response:
            case '1':
                self.upsert()
            case '2':
                account = input('Which account do you wish to view? ')
                self.find_account(account)

def write_key(override=False):
    """
    Writes a key file for encryption.

    Args:
        override (bool): Whether to override an existing key file.
    """
    if override:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)
    else:
        print('no authorization')

def load_key():
    """
    Loads the encryption key from a key file.

    Returns:
        bytes: The encryption key.
    """
    file = open('key.key', 'rb')
    key = file.read()
    file.close()
    return key

def in_venv():
    """
    Checks if the current environment is a virtual environment.

    Returns:
        bool: True if in a virtual environment, False otherwise.
    """
    return sys.prefix != sys.base_prefix

def dev_interface():
    """
    Provides a development interface for testing the environment.

    Returns:
        str: A message indicating the status of the environment.
    """
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
    """
    Asks the user for the name of the account.

    Returns:
        str: The name of the account.
    """
    account = input(("Please enter the name of the website or business you have an account with: "))
    return account

def get_username():
    """
    Asks the user for the username.

    Returns:
        str: The username.
    """
    username = input("Username: ")
    return username

def generate_password() -> str:
    """
    Generates a random alphanumeric password.

    Returns:
        str: The generated password.
    """
    alphabet = string.ascii_letters + string.digits
    while True: #TODO add symbols to generated passwords
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password

def encrypt_pw(password):
    """
    Encrypts a password.

    Args:
        password (str): The password to encrypt.

    Returns:
        bytes: The encrypted password.
    """
    key = load_key()
    f = Fernet(key)
    token = f.encrypt(f'{password}'.encode())
    return token

def decrypt_pw(token):
    """
    Decrypts a password.

    Args:
        token (bytes): The encrypted password token.

    Returns:
        str: The decrypted password.
    """
    key = load_key()
    f = Fernet(key)
    password = f.decrypt(token)
    return password

def get_password():
    """
    Asks the user for a password and encrypts it.

    Returns:
        bytes: The encrypted password.
    """
    password = ''
    response = input('Would you like to generate a password? y/n: ')
    match response:
        case 'y':
            password = generate_password()
        case 'n':
            password = input('Password: ')
        case _:
            password = get_password()

    token = encrypt_pw(password)
    return token

db_credentials = {
    'db_username': os.environ.get('db_username'),
    'db_password': os.environ.get('db_password'),
    'db_host': os.environ.get('db_host'),
    'db_port': os.environ.get('db_port'),
    'db_name': os.environ.get('db_name')
}

passbank = Bank(db_credentials)
db = passbank.db_credentials['db_name']

passbank.connect(db)
passbank.user_interface()
print(f'\n{passbank.entry}')
passbank.connection.close()
print(f'\nDisconnected from {db}')
