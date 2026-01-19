from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

print(f"Testing SMTP for: {SMTP_EMAIL}")
print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")

try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("Connecting...")
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    print("Login SUCCESS!")
    
    msg = MIMEText("Test email from Quantum Login")
    msg['Subject'] = "SMTP Test"
    msg['From'] = SMTP_EMAIL
    msg['To'] = SMTP_EMAIL
    
    server.sendmail(SMTP_EMAIL, SMTP_EMAIL, msg.as_string())
    print("Email sent successfully!")
    server.quit()
except Exception as e:
    print(f"SMTP ERROR: {e}")
