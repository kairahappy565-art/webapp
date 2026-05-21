from app import app
from config import Config
from models import db, User, Student, Teacher, Attendance, Grade, Fee, CalendarEvent


def column_exists(engine, table_name, column_name):
    with engine.connect() as connection:
        result = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in result)


def main():
    with app.app_context():
        db.create_all()

        default_user = User.query.first()
        if not default_user:
            default_user = User(username=Config.DEFAULT_ADMIN_USERNAME)
            default_user.set_password(Config.DEFAULT_ADMIN_PASSWORD)
            db.session.add(default_user)
            db.session.commit()
            print(f"Created default user: {default_user.username}")

        owner_id = default_user.id
        engine = db.engine

        tables = [
            ('students', Student),
            ('teachers', Teacher),
            ('attendance', Attendance),
            ('grades', Grade),
            ('fees', Fee),
            ('calendar_events', CalendarEvent),
        ]

        for table_name, model in tables:
            if not column_exists(engine, table_name, 'user_id'):
                print(f"Adding user_id column to {table_name}...")
                with engine.connect() as connection:
                    connection.exec_driver_sql(f'ALTER TABLE {table_name} ADD COLUMN user_id INTEGER')
                db.session.commit()
                with engine.connect() as connection:
                    connection.exec_driver_sql(f'UPDATE {table_name} SET user_id = :uid', {'uid': owner_id})
                db.session.commit()
                print(f"Updated existing rows in {table_name} to user_id={owner_id}.")
            else:
                print(f"{table_name} already has user_id column.")

        print("Migration complete. Existing records are now associated with user_id", owner_id)


if __name__ == '__main__':
    main()
