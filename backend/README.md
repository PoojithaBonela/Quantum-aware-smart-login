# Quantum-Aware Smart Login Security System - Backend

## API-Only Flask Backend

This is the backend API for the Quantum-Aware Smart Login Security System. It provides JSON endpoints for user authentication, risk evaluation, and admin security monitoring.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
copy .env.example .env
```
(Edit `.env` with your configuration)

5. Run the Flask API:
```bash
python app.py
```

The API will run on `http://localhost:5000`

## API Endpoints

### Authentication Endpoints

#### POST /api/register
Register a new user.
```json
Request:
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "status": "success",
  "message": "User registered successfully",
  "user": { "email": "user@example.com" }
}
```

#### POST /api/login
Login and evaluate risk.
```json
Request:
{
  "email": "user@example.com",
  "password": "password123"
}

Response (Low/Medium Risk):
{
  "status": "success",
  "risk_level": "low",
  "message": "Login successful",
  "user": { "email": "user@example.com" }
}

Response (High Risk - MFA Required):
{
  "status": "mfa_required",
  "risk_level": "high",
  "message": "MFA verification required"
}
```

#### POST /api/verify-otp
Verify OTP (hardcoded: 123456).
```json
Request:
{
  "email": "user@example.com",
  "otp": "123456"
}

Response:
{
  "status": "success",
  "message": "OTP verified successfully",
  "user": { "email": "user@example.com" }
}
```

#### POST /api/logout
Logout current user.
```json
Response:
{
  "status": "success",
  "message": "Logged out successfully"
}
```

### User Endpoints

#### GET /api/user/security-status
Get current user's security status.
```json
Response:
{
  "status": "success",
  "data": {
    "login_status": "Authenticated",
    "security_level": "Medium",
    "last_login_risk": "Low",
    "mfa_enabled": "MFA Enabled",
    "recommendation": "Your account uses adaptive MFA based on risk evaluation."
  }
}
```

### Admin Endpoints

#### GET /api/admin/readiness
Get quantum readiness metrics.
```json
Response:
{
  "status": "success",
  "data": {
    "quantum_safe": "40%",
    "partially_safe": "35%",
    "critical": "25%"
  }
}
```

#### GET /api/admin/logs
Get security logs.
```json
Response:
{
  "status": "success",
  "data": [
    {
      "email": "user1@example.com",
      "result": "Success",
      "risk": "Low",
      "mfa": "No"
    },
    ...
  ]
}
```

### Utility Endpoints

#### GET /api/health
Health check endpoint.
```json
Response:
{
  "status": "ok",
  "message": "API is running"
}
```

## Tech Stack

- **Flask 3.0.2** - Web framework
- **Flask-Login 0.6.3** - Session management
- **Flask-SQLAlchemy 3.1.1** - Database ORM
- **Flask-CORS 4.0.0** - Cross-Origin Resource Sharing
- **bcrypt 4.1.2** - Password hashing
- **email-validator 2.1.0** - Email validation
- **SQLite** - Database
- **python-dotenv 1.0.1** - Environment configuration

## Database

The application uses SQLite with a `User` model containing:
- id (Primary Key)
- email (Unique)
- password_hash
- created_at
- last_login
- risk_level
- mfa_enabled

Database file: `security.db` (auto-created on first run)

## Security Features

- **Password Hashing**: bcrypt with salt
- **Email Validation**: Validates email format before registration
- **Risk Evaluation**: Simulated risk scoring (low/medium/high)
- **Adaptive MFA**: High-risk logins trigger OTP verification
- **Session Management**: Flask-Login for user sessions

## Notes

- This is a development version with hardcoded OTP (123456)
- Risk evaluation is currently randomized for demonstration
- No JWT implementation yet
- No role-based access control
- CORS enabled for frontend integration
