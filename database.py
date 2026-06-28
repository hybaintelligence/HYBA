import sqlite3

def initialize_database():
    conn = sqlite3.connect("hyba_customer_portal.db")
    cursor = conn.cursor()

    # Create api_keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE
        )
    ''')

    # Create usage_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL,
            request_time DATETIME NOT NULL,
            request_path TEXT NOT NULL,
            request_method TEXT NOT NULL,
            response_code INTEGER NOT NULL,
            FOREIGN KEY(api_key_id) REFERENCES api_keys(id)
        )
    ''')

    conn.commit()
    conn.close()
