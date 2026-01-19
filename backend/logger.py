import logging
import json
from datetime import datetime
import os

# Configure logging
LOG_FILE = 'security_events.log'

# Ensure file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        pass

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(message)s'
)

def log_security_event(event_type, email, risk_level, ip_address, details=None):
    """
    Log a security event in structured JSON format.
    
    Args:
        event_type (str): Type of event (e.g., LOGIN_ATTEMPT, OTP_SENT, OTP_FAIL)
        email (str): User's email
        risk_level (str): Current risk level (LOW, MEDIUM, HIGH)
        ip_address (str): User's IP address
        details (dict, optional): Additional context
    """
    entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'email': email,
        'risk_level': risk_level,
        'ip_address': ip_address,
        'details': details or {}
    }
    
    # Log to file
    logging.info(json.dumps(entry))
    
    # Also print to console for dev visibility
    print(f"[SECURITY LOG] {json.dumps(entry)}")
