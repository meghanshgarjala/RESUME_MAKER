import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EmailAlert:
    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.from_email = os.getenv("ALERT_FROM_EMAIL", self.username)
        self.to_email = os.getenv("ALERT_TO_EMAIL", "")

    def enabled(self) -> bool:
        return bool(self.username and self.password and self.to_email)

    def send_job_alert(self, job: Dict[str, Any]) -> bool:
        if not self.enabled():
            logger.warning("Email alert skipped: SMTP env vars incomplete.")
            return False

        body = (
            "Job Match Found!\n\n"
            f"Title: {job.get('title')}\n"
            f"Company: {job.get('company', 'Unknown')}\n"
            f"Location: {job.get('location', 'Unknown')}\n"
            f"Match Score: {job.get('match_score')}%\n"
            f"Missing Skills: {job.get('missing_skills')}\n"
            f"Link: {job.get('link')}\n"
        )

        msg = MIMEText(body)
        msg["Subject"] = f"Career Radar Match: {job.get('title')}"
        msg["From"] = self.from_email
        msg["To"] = self.to_email

        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, [self.to_email], msg.as_string())
            logger.info("Sent job alert email for %s", job.get("title"))
            return True
        except (smtplib.SMTPException, TimeoutError):
            logger.exception("Failed to send job alert for %s", job.get("title"))
            return False
