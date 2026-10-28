import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import re

from app.core.config import settings
from app.core.logging import logger

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class EmailDeliveryService:
    def __init__(self):
        self.enabled = settings.SMTP_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.use_tls = settings.SMTP_USE_TLS

    def is_service_available(self) -> bool:
        return bool(self.enabled and self.host and self.host != "smtp.example.com")

    def validate_recipient(self, email: Optional[str]) -> bool:
        if not email or not isinstance(email, str):
            return False
        clean = email.strip()
        return bool(EMAIL_REGEX.match(clean))

    def send_solution_email(
        self,
        recipient_email: Optional[str],
        passenger_name: str,
        ticket_number: str,
        ticket_title: str,
        solution_text: str
    ) -> Dict[str, Any]:
        """
        Sends an automated AI solution to the passenger/customer.
        Accurately records whether email was delivered, service unavailable, or recipient invalid.
        """
        clean_recipient = recipient_email.strip() if recipient_email else ""

        # 1. Validate recipient details
        if not self.validate_recipient(clean_recipient):
            return {
                "success": False,
                "status": "INVALID_RECIPIENT",
                "message": f"Passenger email address '{clean_recipient or 'None'}' is invalid or missing.",
                "recipient": clean_recipient or None,
                "sent_at": None
            }

        # 2. Check if SMTP service is configured
        if not self.is_service_available():
            logger.info(f"Email service not configured for dispatch to {clean_recipient}. Mock/unconfigured state.")
            return {
                "success": False,
                "status": "SERVICE_NOT_CONFIGURED",
                "message": "Email delivery service is currently not configured or disabled (SMTP credentials not provided).",
                "recipient": clean_recipient,
                "sent_at": None
            }

        # 3. Attempt real SMTP dispatch
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"AeroAssist AI Resolution: [{ticket_number}] {ticket_title}"
            msg["From"] = self.from_email
            msg["To"] = clean_recipient

            plain_body = (
                f"Dear {passenger_name or 'Passenger'},\n\n"
                f"Thank you for contacting AeroAssist Flight Support.\n"
                f"Regarding your ticket {ticket_number} ({ticket_title}), our automated resolution system has prepared the following solution:\n\n"
                f"{solution_text}\n\n"
                f"Safe travels,\nAeroAssist Airline Operations Team"
            )

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #0284c7; margin-bottom: 8px;">AeroAssist AI Resolution</h2>
                <p style="color: #64748b; font-size: 14px; margin-top: 0;">Ticket {ticket_number} &bull; {ticket_title}</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;" />
                <p>Dear <strong>{passenger_name or 'Passenger'}</strong>,</p>
                <p>Thank you for reaching out. Here is the verified solution for your inquiry:</p>
                <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 14px; margin: 16px 0; border-radius: 4px; white-space: pre-wrap; font-size: 14px; line-height: 1.5;">
{solution_text}
                </div>
                <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
                    This solution was generated and verified using our AeroAssist AI flight operations knowledge base.
                </p>
                <p style="font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 12px;">
                    AeroAssist Airline Operations &bull; Commercial Dispatch Support
                </p>
            </div>
            """

            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)

            sent_timestamp = datetime.now(timezone.utc).isoformat()
            logger.info(f"Successfully sent resolution email to {clean_recipient} for ticket {ticket_number}")
            return {
                "success": True,
                "status": "DELIVERED",
                "message": f"Solution dispatched successfully to {clean_recipient}.",
                "recipient": clean_recipient,
                "sent_at": sent_timestamp
            }

        except Exception as e:
            logger.error(f"Failed to dispatch email to {clean_recipient}: {str(e)}")
            return {
                "success": False,
                "status": "DELIVERY_FAILED",
                "message": f"Email dispatch failed: {str(e)}",
                "recipient": clean_recipient,
                "sent_at": None
            }
