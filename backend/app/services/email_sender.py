import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _send(to_email: str, subject: str, html_body: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured; skipping email send to %s (subject=%s)", to_email, subject)
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.from_name} <{settings.from_email or settings.smtp_user}>"
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, [to_email], message.as_string())


def send_verification_email(to_email: str, name: str, verify_url: str) -> None:
    template = _env.get_template("verify_email.html")
    html_body = template.render(
        name=name, verify_url=verify_url, expire_hours=settings.jwt_email_verify_expire_hours
    )
    _send(to_email, "Verify your email address", html_body)
