from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import random

from models import db, User

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///security.db'
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

# ==================== API ENDPOINTS ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
        
        # Validate email format
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters long'}), 400
        if not any(c.isupper() for c in password):
            return jsonify({'status': 'error', 'message': 'Password must contain at least one uppercase letter'}), 400
        if not any(c.islower() for c in password):
            return jsonify({'status': 'error', 'message': 'Password must contain at least one lowercase letter'}), 400
        if not any(c.isdigit() for c in password):
            return jsonify({'status': 'error', 'message': 'Password must contain at least one number'}), 400
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            return jsonify({'status': 'error', 'message': 'Password must contain at least one special character'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': 'User already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = User(
            email=email,
            password_hash=password_hash,
            mfa_enabled=True,  # MFA enabled by default
            risk_level='low'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user': {'email': email}
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Login user and evaluate risk"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        # Simulate risk evaluation (random for demo)
        risk_levels = ['low', 'medium', 'high']
        risk_level = random.choice(risk_levels)
        
        # Update user's risk level
        user.risk_level = risk_level
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Login user
        login_user(user)
        
        # Decide if MFA is required (high risk triggers MFA)
        if risk_level == 'high':
            return jsonify({
                'status': 'mfa_required',
                'risk_level': risk_level,
                'message': 'MFA verification required'
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'risk_level': risk_level,
                'message': 'Login successful',
                'user': {'email': user.email}
            }), 200
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP (simulated)"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'status': 'error', 'message': 'Email and OTP are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Simulated OTP verification (hardcoded OTP: 123456)
        if otp == '123456':
            login_user(user)
            return jsonify({
                'status': 'success',
                'message': 'OTP verified successfully',
                'user': {'email': user.email}
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid OTP'
            }), 401
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
    """Get security logs"""
    try:
        # Static log data
        logs = [
            {'email': 'user1@example.com', 'result': 'Success', 'risk': 'Low', 'mfa': 'No'},
            {'email': 'user2@example.com', 'result': 'Success', 'risk': 'Medium', 'mfa': 'Yes'},
            {'email': 'admin@example.com', 'result': 'Success', 'risk': 'Low', 'mfa': 'No'},
            {'email': 'user3@example.com', 'result': 'Failed', 'risk': 'High', 'mfa': 'Yes'},
            {'email': 'user4@example.com', 'result': 'Success', 'risk': 'Medium', 'mfa': 'Yes'},
            {'email': 'user5@example.com', 'result': 'Failed', 'risk': 'High', 'mfa': 'Yes'}
        ]
        
        return jsonify({
            'status': 'success',
            'data': logs
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'message': 'API is running'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
