import json
import os
import sqlite3
from getpass import getpass
import zipfile
import requests
import time

session_user = None
EXCUSER_API = 'https://excuser.herokuapp.com/v1'

def clear():
    os.system('clear')

def print_menu():
    clear()
    print('*** Excuser ***\n')
    print('[1] Login')
    print('[2] Register')
    print('[3] About')
    print('[4] Export data')
    print('[5] Get random excuse')
    print('[6] Get a random excuse by category')
    print('[7] My favorites excuses')
    print('[0] Sair')
    print('\n')

def user_option():
    menu_options = {
        '1': login,
        '2': register,
        '3': about,
        '4': export_data_to_json,
        '5': get_random_excuse,
        '6': get_random_excuse_by_category,
        '7': show_user_favorites_excuses,
        '0': logout
    }

    print_menu()
    opt = input('Escolha uma opção do menu: ')
    if not opt in menu_options:
        clear()
        input('Opção inválida ')
        user_option()
        return

    clear()
    menu_options[opt]()
    user_option()

def login():
    username = input('username: ')

    cursor.execute(f"SELECT id, password FROM users WHERE username = '{username}';")

    users = cursor.fetchall()

    if len(users) > 0:
        password = getpass('password: ')
        if  password != users[0][1]:
            input('Incorrect password ')
            login()
        else:
            global session_user
            session_user = users[0]
    else:
        input('User not found ')
        login()

    return

def logout():
    exit()

def register():
    while True:
        username = input('Choose a username: ')
        
        cursor.execute(f"SELECT id FROM users WHERE username = '{username}';")

        if len(cursor.fetchall()) > 0:
            print('Username already in use')
        else:
            break

    password = getpass('Choose a password: ')

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f""" INSERT INTO users (username, password, created_at)
                        VALUES ('{username}', '{password}', '{now}');
    """)

    conn.commit()
    login()

def about():
    print('Excuser App - This application gives you excuses for different areas of life')
    print('Authors: Davi Santoro Stocco - RA: ')
    input()

def export_data_to_json():
    cursor.execute("""SELECT name FROM sqlite_schema WHERE type ='table' AND name NOT LIKE 'sqlite_%';""")   
    tables = list(map(lambda table: table[0], cursor.fetchall()))
    
    zip_file_path = 'database.zip'
    with zipfile.ZipFile(zip_file_path, 'w') as zipF:
        for table in tables:
            table_data = export_table_data(table)
            file_path = f'{table}.json'
            f = open(file_path, 'w')
            f.write(json.dumps({f"{table}": table_data}))
            f.close()
            zipF.write(file_path, compress_type=zipfile.ZIP_DEFLATED)
            os.remove(file_path)
    
    print(f"Dados exportados com sucesso > {zip_file_path}")
    input()

def export_table_data(table):
    cursor.execute(f"PRAGMA table_info({table});")
    columns = list(map(lambda column: column[1], cursor.fetchall()))
    cursor.execute(f"SELECT * FROM {table};")
    table_data = cursor.fetchall()

    def row_with_columns(row):
        dct = {}
        for i, column in enumerate(row):
            dct[columns[i]] = column
        return dct

    return list(map(lambda row: row_with_columns(row), table_data))

def get_random_excuse():
    r = requests.get(f"{EXCUSER_API}/excuse")
    data = r.json()[0]
    print_excuse(data['category'], data['excuse'])
    if input('Favorite excuse (Y/n) ') != 'n':
        favorite_excuse(data)

def print_excuse(category, excuse):
    print("{:<10} {}".format('Category:', category))
    print("{:<10} {}\n".format('Excuse:', excuse))

def get_random_excuse_by_category():
    categories = {
        '1': 'family',
        '2': 'office',
        '3': 'children',
        '4': 'college',
        '5': 'party',
    }

    print('[1] Family')
    print('[2] Office')
    print('[3] Children')
    print('[4] College')
    print('[5] Party')
    
    opt = input('Choose a category: ')
    if not opt in categories:
        clear()
        input('Opção inválida ')
        clear()
        get_random_excuse_by_category()
        return

    clear()
    category = categories[opt]
    r = requests.get('https://excuser.herokuapp.com/v1/excuse/' + category)
    data = r.json()[0]
    print_excuse(data['category'], data['excuse'])

    if input('Favorite excuse (Y/n) ') != 'n':
        favorite_excuse(data)

def favorite_excuse(data):
    excuse = get_excuse_by_external_code(data['id'])

    if excuse:
        insert_favorite_excuse(session_user[0], excuse[0])
    else:
        insert_excuse(data)
        excuse = get_excuse_by_external_code(data['id'])
        insert_favorite_excuse(session_user[0], excuse[0])

# DATABASE FUNCTIONS
def get_excuse_by_external_code(code):
    cursor.execute(f"SELECT id FROM excuses WHERE external_code = '{code}';")
    excuses = cursor.fetchall()
    return excuses[0] if len(excuses) > 0 else None

def insert_excuse(data):
      now = time.strftime("%Y-%m-%d %H:%M:%S")
      cursor.execute(f""" INSERT INTO excuses (external_code, category, text, created_at)
                        VALUES ('{data['id']}', '{data['category']}', '{data['excuse'].replace("'", "''")}', '{now}');
                        """)
      conn.commit()

def insert_favorite_excuse(user_id, excuse_id):
    cursor.execute(f"""SELECT id FROM users_favorites_excuses 
                        WHERE excuse_id = {excuse_id}
                        AND user_id = {user_id}""")
    if len(cursor.fetchall()) > 0:
        return

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f""" INSERT INTO users_favorites_excuses (user_id, excuse_id, created_at)
                        VALUES ('{user_id}', '{excuse_id}', '{now}');
                    """)
    conn.commit()

def show_user_favorites_excuses():
    cursor.execute(f""" SELECT e.category, e.text FROM users_favorites_excuses ufe
                        JOIN excuses e on e.id = ufe.excuse_id
                        WHERE ufe.user_id = {session_user[0]}
                    """)
    user_excuses = cursor.fetchall()
    for excuse in user_excuses:
        print_excuse(excuse[0], excuse[1])
    input()

def create_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at DATE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS excuses (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            external_code VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            text TEXT NOT NULL,
            created_at DATE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users_favorites_excuses (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            excuse_id INTEGER NOT NULL,
            created_at DATE NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(excuse_id) REFERENCES excuses(id)
    );
    """)

# PROGRAM STARTS
clear()
conn = sqlite3.connect('excuser.db')
cursor = conn.cursor()
create_db()

if input('Already registered? (S/n) ') == 'n':
    register()
else:
    clear()
    print('Então faça o login:')
    login()

user_option()