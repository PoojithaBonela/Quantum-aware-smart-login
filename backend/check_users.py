from app import app, db, User

with app.app_context():
    users = User.query.all()
    print(f"{'Email':<30} | {'Risk Level':<10} | {'MFA Enabled':<5}")
    print("-" * 50)
    if not users:
        print("No users found.")
    for u in users:
        print(f"{u.email:<30} | {u.risk_level:<10} | {u.mfa_enabled:<5}")
