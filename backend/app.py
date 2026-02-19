import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import random

<<<<<<< HEAD
# Import local modules
from models import db, User, OTPVerification
from logger import log_security_event
from otp_utils import generate_otp, hash_otp, verify_otp_hash
from email_service import send_otp_email
=======
from models import db, User, LoginLog, UserBiometric
>>>>>>> second-version

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///security_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False # http only for dev
app.config['BIOMETRIC_KEY'] = 'quantum-secret-123' # For basic encryption

# SMTP Configuration (will use .env values if set)
import os
from dotenv import load_dotenv
load_dotenv()

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER') or os.getenv('SMTP_SERVER') or 'smtp.gmail.com'
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT') or os.getenv('SMTP_PORT') or 587)
app.config['MAIL_USE_TLS'] = (os.getenv('MAIL_USE_TLS') or os.getenv('SMTP_USE_TLS') or 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') or os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') or os.getenv('SMTP_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

# Initialize extensions
db.init_app(app)
from flask_mail import Mail, Message
mail = Mail(app)

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173", 
    "http://localhost:5174", 
    "http://localhost:3000", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174"
])

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and ensure schema is up to date
with app.app_context():
    db.create_all()
    # Robust migration: check and add columns individually
    from sqlalchemy import text
    columns_to_add = [
        ('password_patterns', 'TEXT DEFAULT "[]"'),
        ('otp_code', 'VARCHAR(6)'),
        ('otp_expiry', 'DATETIME'),
        ('failed_attempts', 'INTEGER DEFAULT 0'),
        ('lockout_until', 'DATETIME'),
        ('lockout_count', 'INTEGER DEFAULT 0'),
        ('biometrics_enrolled', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            db.session.execute(text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'))
            db.session.commit()
            print(f"Added column {col_name} to users table.")
        except Exception:
            db.session.rollback() # Likely column already exists

# ==================== HELPERS ====================

def get_device_info():
    """Parse User-Agent into a readable device description"""
    ua = request.user_agent
    if not ua or not ua.string:
        return "Unknown Device"
    
    browser = ua.browser or "Unknown Browser"
    platform = ua.platform or "Unknown OS"
    
    # Capitalize for readability
    browser = browser.capitalize()
    platform = platform.capitalize()
    
    return f"{browser} on {platform}"

def add_audit_log(email, result, risk_level, mfa_triggered=False, failure_reason=None):
    """Centralized logging for all login-related activities"""
    try:
        new_log = LoginLog(
            email=email,
            timestamp=datetime.now(),  # Local server time
            ip_address=request.remote_addr,
            device_info=get_device_info(),
            result=result,
            risk_level=risk_level,
            mfa_triggered=mfa_triggered,
            failure_reason=failure_reason
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print(f"Logging error: {e}")
        db.session.rollback()

def handle_failed_attempt(user, threshold=3):
    """Increment failure counter and trigger lockout if necessary"""
    user.failed_attempts += 1
    
    if user.failed_attempts >= threshold:
        user.lockout_count += 1
        # 1st lockout = 2 mins, subsequent = 5 mins
        duration = 2 if user.lockout_count == 1 else 5
        user.lockout_until = datetime.utcnow() + timedelta(minutes=duration)
        db.session.commit()
        return True, duration
        
    db.session.commit()
    return False, 0

def is_user_locked(user):
    """Check if user is currently locked out"""
    if user.lockout_until and user.lockout_until > datetime.utcnow():
        remaining = (user.lockout_until - datetime.utcnow()).total_seconds()
        return True, int(remaining / 60) + 1
    return False, 0

def reset_attempts(user):
    """Reset all lockout-related counters on successful login/OTP"""
    user.failed_attempts = 0
    user.lockout_until = None
    user.lockout_count = 0
    db.session.commit()

def cleanup_old_logs():
    """Delete logs older than 30 days"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        num_deleted = LoginLog.query.filter(LoginLog.timestamp < cutoff).delete()
        if num_deleted > 0:
            db.session.commit()
            print(f"Cleaned up {num_deleted} old logs.")
    except Exception as e:
        print(f"Cleanup error: {e}")
        db.session.rollback()

def send_otp_email(email, risk_level):
    """Generate and send OTP to user"""
    otp = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(minutes=5)
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.otp_code = otp
        user.otp_expiry = expiry
        db.session.commit()
        
    try:
        msg = Message(
            "Your Secure Login OTP",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        msg.body = f"Hello,\n\nA login attempt for your account ({email}) was detected as {risk_level} risk.\n\nYour 6-digit verification code is: {otp}\n\nThis code will expire in 5 minutes.\n\nIf you did not attempt to log in, please secure your account immediately."
        mail.send(msg)
        print(f"OTP sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# ==================== BIOMETRIC HELPERS ====================
import base64

def basic_encrypt(data, key):
    """Simple XOR-based 'basic' encryption for embeddings"""
    encoded = base64.b64encode(data.encode()).decode()
    result = []
    for i in range(len(encoded)):
        key_c = key[i % len(key)]
        enc_c = chr(ord(encoded[i]) ^ ord(key_c))
        result.append(enc_c)
    return base64.b64encode("".join(result).encode()).decode()

def basic_decrypt(encoded_data, key):
    """Simple XOR-based 'basic' decryption for embeddings"""
    try:
        decoded_enc = base64.b64decode(encoded_data.encode()).decode()
        result = []
        for i in range(len(decoded_enc)):
            key_c = key[i % len(key)]
            dec_c = chr(ord(decoded_enc[i]) ^ ord(key_c))
            result.append(dec_c)
        return base64.b64decode("".join(result).encode()).decode()
    except Exception:
        return "{}"

def compare_embeddings(saved_embeddings_json, live_embedding, threshold=0.6):
    """
    Compare live embedding with 3 saved embeddings using Euclidean distance.
    Returns True if any match is within threshold.
    """
    import math
    try:
        saved_list = json.loads(saved_embeddings_json)
        for saved in saved_list:
            # Euclidean distance
            dist = math.sqrt(sum((s - l) ** 2 for s, l in zip(saved, live_embedding)))
            if dist < threshold:
                return True, dist
        return False, 999
    except Exception as e:
        print(f"Comparison error: {e}")
        return False, 999

# ==================== HELPERS ====================

import re
import math

def analyze_password_patterns(password, email=''):
    """Accurate Python port of evaluateSecurityMetrics from passwordAnalysis.js"""
    lower_pass = password.lower()
    email_prefix = email.split('@')[0].lower() if email else ''
    
    # leetspeak substitutions
    substitutions = {
        '@': 'a', '0': 'o', '1': 'l', '3': 'e', '4': 'a',
        '5': 's', '$': 's', '7': 't', '!': 'i'
    }
    normalized_pass = lower_pass
    for leet, plain in substitutions.items():
        normalized_pass = normalized_pass.replace(leet, plain)

    patterns = []
    
    # 1. Dictionary words
    common_words = [
        'password', 'pass', 'admin', 'welcome', 'login', 'security',
        'qwerty', 'letmein', 'iloveyou', 'monkey', 'dragon',
        'football', 'baseball', 'master', 'shadow', 'sunshine',
        'princess', 'trustno1'
    ]
    if any(word in lower_pass for word in common_words) or any(word in normalized_pass for word in common_words):
        patterns.append('dictionary_word')

    # 2. Aggressive Name/Email Reuse (Sliding Window of 4 chars)
    name_reuse = False
    if email_prefix:
        if len(email_prefix) >= 4:
            if email_prefix in lower_pass:
                name_reuse = True
            else:
                # Sliding window of 4 chars
                for i in range(len(email_prefix) - 3):
                    chunk = email_prefix[i:i+4]
                    if chunk in lower_pass:
                        name_reuse = True
                        break
        # Check parts split by . _ -
        if not name_reuse:
            for part in re.split(r'[._-]', email_prefix):
                if len(part) >= 4 and part in lower_pass:
                    name_reuse = True
                    break
    if name_reuse:
        patterns.append('name_reuse')

    # 3. Numeric suffixes (2-4 digits at end)
    if re.search(r'\d{2,4}$', password):
        patterns.append('numeric_suffix')

    # 4. Sequential patterns (3+ chars) - Match JS exactly
    def check_sequential(s):
        if len(s) < 3: return False
        for i in range(len(s) - 2):
            c1, c2, c3 = ord(s[i]), ord(s[i+1]), ord(s[i+2])
            if (c2 == c1 + 1 and c3 == c2 + 1) or (c2 == c1 - 1 and c3 == c2 - 1):
                return True
        return False
    if check_sequential(lower_pass):
        patterns.append('sequential_pattern')

    # 5. Keyboard patterns (4+ consecutive adjacent) - Match JS exactly
    KEYBOARD_ROWS = [
        '1234567890',
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm'
    ]
    def has_invalid_keyboard_pattern(s):
        if len(s) < 4: return False
        ls = s.lower()
        consecutive_count = 1
        for i in range(1, len(ls)):
            prev_char, curr_char = ls[i-1], ls[i]
            is_adjacent = False
            for row in KEYBOARD_ROWS:
                prev_idx = row.find(prev_char)
                curr_idx = row.find(curr_char)
                if prev_idx != -1 and curr_idx != -1:
                    if abs(curr_idx - prev_idx) == 1:
                        is_adjacent = True
                    break
            if is_adjacent:
                consecutive_count += 1
                if consecutive_count > 3: return True
            else:
                consecutive_count = 1
        return False
    
    if has_invalid_keyboard_pattern(password):
        patterns.append('keyboard_pattern')

    # 6. Character Repetition (>2 repeats)
    if re.search(r'(.)\1\1', password):
        patterns.append('repeated_pattern')
        
    # 7. Year (19xx, 20xx)
    if re.search(r'(19\d{2}|20\d{2})', password):
        patterns.append('year_pattern')
        
    # 8. Date patterns
    if re.search(r'(\d{2}[\/\-.]\d{2}[\/\-.]\d{2,4})|(\d{4}[\/\-.]\d{2}[\/\-.]\d{2})|(\d{8})', password):
        patterns.append('date_pattern')

    # JS-consistent Character Classes
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'[0-9]', password))
    has_symbol = bool(re.search(r'[^A-Za-z0-9]', password))

    charset_size = 0
    if has_lower: charset_size += 26
    if has_upper: charset_size += 26
    if has_digit: charset_size += 10
    if has_symbol: charset_size += 32
    if charset_size == 0: charset_size = 1

    penalty = 1.0
    if 'dictionary_word' in patterns: penalty *= 10**6
    if 'numeric_suffix' in patterns: penalty *= 10**3
    if 'year_pattern' in patterns: penalty *= 10**3
    if 'date_pattern' in patterns: penalty *= 10**4
    if 'name_reuse' in patterns: penalty *= 10**5
    if 'keyboard_pattern' in patterns: penalty *= 10**4
    if 'sequential_pattern' in patterns: penalty *= 10**3
    if 'repeated_pattern' in patterns: penalty *= 10**3

    raw_space = charset_size ** len(password)
    effective_space = raw_space / penalty
    
    hash_cost = 0.1
    classical_seconds = effective_space * hash_cost
    quantum_seconds = math.sqrt(max(effective_space, 1)) * hash_cost

    classical_score = 3 if classical_seconds < 3600 else (2 if classical_seconds < 30*24*3600 else 1)
    quantum_score = 3 if quantum_seconds < 24*3600 else (2 if quantum_seconds < 365*24*3600 else 1)
    
    final_score = max(classical_score, quantum_score)
    risk_label = 'high' if final_score == 3 else ('medium' if final_score == 2 else 'low')
    
    print(f"DEBUG_RISK: pass_len={len(password)} charset={charset_size} penalty={penalty:.1e} space={effective_space:.1e} c_sec={classical_seconds:.1e} q_sec={quantum_seconds:.1e} final={risk_label}")
    
    return patterns, risk_label

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
<<<<<<< HEAD
        # Allow setting risk_level for demonstration/testing (default to 'low')
        risk_level = data.get('risk_level', 'low') 
        ip_address = request.remote_addr
=======
        biometric_data = data.get('biometricData')
>>>>>>> second-version
        
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
<<<<<<< HEAD
        new_user = User(
            email=email,
            password_hash=password_hash,
            risk_level=risk_level, # Store the specific risk level
            mfa_enabled=True
=======
        
        # Create new user
        patterns, risk_level = analyze_password_patterns(password, email)
        print(f"REGISTER: Calculated risk for {email}: {risk_level}")
        new_user = User(
            email=email,
            password_hash=password_hash,
            mfa_enabled=True,  # MFA enabled by default
            risk_level=risk_level,
            password_patterns=json.dumps(patterns)
>>>>>>> second-version
        )
        
        db.session.add(new_user)
        db.session.commit()
        
<<<<<<< HEAD
        log_security_event('REGISTER_SUCCESS', email, risk_level, ip_address)
=======
        # Biometric enrollment if provided
        # Biometric enrollment if provided
        if biometric_data and len(biometric_data) == 3:
            encrypted = basic_encrypt(json.dumps(biometric_data), app.config['BIOMETRIC_KEY'])
            new_biometric = UserBiometric(user_id=new_user.id, face_embedding=encrypted)
            new_user.biometrics_enrolled = True
            db.session.add(new_biometric)
            db.session.commit()
            print(f"REGISTER: Biometrics stored for {email}")
>>>>>>> second-version
        
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
<<<<<<< HEAD
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
=======
            # Note: We don't have a user object, but we log the attempt by email
            add_audit_log(email, 'Failed', 'N/A', failure_reason='User not found')
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        # Check for lockout
        is_locked, minutes = is_user_locked(user)
        if is_locked:
            add_audit_log(email, 'Locked Out', user.risk_level.capitalize(), failure_reason=f'Account locked for {minutes}m')
            return jsonify({
                'status': 'error', 
                'message': f'Account temporarily blocked. Please try again in {minutes} minutes.'
            }), 403
            
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            locked, duration = handle_failed_attempt(user)
            attempts_left = 3 - user.failed_attempts
            msg = 'Invalid credentials'
            
            if locked:
                res = 'Locked Out'
                reason = f'3 failed login attempts. Blocked for {duration}m'
                msg = f'Account blocked for {duration} minutes due to multiple failed attempts.'
                status_code = 403
            else:
                res = 'Failed'
                reason = 'Invalid password'
                status_code = 401
                
            add_audit_log(email, res, 'N/A', failure_reason=f"{reason}. {attempts_left} left")
            
            if locked:
                return jsonify({'status': 'error', 'message': msg}), 403
            
            return jsonify({
                'status': 'error', 
                'message': f'Invalid credentials. {attempts_left} attempts remaining.',
                'attempts_left': attempts_left
            }), 401
        
        # Update user's risk level and patterns based on password
        patterns, risk_level = analyze_password_patterns(password, email)
        print(f"LOGIN: Calculated risk for {email}: {risk_level} (patterns: {patterns})")
        user.risk_level = risk_level
        user.password_patterns = json.dumps(patterns)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Decide if MFA is required (high and medium risk trigger MFA)
        if risk_level == 'high' and user.biometrics_enrolled:
             add_audit_log(email, 'Biometric Required', 'High', mfa_triggered=True)
             return jsonify({
                 'status': 'biometric_required',
                 'risk_level': risk_level,
                 'message': 'Face verification required for high-risk account.'
             }), 200

        if risk_level in ['high', 'medium']:
            # Log the MFA requirement
            add_audit_log(email, 'MFA Required', risk_level.capitalize(), mfa_triggered=True)
            
            # Reset failed_attempts to give fresh budget for OTP
            user.failed_attempts = 0
            db.session.commit()
            
            send_otp_email(email, risk_level)
            
            return jsonify({
                'status': 'mfa_required',
                'risk_level': risk_level,
                'message': f'MFA verification required for {risk_level} risk. OTP sent to your email.'
            }), 200
        else:
            # Only login directly for low risk
            login_user(user)
            reset_attempts(user)
            add_audit_log(email, 'Success', 'Low', mfa_triggered=False)
>>>>>>> second-version
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
            
<<<<<<< HEAD
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
=======
        # Check for lockout
        is_locked, minutes = is_user_locked(user)
        if is_locked:
            add_audit_log(email, 'Locked Out', user.risk_level.capitalize(), failure_reason=f'Account locked for {minutes}m')
            return jsonify({
                'status': 'error', 
                'message': f'Account blocked. Try again in {minutes} minutes.'
            }), 403
            
        # Real OTP verification
        if user.otp_code and user.otp_expiry > datetime.utcnow():
            if otp == user.otp_code:
                login_user(user)
                # Clear OTP and Reset lockout counters
                risk = user.risk_level.capitalize()
                user.otp_code = None
                user.otp_expiry = None
                reset_attempts(user)
                
                add_audit_log(email, 'Success', risk, mfa_triggered=True)
                
                return jsonify({
                    'status': 'success',
                    'message': 'OTP verified successfully',
                    'user': {'email': user.email}
                }), 200
            else:
                locked, duration = handle_failed_attempt(user, threshold=2)
                attempts_left = 2 - user.failed_attempts
                risk = user.risk_level.capitalize()
                
                if locked:
                    # Clear the OTP code so they must log in again after lockout
                    user.otp_code = None
                    user.otp_expiry = None
                    db.session.commit()
                    reason = f'2 failed OTP attempts. Blocked for {duration}m'
                    add_audit_log(email, 'Locked Out', risk, mfa_triggered=True, failure_reason=reason)
                    return jsonify({'status': 'error', 'message': f'Account blocked for {duration} minutes due to failed OTP attempts.'}), 403
                
                reason = f'Invalid OTP. {attempts_left} left'
                add_audit_log(email, 'Failed', risk, mfa_triggered=True, failure_reason=reason)
                
                return jsonify({
                    'status': 'error', 
                    'message': f'Invalid OTP code. {attempts_left} attempts remaining.',
                    'attempts_left': attempts_left
                }), 401
        else:
            return jsonify({'status': 'error', 'message': 'OTP expired or not requested'}), 401
>>>>>>> second-version
            
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
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Not authenticated'
            }), 401

        # Parse stored patterns
        try:
            patterns = json.loads(current_user.password_patterns or '[]')
        except:
            patterns = []

        # Map internal pattern names to human-readable warnings
        pattern_map = {
            'dictionary_word': 'Contains common dictionary words',
            'name_reuse': 'Reuse of email/name detected',
            'numeric_suffix': 'Uses simple numeric suffix',
            'keyboard_pattern': 'Simple keyboard sequence detected',
            'repeated_pattern': 'Contains repeated character sequences'
        }
        
        warnings = [pattern_map.get(p, p) for p in patterns]
        pattern_text = ". ".join(warnings) if warnings else "No weak patterns detected"

        # Logic for recommendations as per user requirements:
        # High Risk: Switch to biometrics + Hardware key
        # Medium Risk: Based on patterns + switch to biometric
        # Low Risk/Security: Switch to OTP + improve based on patterns
        
        risk = current_user.risk_level.lower()
        print(f"FETCH: User {current_user.email} has risk level: {risk}")
        
        if risk == 'high':
            recommendation = f"CRITICAL: Unusual login activity detected. {pattern_text}. HIGHLY RECOMMENDED: Switch to biometric authentication and consider a hardware security key immediately."
        elif risk == 'medium':
            recommendation = f"Security Recommendation: {pattern_text}. Suggestion: Strengthen your password by avoiding common patterns and switch to biometric authentication if necessary."
        else: # Low Risk
            recommendation = f"Security Status: Healthy. Detected Patterns: {pattern_text}. To further improve security, switch to OTP verification and avoid simple password patterns."

        security_data = {
            'email': current_user.email,
            'login_status': 'Authenticated',
            'security_level': current_user.risk_level.capitalize(),
            'risk_level': current_user.risk_level.capitalize(),
            'last_login_risk': current_user.risk_level.capitalize(),
            'mfa_enabled': current_user.mfa_enabled,
            'recommendation': recommendation
        }
        
        return jsonify({
            'status': 'success',
            'data': security_data
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/readiness', methods=['GET'])
def get_readiness():
    """Get real quantum readiness metrics based on DB user profiles"""
    try:
        total_users = User.query.count()
        if total_users == 0:
            return jsonify({'status': 'success', 'data': {'quantum_safe': '0%', 'partially_safe': '0%', 'critical': '0%'}}), 200
            
        low_risk = User.query.filter_by(risk_level='low').count()
        med_risk = User.query.filter_by(risk_level='medium').count()
        high_risk = User.query.filter_by(risk_level='high').count()
        
        readiness_data = {
            'total_users': total_users,
            'quantum_safe': f"{int((low_risk/total_users)*100)}%",
            'partially_safe': f"{int((med_risk/total_users)*100)}%",
            'critical': f"{int((high_risk/total_users)*100)}%"
        }
        
        return jsonify({
            'status': 'success',
            'data': readiness_data
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/logs', methods=['GET'])
def get_logs():
<<<<<<< HEAD
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

=======
    """Get real-time security logs from DB"""
    try:
        cleanup_old_logs()  # Run cleanup periodically
        # Fetch all logs, newest first
        db_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(100).all()
        
        logs = []
        for log in db_logs:
            logs.append({
                'id': log.id,
                'email': log.email,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'ip': log.ip_address,
                'device': log.device_info,
                'result': log.result,
                'risk': log.risk_level,
                'mfa': 'Yes' if log.mfa_triggered else 'No',
                'reason': log.failure_reason
            })
        
        return jsonify({
            'status': 'success',
            'data': logs
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/logs/download', methods=['GET'])
def download_logs():
    """Generate and return a PDF security audit report"""
    try:
        from io import BytesIO
        from flask import send_file
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        db_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(1000).all()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Security Audit Report", styles['Title']))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Table data
        data = [['Timestamp', 'Email', 'IP Address', 'Result', 'Risk', 'MFA', 'Details']]
        for log in db_logs:
            data.append([
                log.timestamp.strftime('%Y-%m-%d %H:%M'),
                log.email,
                log.ip_address,
                log.result,
                log.risk_level,
                'Yes' if log.mfa_triggered else 'No',
                log.failure_reason if log.failure_reason else '-'
            ])
            
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'security_report_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"PDF error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/debug/session', methods=['GET'])
def debug_session():
    """Debug session and authentication status"""
    return jsonify({
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.get_id() if current_user.is_authenticated else None,
        'cookies': dict(request.cookies)
    }), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout current user"""
    try:
        logout_user()
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== BIOMETRIC ENDPOINTS ====================

@app.route('/api/biometric/enroll', methods=['POST'])
def enroll_biometric():
    """Enroll face embeddings for a high-risk user"""
    try:
        data = request.get_json()
        email = data.get('email')
        embeddings = data.get('embeddings') # List of 3 embeddings
        
        if not email or not embeddings or len(embeddings) != 3:
            return jsonify({'status': 'error', 'message': 'Invalid enrollment data'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Encrypt embeddings JSON
        encrypted_embeddings = basic_encrypt(json.dumps(embeddings), app.config['BIOMETRIC_KEY'])
        
        # Store in table
        new_biometric = UserBiometric(
            user_id=user.id,
            face_embedding=encrypted_embeddings
        )
        user.biometrics_enrolled = True
        
        db.session.add(new_biometric)
        db.session.commit()
        
        add_audit_log(email, 'Biometric Enrolled', user.risk_level.capitalize())
        
        return jsonify({
            'status': 'success',
            'message': 'Biometric data enrolled successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/biometric/verify', methods=['POST'])
def verify_biometric():
    """Verify live face embedding against stored data"""
    try:
        data = request.get_json()
        email = data.get('email')
        live_embedding = data.get('embedding')
        
        if not email or not live_embedding:
            return jsonify({'status': 'error', 'message': 'Missing verification data'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.biometrics_enrolled:
            return jsonify({'status': 'error', 'message': 'Biometrics not available'}), 404
            
        # Get latest biometric data
        biometric_record = UserBiometric.query.filter_by(user_id=user.id).order_by(UserBiometric.created_at.desc()).first()
        if not biometric_record:
            return jsonify({'status': 'error', 'message': 'No biometric record found'}), 404
            
        # Decrypt and compare
        saved_json = basic_decrypt(biometric_record.face_embedding, app.config['BIOMETRIC_KEY'])
        match, distance = compare_embeddings(saved_json, live_embedding)
        
        if match:
            # If high risk, we still require OTP after biometric
            if user.risk_level.lower() == 'high':
                send_otp_email(email, 'High')
                return jsonify({
                    'status': 'mfa_required',
                    'message': 'Biometric verified. Please enter the OTP sent to your email.',
                    'user': {'email': user.email}
                }), 200
            
            # Otherwise (if we ever use biometrics for medium), login directly
            login_user(user)
            reset_attempts(user)
            add_audit_log(email, 'Success (Biometric)', user.risk_level.capitalize(), mfa_triggered=True)
            return jsonify({
                'status': 'success',
                'message': 'Biometric verification successful',
                'user': {'email': user.email}
            }), 200
        else:
            add_audit_log(email, 'Failed (Biometric)', user.risk_level.capitalize(), mfa_triggered=True, failure_reason=f"Face mismatch (dist: {distance:.3f})")
            return jsonify({
                'status': 'error',
                'message': 'Face verification failed'
            }), 401
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Health check endpoint
>>>>>>> second-version
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

import os
if __name__ == '__main__':
    app.run(debug=True, port=5000)
