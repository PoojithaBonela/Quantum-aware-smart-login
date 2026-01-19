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
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<OTP {self.email}>'
