"""
Goal: Learn to interface with postgres database, and (additionally) encrypt/decrypt data. Potential expansion: Create an API
"""

import pandas as pd
import secrets
import string
import sys


def in_venv():
    '''
    Compare with the purpose of ensuring that virtual environment is active.
    Works by confirming base environment is not the current environment
    True = Good, venv is active
    '''
    return sys.prefix != sys.base_prefix

def dev_interface():
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
    response = input('Would you like to generate a password? y/n')
    match response:
        case 'y':
            password = generate_password()
        case 'n':
            password = input()
        case _:
            password = get_password()
    return password

def add(account):
    entry_data = []
    entry_data.append(account)
    entry_data.append(get_username)
    entry_data.append(get_password)
    df = pd.DataFrame(entry_data)
    return entry_data

def view():
    '''
    Retrieve username and password from database for a selected account.
    '''
    pass

def get_mode():
    '''
    Let user select if they wish to read or write information.
    '''
    modes = ['Add', 'View']
    response = input('What would you like to do?')
    for num, option in enumerate(modes):
        print(f'{num}. {option}')
    match response:
        case '1':
            info = add()
        case '2':
            info = view()
    return info

test = dev_interface()
print(test )
