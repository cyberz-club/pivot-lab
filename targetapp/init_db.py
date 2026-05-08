#!/usr/bin/env python3
import os
import sqlite3

DB_PATH = '/opt/targetapp/target.db'


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        )
    ''')
    cur.execute('DELETE FROM users')
    cur.execute('DELETE FROM flags')
    cur.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                ('admin', 'supersecret'))
    cur.execute('INSERT INTO flags (value) VALUES (?)',
                ('CyberZ{reached_the_target}',))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
