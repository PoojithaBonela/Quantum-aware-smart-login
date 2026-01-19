from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
            print("Added failed_login_attempts column")
        except Exception as e:
            print(f"failed_login_attempts column might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN lockout_until DATETIME"))
            print("Added lockout_until column")
        except Exception as e:
            print(f"lockout_until column might already exist: {e}")
            
    print("Migration complete.")
