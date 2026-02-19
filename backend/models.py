from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Security fields
    risk_level = db.Column(db.String(20), default='low')
    mfa_enabled = db.Column(db.Boolean, default=True)
    password_patterns = db.Column(db.Text, default='[]')
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    lockout_count = db.Column(db.Integer, default=0)
    biometrics_enrolled = db.Column(db.Boolean, default=False)
    
    # Relationships
    biometrics = db.relationship('UserBiometric', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class UserBiometric(db.Model):
    __tablename__ = 'user_biometrics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    face_embedding = db.Column(db.Text, nullable=False)  # JSON format (encrypted)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(255))
    result = db.Column(db.String(50))  # Success, Failed, MFA Required, Locked Out
    risk_level = db.Column(db.String(20))
    mfa_triggered = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Log {self.email} @ {self.timestamp}>'
