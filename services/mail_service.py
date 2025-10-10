import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional
from config.appliccation_config import ApplicationConfig
from config.smtp_config import SmtpConfig
from logic.singleton import Singleton


from utils.Os import Os


class MailService(metaclass=Singleton):
    """
    Simple SMTP mailer that sends HTML emails with optional calendar invites
    compatible with Google Calendar and Outlook by attaching a text/calendar
    (iCalendar/ICS) alternative part.
    """

    def __init__(self, config: SmtpConfig=None):
        if config is None:
            self.config = ApplicationConfig().mail_server
        else:
             self.config = config
        self.logger = logging.getLogger(__name__)

    # Public API
    def send_html(
        self,
        to: Iterable[str] | str,
        subject: str,
        html_body: str,
        from_email: Optional[str] = None,
        cc: Optional[Iterable[str] | str] = None,
        bcc: Optional[Iterable[str] | str] = None,
    ) -> None:
        self._send_message(
            to=self._ensure_list(to),
            subject=subject,
            from_email=from_email or self.config.sender_email or (self.config.username or ""),
            html_body=html_body,
            ics_text=None,
            cc=self._ensure_list(cc),
            bcc=self._ensure_list(bcc),
        )

    def send_with_calendar_invite(
        self,
        to: Iterable[str] | str,
        subject: str,
        html_body: str,
        *,
        start: datetime,
        end: datetime,
        organizer_email: str,
        organizer_name: Optional[str] = None,
        location: Optional[str] = None,
        description_text: Optional[str] = None,
        uid: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[Iterable[str] | str] = None,
        bcc: Optional[Iterable[str] | str] = None,
        alarm_minutes_before: Optional[int] = 15,
    ) -> None:
        """
        Sends an HTML email with an iCalendar invite attached. Works for Google and Outlook.
        """
        ics = self._build_ics(
            subject=subject,
            start=start,
            end=end,
            organizer_email=organizer_email,
            organizer_name=organizer_name,
            attendees=self._ensure_list(to),
            location=location,
            description=description_text or self._strip_html(html_body),
            uid=uid,
            alarm_minutes_before=alarm_minutes_before,
        )
        self._send_message(
            to=self._ensure_list(to),
            subject=subject,
            from_email=from_email or self.config.sender_email or (self.config.username or ""),
            html_body=html_body,
            ics_text=ics,
            cc=self._ensure_list(cc),
            bcc=self._ensure_list(bcc),
        )

    # Internals
    def _send_message(
        self,
        *,
        to: list[str],
        subject: str,
        from_email: str,
        html_body: str,
        ics_text: Optional[str],
        cc: Optional[list[str]],
        bcc: Optional[list[str]],
    ) -> None:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)

        # Alternative part (HTML and optional calendar)
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(self._fallback_plain(html_body), "plain", "utf-8"))
        alt.attach(MIMEText(html_body, "html", "utf-8"))

        if ics_text:
            # text/calendar as alternative for clients to parse the invite
            cal_part = MIMEText(ics_text, "calendar", "utf-8")
            cal_part.add_header("Content-Class", "urn:content-classes:calendarmessage")
            cal_part.add_header("Content-ID", "<calendar_invite>")
            cal_part.replace_header("Content-Type", "text/calendar; method=REQUEST; charset=UTF-8")
            alt.attach(cal_part)

        msg.attach(alt)

        recipients = list({*to, *(cc or []), *(bcc or [])})
        self._deliver(from_email, recipients, msg)

    def _deliver(self, from_email: str, recipients: list[str], msg: MIMEMultipart) -> None:

        if not Os.is_alive(self.config.host):
            logging.error(f"SMTP server {self.config.host} is not alive")
            return
        try:
            if self.config.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.config.host, self.config.port, context=context) as server:
                    self._maybe_login(server)
                    server.sendmail(from_email, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.config.host, self.config.port) as server:
                    if self.config.use_tls:
                        server.starttls(context=ssl.create_default_context())
                    self._maybe_login(server)
                    server.sendmail(from_email, recipients, msg.as_string())
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def _maybe_login(self, server: smtplib.SMTP) -> None:
        if self.config.username and self.config.password:
            server.login(self.config.username, self.config.password)

    @staticmethod
    def _ensure_list(val: Optional[Iterable[str] | str]) -> Optional[list[str]]:
        if val is None:
            return None
        if isinstance(val, str):
            return [val]
        return list(val)

    @staticmethod
    def _strip_html(html: str) -> str:
        # lightweight fallback; for better results use an HTML-to-text lib
        import re
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()

    @staticmethod
    def _fallback_plain(html: str) -> str:
        return MailService._strip_html(html)

    @staticmethod
    def _fmt_dt(dt: datetime) -> str:
        # ICS requires UTC Zulu format, ensure timezone-naive treated as UTC
        if dt.tzinfo is None:
            return dt.strftime("%Y%m%dT%H%M%SZ")
        return dt.astimezone(tz=MailService._utc()).strftime("%Y%m%dT%H%M%SZ")

    @staticmethod
    def _utc():
        from datetime import timezone
        return timezone.utc

    def _build_ics(
        self,
        *,
        subject: str,
        start: datetime,
        end: datetime,
        organizer_email: str,
        organizer_name: Optional[str],
        attendees: list[str],
        location: Optional[str],
        description: Optional[str],
        uid: Optional[str],
        alarm_minutes_before: Optional[int],
    ) -> str:
        dtstamp = self._fmt_dt(datetime.utcnow())
        dtstart = self._fmt_dt(start)
        dtend = self._fmt_dt(end)
        uid_val = uid or f"{dtstart}-{organizer_email}"

        organizer_cn = f"CN={organizer_name}" if organizer_name else ""
        organizer = f"ORGANIZER;{organizer_cn}:mailto:{organizer_email}" if organizer_cn else f"ORGANIZER:mailto:{organizer_email}"

        attn_lines = []
        for a in attendees:
            attn_lines.append(
                f"ATTENDEE;CN={a};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{a}"
            )

        alarm_block = ""
        if alarm_minutes_before and alarm_minutes_before > 0:
            # VALARM as a popup reminder
            alarm_block = (
                "BEGIN:VALARM\r\n"
                f"TRIGGER:-PT{int(alarm_minutes_before)}M\r\n"
                "ACTION:DISPLAY\r\n"
                "DESCRIPTION:Reminder\r\n"
                "END:VALARM\r\n"
            )

        loc_line = f"LOCATION:{self._escape_ics(location)}\r\n" if location else ""
        desc_line = f"DESCRIPTION:{self._escape_ics(description)}\r\n" if description else ""

        ics = (
            "BEGIN:VCALENDAR\r\n"
            "PRODID:-//WarriorFit//MailService//EN\r\n"
            "VERSION:2.0\r\n"
            "METHOD:REQUEST\r\n"
            "CALSCALE:GREGORIAN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{uid_val}\r\n"
            f"DTSTAMP:{dtstamp}\r\n"
            f"SUMMARY:{self._escape_ics(subject)}\r\n"
            f"DTSTART:{dtstart}\r\n"
            f"DTEND:{dtend}\r\n"
            f"{organizer}\r\n"
            f"{''.join(a + '\\r\\n' for a in attn_lines)}"
            f"{loc_line}"
            f"{desc_line}"
            "STATUS:CONFIRMED\r\n"
            f"{alarm_block}"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        return ics

    @staticmethod
    def _escape_ics(val: Optional[str]) -> str:
        if not val:
            return ""
        # Escape commas, semicolons, and backslashes; replace newlines
        return (
            val.replace("\\", "\\\\")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("\r\n", "\\n")
            .replace("\n", "\\n")
            .replace("\r", "\\n")
        )


# Example usage (remove or adapt in production):
if __name__ == "__main__":
    cfg = SmtpConfig(
        host="192.168.0.174",
        port=25,
        username="benoit",
        password="R@nger&1401!",
        sender_email="benoit@albatros.be",
    )
    ms = MailService(cfg)
    start_dt = datetime.utcnow() + timedelta(days=1)
    end_dt = start_dt + timedelta(hours=1)
    html = """
    <h2>Training Session</h2>
    <p>Hello,<br/>Please find below the meeting details.</p>
    <ul>
      <li>Topic: Fitness Assessment</li>
      <li>When: Tomorrow</li>
    </ul>
    """
    ms.send_html("person@example.com", "Plain HTML Test", html)
    ms.send_with_calendar_invite(
        to=["benoit@albatros.be"],
        subject="Fitness Assessment Invite",
        html_body=html,
        start=start_dt,
        end=end_dt,
        organizer_email="benoit@albatros.be",
        organizer_name="Coach",
        location="Gym Hall A",
    )
