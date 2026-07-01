import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.config import get_settings

settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        creds = None
        token_file = settings.google_token_file
        creds_file = settings.google_credentials_file

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(creds_file):
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, "w") as token:
                    token.write(creds.to_json())
            else:
                return

        if creds:
            self.service = build("calendar", "v3", credentials=creds)

    def create_follow_up_reminder(self, job_title: str, company: str,
                                  follow_up_date: datetime,
                                  application_id: int) -> dict | None:
        if not self.service:
            return None

        event = {
            "summary": f"Follow up: {job_title} at {company}",
            "description": (
                f"Follow up on your application for {job_title} at {company}.\n"
                f"Application ID: {application_id}\n"
                f"Action: Send a follow-up email or check application status."
            ),
            "start": {
                "dateTime": follow_up_date.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": (follow_up_date + timedelta(minutes=30)).isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "email", "minutes": 60},
                ],
            },
            "colorId": "5",
        }

        try:
            created = self.service.events().insert(
                calendarId="primary", body=event
            ).execute()
            return {
                "event_id": created.get("id"),
                "html_link": created.get("htmlLink"),
                "start": follow_up_date.isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def create_interview_event(self, job_title: str, company: str,
                               interview_date: datetime,
                               duration_minutes: int = 60,
                               notes: str = "") -> dict | None:
        if not self.service:
            return None

        event = {
            "summary": f"Interview: {job_title} at {company}",
            "description": (
                f"Interview for {job_title} position at {company}.\n\n"
                f"Preparation Notes:\n{notes}"
            ),
            "start": {
                "dateTime": interview_date.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": (interview_date + timedelta(minutes=duration_minutes)).isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 1440},
                ],
            },
            "colorId": "11",
        }

        try:
            created = self.service.events().insert(
                calendarId="primary", body=event
            ).execute()
            return {
                "event_id": created.get("id"),
                "html_link": created.get("htmlLink"),
                "start": interview_date.isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def create_daily_report_reminder(self) -> dict | None:
        if not self.service:
            return None

        tomorrow = datetime.now() + timedelta(days=1)
        report_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

        event = {
            "summary": "Job Agent: Review Daily Report",
            "description": "Check your AI Job Agent dashboard for today's application report.",
            "start": {
                "dateTime": report_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": (report_time + timedelta(minutes=15)).isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=30"],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 5},
                ],
            },
        }

        try:
            created = self.service.events().insert(
                calendarId="primary", body=event
            ).execute()
            return {"event_id": created.get("id"), "html_link": created.get("htmlLink")}
        except Exception as e:
            return {"error": str(e)}

    def get_upcoming_events(self, max_results: int = 10) -> list[dict]:
        if not self.service:
            return []

        now = datetime.utcnow().isoformat() + "Z"
        try:
            result = self.service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = result.get("items", [])
            return [
                {
                    "id": e.get("id"),
                    "summary": e.get("summary"),
                    "start": e.get("start", {}).get("dateTime"),
                    "end": e.get("end", {}).get("dateTime"),
                    "link": e.get("htmlLink"),
                }
                for e in events
            ]
        except Exception:
            return []
