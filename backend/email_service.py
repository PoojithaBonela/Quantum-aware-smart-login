import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

def send_otp_email(to_email, otp):
    """
    Send OTP email using Gmail SMTP.
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[ERROR] SMTP credentials missing in .env")
        return False
        
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Login Verification Code - Quantum Secure"
        
        body = f"""
        <html>
          <body>
            <h2>Login Verification</h2>
            <p>Your verification code is:</p>
            <h1>{otp}</h1>
            <p>This code expires in 5 minutes.</p>
            <p>If you did not request this login, please ignore this email.</p>
            <br>
            <small>Quantum-Aware Smart Login System</small>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        print(f"Connecting to SMTP: {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        
        # Login
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, to_email, text)
        
        server.quit()
        print(f"OTP sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
        # IMPORTANT: In production, do not expose exact error to user, 
        # but log it for debugging.
        return False
