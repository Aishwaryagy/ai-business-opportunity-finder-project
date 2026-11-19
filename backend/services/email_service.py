"""
Real Email Dispatch Service for AI Business Opportunity Finder.
Uses Python's built-in smtplib to send dynamic 6-digit OTP verification codes.
Supports Gmail SMTP, Outlook SMTP, and custom SMTP servers via environment variables.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple


def is_smtp_configured() -> bool:
    """Checks whether SMTP email credentials are fully specified in the environment."""
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    return bool(user and password)


def send_otp_email(recipient_email: str, otp_code: str) -> Tuple[bool, str]:
    """
    Sends a 6-digit OTP email to the user's real inbox via SMTP.
    Returns:
      (True, success_message) if email was delivered.
      (False, informational_message) if SMTP is unconfigured or encounters an error.
    """
    clean_recipient = recipient_email.strip().lower()

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME", "AI Business Opportunity Finder").strip()

    if not smtp_user or not smtp_password:
        return (
            False,
            f"SMTP credentials are not configured in backend/.env. Generated OTP '{otp_code}' for local testing."
        )

    # Compose Email Message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{otp_code} is your Business Opportunity Finder Verification Code"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = clean_recipient

    # Plain text version
    text_content = f"""
Hello,

Your verification code for AI Business Opportunity Finder is: {otp_code}

This code will expire in 10 minutes. If you did not request this login, please ignore this email.

Best regards,
AI Business Opportunity Finder Team
"""

    # Modern HTML email design
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f8fafc;
      margin: 0;
      padding: 30px;
    }}
    .email-card {{
      max-width: 520px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 36px 32px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}
    .brand-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
    }}
    .brand-badge {{
      background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
      color: #ffffff;
      padding: 8px 14px;
      border-radius: 10px;
      font-weight: 800;
      font-size: 16px;
      display: inline-block;
    }}
    .brand-title {{
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
    }}
    .otp-box {{
      background: #f1f5f9;
      border: 2px dashed #cbd5e1;
      border-radius: 12px;
      text-align: center;
      padding: 24px;
      margin: 28px 0;
    }}
    .otp-code {{
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #4f46e5;
      margin: 0;
      font-family: monospace;
    }}
    .otp-timer {{
      font-size: 13px;
      color: #64748b;
      margin-top: 8px;
    }}
    .footer-text {{
      font-size: 12px;
      color: #94a3b8;
      border-top: 1px solid #f1f5f9;
      padding-top: 18px;
      margin-top: 24px;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="brand-header">
      <span class="brand-badge">AI</span>
      <span class="brand-title">AI Business Opportunity Finder</span>
    </div>
    <h2 style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 0;">Your Verification Code</h2>
    <p style="color: #475569; font-size: 15px; line-height: 1.5;">
      Use the 6-digit code below to securely log in to your account and access market intelligence tools:
    </p>

    <div class="otp-box">
      <p class="otp-code">{otp_code}</p>
      <p class="otp-timer">⏰ Valid for 10 minutes</p>
    </div>

    <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
      If you did not request this verification code, you can safely disregard this message.
    </p>

    <div class="footer-text">
      This is an automated security email from AI Business Opportunity Finder.<br>
      Please do not reply directly to this email.
    </div>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to SMTP server with TLS
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [clean_recipient], msg.as_string())
        server.quit()

        return (True, f"A 6-digit verification code has been dispatched to {clean_recipient}.")
    except Exception as e:
        return (
            False,
            f"SMTP send failed ({str(e)}). Generated code '{otp_code}' for login."
        )
