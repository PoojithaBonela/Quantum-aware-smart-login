from app import app, db, User
import json

with app.app_context():
    users = User.query.all()
    results = []
    for u in users:
        results.append({
            "email": u.email,
            "failed_attempts": getattr(u, 'failed_attempts', 'MISSING'),
            "lockout_until": str(u.lockout_until) if getattr(u, 'lockout_until', None) else None,
            "lockout_count": getattr(u, 'lockout_count', 'MISSING')
        })
    print(json.dumps(results, indent=2))
