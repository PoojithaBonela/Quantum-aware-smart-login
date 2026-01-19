from app import app, db, User

email_to_update = "dipti.singh_2027@woxsen.edu.in"
# Also update the other dipti emails just in case
emails = ["dipti.singh_2027@woxsen.edu.in", "diptisingh202006@gmail.com"]

with app.app_context():
    for email in emails:
        user = User.query.filter_by(email=email).first()
        if user:
            user.risk_level = 'high'
            db.session.commit()
            print(f"Updated {email} to HIGH risk.")
        else:
            print(f"User {email} not found.")
