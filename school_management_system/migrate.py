import os
import sqlite3

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'instance', 'school_management.db')

TABLES = [
    'students',
    'teachers',
    'grades',
    'fees',
    'attendance',
    'calendar_events',
]

COLUMN_NAME = 'user_id'
COLUMN_DEFINITION = 'INTEGER DEFAULT 1'


def has_column(connection, table_name, column_name):
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column(connection, table_name, column_definition):
    connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {COLUMN_NAME} {column_definition}")
    connection.commit()


def main():
    if not os.path.exists(DB_PATH):
        print(f"Warning: database file not found at {DB_PATH}. A new file will be created.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA foreign_keys = ON')

        for table in TABLES:
            try:
                if has_column(conn, table, COLUMN_NAME):
                    print(f"Warning: '{COLUMN_NAME}' already exists in '{table}', skipping.")
                    continue

                add_column(conn, table, COLUMN_DEFINITION)
                conn.execute(f"UPDATE {table} SET {COLUMN_NAME} = 1 WHERE {COLUMN_NAME} IS NULL")
                conn.commit()
                print(f"Success: added '{COLUMN_NAME}' to '{table}' and set existing rows to 1.")
            except sqlite3.OperationalError as e:
                print(f"Error updating '{table}': {e}")
            except Exception as e:
                print(f"Unexpected error updating '{table}': {e}")

        print('\nMigration complete.')


if __name__ == '__main__':
    main()
