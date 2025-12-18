import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger("EmailService")

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD")

    def send_reset_email(self, to_email: str, reset_link: str):
        """
        Sends a password reset email using Gmail SMTP.
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ SMTP credentials not set. Skipping email send.")
            logger.info(f"MOCK EMAIL: Password reset link for {to_email}: {reset_link}")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = "Reset Your Password - Trading Bot"

            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2>Password Reset Request</h2>
                    <p>You requested to reset your password. Click the button below to proceed:</p>
                    <p>
                        <a href="{reset_link}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            Reset Password
                        </a>
                    </p>
                    <p style="font-size: 12px; color: #666;">
                        If you didn't request this, purely ignore this email. The link expires in 15 minutes.
                    </p>
                    <p style="font-size: 10px; color: #999;">Link: {reset_link}</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            # Connect to Gmail SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            logger.info(f"✅ Password reset email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False
