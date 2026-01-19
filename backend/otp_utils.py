import secrets
import hashlib
import hmac

def generate_otp(length=6):
    """Generate a cryptographically secure numeric OTP."""
    # secrets.randbelow(10**length) generates 0 to 999999
    # zfill ensures leading zeros are kept (e.g., "012345")
    random_num = secrets.randbelow(10**length)
    return str(random_num).zfill(length)

def hash_otp(otp):
    """Hash the OTP using SHA-256 for secure storage."""
    # Using SHA-256 (fast and secure enough for short-lived OTPs)
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()

def verify_otp_hash(input_otp, stored_hash):
    """
    Verify input OTP against stored hash using constant-time comparison.
    Returns True if valid, False otherwise.
    """
    input_hash = hash_otp(input_otp)
    # constant_time_compare to prevent timing attacks
    return hmac.compare_digest(input_hash, stored_hash)
