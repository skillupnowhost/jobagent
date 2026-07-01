import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path
from app.config import get_settings

settings = get_settings()


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.from_name = settings.from_name

    def send_application_email(self, to_email: str, subject: str,
                               body: str, resume_path: str = None,
                               cover_letter_path: str = None) -> dict:
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            if resume_path and Path(resume_path).exists():
                with open(resume_path, "rb") as f:
                    attachment = MIMEApplication(f.read(), _subtype="pdf")
                    attachment.add_header(
                        "Content-Disposition", "attachment",
                        filename=Path(resume_path).name,
                    )
                    msg.attach(attachment)

            if cover_letter_path and Path(cover_letter_path).exists():
                with open(cover_letter_path, "rb") as f:
                    attachment = MIMEApplication(f.read(), _subtype="pdf")
                    attachment.add_header(
                        "Content-Disposition", "attachment",
                        filename="Cover_Letter.pdf",
                    )
                    msg.attach(attachment)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return {"success": True, "message": "Email sent successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def send_follow_up_email(self, to_email: str, original_subject: str,
                             candidate_name: str, job_title: str,
                             company: str, applied_date: str) -> dict:
        subject = f"Follow-up: {original_subject}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Dear Hiring Manager,</p>

            <p>I hope this message finds you well. I am writing to follow up on my application
            for the <strong>{job_title}</strong> position at <strong>{company}</strong>,
            submitted on {applied_date}.</p>

            <p>I remain very enthusiastic about the opportunity to contribute to your team.
            My experience in software testing and quality assurance aligns well with the
            requirements of this role, and I am confident I can make meaningful contributions
            from day one.</p>

            <p>I would welcome the opportunity to discuss my qualifications further at your
            convenience. Please feel free to reach out if you need any additional information.</p>

            <p>Thank you for your time and consideration.</p>

            <p>Best regards,<br>
            <strong>{candidate_name}</strong></p>
        </body>
        </html>
        """
        return self.send_application_email(to_email, subject, body)

    def build_application_email_body(self, candidate_name: str, job_title: str,
                                     company: str, cover_letter: str) -> str:
        cover_letter_html = cover_letter.replace("\n", "<br>")
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Dear Hiring Manager,</p>

            <p>Please find attached my resume for the <strong>{job_title}</strong>
            position at <strong>{company}</strong>.</p>

            <hr style="border: 1px solid #eee; margin: 20px 0;">

            {cover_letter_html}

            <hr style="border: 1px solid #eee; margin: 20px 0;">

            <p>Best regards,<br>
            <strong>{candidate_name}</strong></p>
        </body>
        </html>
        """

    def validate_email_content(self, subject: str, body: str) -> list[str]:
        errors = []
        if not subject or len(subject) < 5:
            errors.append("Subject line is too short or empty")
        if len(subject) > 200:
            errors.append("Subject line exceeds 200 characters")
        if not body or len(body) < 50:
            errors.append("Email body is too short")
        placeholder_patterns = ["[your name]", "[company]", "[position]", "xxx", "todo"]
        for pattern in placeholder_patterns:
            if pattern.lower() in body.lower():
                errors.append(f"Unfilled placeholder found: '{pattern}'")
        return errors
