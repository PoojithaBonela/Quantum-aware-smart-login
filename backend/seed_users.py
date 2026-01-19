from app import app, db, User
import bcrypt

def create_user(email, password, risk_level):
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        email=email,
        password_hash=password_hash,
        risk_level=risk_level,
        mfa_enabled=True
    )
    db.session.add(user)
    print(f"Created {risk_level.upper()} risk user: {email}")

with app.app_context():
    # FORCE RESET: Drop all tables and recreate
    db.drop_all()
    db.create_all()
    print("Tables dropped and recreated.")
    
    # 1. The user's specific account -> LOW RISK (Password Only)
    create_user("poojitha.bonela_2027@woxsen.edu.in", "Password123!", "low")
    
    # 2. A test High Risk account -> HIGH RISK (MFA + Bio)
    create_user("dipti.singh_2027@woxsen.edu.in", "Password123!", "high")
    
    # 3. Explicit Test Accounts
    create_user("low@test.com", "Password123!", "low")
    create_user("high@test.com", "Password123!", "high")
    
    db.session.commit()
    print("Database seeded successfully!")
