from app import app, db
from sqlalchemy import text

def fix_password_hash_length():
    with app.app_context():
        try:
            # PostgreSQL specific command to alter column type
            sql = text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(256);')
            with db.engine.connect() as connection:
                connection.execute(sql)
                connection.commit()
            print("SUCCESS: Password Hash column resized to 256.")
        except Exception as e:
            print(f"Schema Fix Failed: {e}")

if __name__ == "__main__":
    fix_password_hash_length()
