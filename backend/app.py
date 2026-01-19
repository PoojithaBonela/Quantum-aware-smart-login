from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import random

# Import local modules
from models import db, User, OTPVerification
from logger import log_security_event
from otp_utils import generate_otp, hash_otp, verify_otp_hash
from email_service import send_otp_email

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///security_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
CORS(app, supports_credentials=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# ==================== AUTH HELPERS ====================

def evaluate_risk(email, ip_address):
    """
    Simulate risk evaluation.
    Returns: 'low', 'medium', or 'high'
    """
    # For demonstration, FORCE HIGH RISK to test OTP/Biometric flow
    return 'high'
    # return random.choice(['low', 'medium', 'high'])

# ==================== API ENDPOINTS ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        # Allow setting risk_level for demonstration/testing (default to 'low')
        risk_level = data.get('risk_level', 'low') 
        ip_address = request.remote_addr
        
        # Validate input
        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
        
        if risk_level not in ['low', 'medium', 'high']:
             return jsonify({'status': 'error', 'message': 'Invalid risk level. Use low, medium, or high.'}), 400
        
        # Validate email
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
        
        # Password policies
        if len(password) < 8:
            return jsonify({'status': 'error', 'message': 'Password too short'}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': 'User already exists'}), 400
        
        # Create user
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(
            email=email,
            password_hash=password_hash,
            risk_level=risk_level, # Store the specific risk level
            mfa_enabled=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        log_security_event('REGISTER_SUCCESS', email, risk_level, ip_address)
        
        return jsonify({
            'status': 'success',
            'message': f'User registered successfully with {risk_level.upper()} risk.',
            'user': {'email': email, 'risk_level': risk_level}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """
    Step 1: Validate Password & Fetch Stored Risk.
    - Low Risk: Login success (Password Only).
    - Med/High Risk: Trigger OTP.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        ip_address = request.remote_addr
        
        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Missing credentials'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Check for Lockout
            if user.lockout_until and user.lockout_until > datetime.utcnow():
                remaining = (user.lockout_until - datetime.utcnow()).seconds
                return jsonify({
                    'status': 'error', 
                    'message': f'Account locked due to too many failed attempts. Try again in {remaining} seconds.'
                }), 403

            # Verify Password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Success - Reset counters
                user.failed_login_attempts = 0
                user.lockout_until = None
                db.session.commit()
            else:
                # Failure - Increment counters
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                
                if user.failed_login_attempts >= 3:
                     user.lockout_until = datetime.utcnow() + timedelta(minutes=2)
                     log_security_event('ACCOUNT_LOCKED_PWD', email, user.risk_level, ip_address)
                     message = 'Account locked for 2 minutes.'
                else:
                     message = f'Invalid credentials. {3 - user.failed_login_attempts} attempts remaining.'
                
                db.session.commit()
                log_security_event('LOGIN_FAIL', email, user.risk_level, ip_address)
                return jsonify({'status': 'error', 'message': message}), 401
        
        # Generic error if user not found (to prevent enumeration, but for now we follow simple flow)
        if not user:
             log_security_event('LOGIN_FAIL', email or 'unknown', 'unknown', ip_address)
             return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
        # Credentials valid - Use STORED Risk Level
        current_risk = user.risk_level
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        log_security_event('LOGIN_ATTEMPT_VALID', email, current_risk, ip_address)
        
        # === LOW RISK FLOW (Password Only) ===
        if current_risk == 'low':
            login_user(user)
            log_security_event('LOGIN_SUCCESS', email, current_risk, ip_address)
            return jsonify({
                'status': 'success',
                'risk_level': 'low',
                'message': 'Login successful',
                'user': {'email': email}
            }), 200
            
        # === MEDIUM / HIGH RISK FLOW (OTP REQUIRED) ===
        # 1. Generate & Store OTP
        plain_otp = generate_otp()
        otp_hash_val = hash_otp(plain_otp)
        
        # Clear existing OTPs
        OTPVerification.query.filter_by(email=email).delete()
        
        new_otp = OTPVerification(
            email=email,
            otp_hash=otp_hash_val,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            attempts=0
        )
        db.session.add(new_otp)
        db.session.commit()
        
        # 2. Send Email
        email_sent = send_otp_email(email, plain_otp)
        
        if email_sent:
            log_security_event('OTP_SENT', email, current_risk, ip_address)
            return jsonify({
                'status': 'mfa_required',
                'risk_level': current_risk,
                'message': f'Risk: {current_risk.upper()}. OTP verification required.'
            }), 200
        else:
            log_security_event('OTP_SEND_ERROR', email, current_risk, ip_address)
            return jsonify({
                'status': 'error',
                'message': 'Failed to send OTP email. Contact support.'
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Step 2: Verify OTP.
    - If valid & Medium Risk: Login Success.
    - If valid & High Risk: Redirect to Biometric.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        otp_input = data.get('otp')
        ip_address = request.remote_addr
        
        print(f"DEBUG: verify-otp received email={email}, otp={otp_input}") # DEBUG LOG
        
        if not email or not otp_input:
            return jsonify({'status': 'error', 'message': 'Missing inputs'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Find OTP record
        otp_record = OTPVerification.query.filter_by(email=email).first()
        
        if not otp_record:
            return jsonify({'status': 'error', 'message': 'No pending OTP verification'}), 400
            
        # Check Expiry
        if datetime.utcnow() > otp_record.expires_at:
            db.session.delete(otp_record)
            db.session.commit()
            log_security_event('OTP_EXPIRED', email, user.risk_level, ip_address)
            return jsonify({'status': 'error', 'message': 'OTP expired'}), 400
            
        # Check Attempts
        if otp_record.attempts >= 3:
            db.session.delete(otp_record)
            db.session.commit()
            log_security_event('ACCOUNT_LOCKED_OTP', email, user.risk_level, ip_address)
            return jsonify({'status': 'error', 'message': 'Too many failed attempts. Login locked.'}), 403
            
        # Verify OTP Hash
        if verify_otp_hash(otp_input, otp_record.otp_hash):
            # Success!
            db.session.delete(otp_record)
            db.session.commit()
            log_security_event('OTP_SUCCESS', email, user.risk_level, ip_address)
            
            # === HIGH RISK FLOW (--> Biometric) ===
            if user.risk_level == 'high':
                log_security_event('BIOMETRIC_REDIRECT', email, user.risk_level, ip_address)
                return jsonify({
                    'status': 'biometric_required',
                    'message': 'High risk detected. Biometric verification required.'
                }), 200
            
            # === MEDIUM RISK FLOW (Final) ===
            login_user(user)
            return jsonify({
                'status': 'success',
                'risk_level': user.risk_level,
                'message': 'OTP Verified. Login successful.',
                'user': {'email': email}
            }), 200
            
        else:
            # Failed
            otp_record.attempts += 1
            db.session.commit()
            log_security_event('OTP_FAIL', email, user.risk_level, ip_address, {'attempt': otp_record.attempts})
            return jsonify({'status': 'error', 'message': 'Invalid OTP'}), 401

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/verify-biometric', methods=['POST'])
def verify_biometric():
    """
    Step 3 (High Risk Only): Simulate Biometric Check.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        ip_address = request.remote_addr
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Flow validation: Ensure user is actually High risk
        if user.risk_level != 'high':
             return jsonify({'status': 'error', 'message': 'Biometric not required for this risk level'}), 400

        # Simulate Biometric Success
        login_user(user)
        log_security_event('BIOMETRIC_SUCCESS', email, 'high', ip_address)
        
        return jsonify({
            'status': 'success',
            'risk_level': 'high',
            'message': 'Biometric verified. Login successful.',
            'user': {'email': email}
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'status': 'success', 'message': 'Logged out'})

@app.route('/api/user/security-status', methods=['GET'])
def get_security_status():
    """Get current user's security status"""
    try:
        # Using static data for now (can be made dynamic later)
        security_data = {
            'login_status': 'Authenticated',
            'security_level': 'Medium',
            'last_login_risk': 'Low',
            'mfa_enabled': 'MFA Enabled',
            'recommendation': 'Your account uses adaptive MFA based on risk evaluation.'
        }
        
        return jsonify({
            'status': 'success',
            'data': security_data
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/readiness', methods=['GET'])
def get_readiness():
    """Get quantum readiness metrics"""
    try:
        readiness_data = {
            'quantum_safe': '40%',
            'partially_safe': '35%',
            'critical': '25%'
        }
        
        return jsonify({
            'status': 'success',
            'data': readiness_data
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/logs', methods=['GET'])
def get_logs():
    # Only for demo - read the log file
    try:
        logs = []
        if os.path.exists('security_events.log'):
            with open('security_events.log', 'r') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except:
                        continue
        # Return last 50 logs
        return jsonify({'status': 'success', 'data': logs[-50:]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

import os
if __name__ == '__main__':
    app.run(debug=True, port=5000)
