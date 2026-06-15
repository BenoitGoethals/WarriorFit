import logging
import os
import smtplib
import ssl
from collections.abc import Iterable
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.utils.Os import Os


class MailService:
    """
    Simple SMTP mailer that sends HTML emails with optional calendar invites
    compatible with Google Calendar and Outlook by attaching a text/calendar
    (iCalendar/ICS) alternative part.
    """

    def __init__(self, config: ApplicationConfig = None):
        if config is None:
            config = ApplicationConfig()
        self.config = config.mail_server
        self._logger = logging.getLogger(__name__)

    # Public API
    def send_html(
        self,
        to: Iterable[str] | str,
        subject: str,
        html_body: str,
        from_email: str | None = None,
        cc: Iterable[str] | str | None = None,
        bcc: Iterable[str] | str | None = None,
    ) -> None:
        """
        Sends an HTML email message to one or more recipients with optional CC and BCC recipients.

        The method ensures that recipient(s) provided for the 'to', 'cc', and 'bcc' fields are
        converted into a list format if they are not already. An HTML body must be provided for
        the email, and a sender email address is either explicitly supplied or derived from
        the configuration.

        :param to: One or more email addresses of the primary recipient(s).
        :type to: Iterable[str] or str
        :param subject: Subject line of the email to be sent.
        :type subject: str
        :param html_body: HTML formatted body content of the email.
        :type html_body: str
        :param from_email: Email address used as the sender. Defaults to None, in which case, the
            sender address will be determined from the configuration.
        :type from_email: str or None
        :param cc: Optional CC recipient(s) email address(es).
        :type cc: Iterable[str] or str or None
        :param bcc: Optional BCC recipient(s) email address(es).
        :type bcc: Iterable[str] or str or None
        :return: None
        """
        self._send_message(
            to=self._ensure_list(to),  # type: ignore[arg-type]
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
        organizer_name: str | None = None,
        location: str | None = None,
        description_text: str | None = None,
        uid: str | None = None,
        from_email: str | None = None,
        cc: Iterable[str] | str | None = None,
        bcc: Iterable[str] | str | None = None,
        alarm_minutes_before: int | None = 15,
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
            attendees=self._ensure_list(to),  # type: ignore[arg-type]
            location=location,
            description=description_text or self._strip_html(html_body),
            uid=uid,
            alarm_minutes_before=alarm_minutes_before,
        )
        self._send_message(
            to=self._ensure_list(to),  # type: ignore[arg-type]
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
        ics_text: str | None,
        cc: list[str] | None,
        bcc: list[str] | None,
    ) -> None:
        """
        Sends an email message with optional calendar invite functionality and handles recipients' email addresses.

        This method creates a multipart MIME email message, including alternative plain text and HTML formats for
        the email body. It optionally attaches a calendar invite (if provided) as an additional alternative part
        in the message. The message is sent to the specified recipients, including optional CC and BCC recipients.

        :param to: A list of recipient email addresses.
        :type to: list[str]
        :param subject: The subject of the email.
        :type subject: str
        :param from_email: The sender's email address.
        :type from_email: str
        :param html_body: The HTML content for the email body.
        :type html_body: str
        :param ics_text: Optional iCalendar content for adding a calendar invite to the email.
        :type ics_text: str | None
        :param cc: Optional list of CC recipient email addresses.
        :type cc: list[str] | None
        :param bcc: Optional list of BCC recipient email addresses.
        :type bcc: list[str] | None
        :return: This method does not return any value.
        :rtype: None
        """
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
        """
        Delivers an email message using SMTP protocol. Depending on the configuration, the
        method can send an email using SSL or TLS encryption. If the application is running
        in development mode or the SMTP server is not alive, the email is not sent.

        :param from_email: The sender's email address.
        :type from_email: str
        :param recipients: List of recipient email addresses.
        :type recipients: list[str]
        :param msg: The email message to be delivered, represented as a MIMEMultipart object.
        :type msg: MIMEMultipart
        :return: None

        :raises smtplib.SMTPException: Raised if an error occurs during the SMTP communication.
        :raises OSError: Raised for OS-level errors during email sending.

        """
        if os.getenv("APP_ENV", "development") == "development":
            self._logger.debug("Mail suppressed in development mode")
            return

        if not Os.is_alive(self.config.host):
            logging.error(f"SMTP server {self.config.host} is not alive")
            return
        try:
            if self.config.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.config.host, self.config.port, context=context
                ) as server:
                    self._maybe_login(server)
                    server.sendmail(from_email, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.config.host, self.config.port) as server:
                    if self.config.use_tls:
                        server.starttls(context=ssl.create_default_context())
                    self._maybe_login(server)
                    server.sendmail(from_email, recipients, msg.as_string())
        except (smtplib.SMTPException, OSError) as e:
            logging.error(f"Failed to send email: {e}")

    def _maybe_login(self, server: smtplib.SMTP) -> None:
        if self.config.username and self.config.password:
            if server.has_extn("AUTH"):
                server.login(self.config.username, self.config.password)
            else:
                self._logger.warning("SMTP server does not support authentication, skipping login")

    @staticmethod
    def _ensure_list(val: Iterable[str] | str | None) -> list[str] | None:
        """
        Ensures that the input value is converted to a list of strings. This method is useful for
        normalizing input values which may be provided as a string, a list of strings, or None.

        :param val: An input value that can be one of the following:
                    - A string, which will be wrapped in a list
                    - An iterable of strings, which will be converted to a list
                    - None, which will be returned as None
        :type val: Iterable[str] | str | None
        :return: A list of strings if the input is valid or None if the input is None.
        :rtype: list[str] | None
        """
        if val is None:
            return None
        if isinstance(val, str):
            return [val]
        return list(val)

    @staticmethod
    def _strip_html(html: str) -> str:
        """
        Removes HTML tags from a given string and replaces <br> tags with a newline character.
        This is a lightweight utility function and does not guarantee perfect HTML stripping.

        :param html: The string containing HTML content.
        :type html: str
        :return: A cleaned string with HTML tags removed and <br> tags replaced by newlines.
        :rtype: str
        """
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

        return UTC

    def _build_ics(
        self,
        *,
        subject: str,
        start: datetime,
        end: datetime,
        organizer_email: str,
        organizer_name: str | None,
        attendees: list[str],
        location: str | None,
        description: str | None,
        uid: str | None,
        alarm_minutes_before: int | None,
    ) -> str:
        """
        Builds an ICS (iCalendar) formatted event string for email and calendar integration. This method formats the necessary
        event information, including subject, timing, organizer, attendees, location, description, unique identifier, and an
        optional alarm reminder. The generated ICS content complies with the iCalendar standard and can be used to create,
        modify, or send calendar events.

        :param subject: The event's subject or title.
        :type subject: str
        :param start: The start datetime of the event.
        :type start: datetime
        :param end: The end datetime of the event.
        :type end: datetime
        :param organizer_email: The email address of the event organizer.
        :type organizer_email: str
        :param organizer_name: The name of the event organizer, if available.
        :type organizer_name: str | None
        :param attendees: A list of attendee email addresses.
        :type attendees: list[str]
        :param location: The event location, if available.
        :type location: str | None
        :param description: A description of the event, if provided.
        :type description: str | None
        :param uid: A unique identifier (UID) for the event. If not provided, a UID is generated automatically.
        :type uid: str | None
        :param alarm_minutes_before: The number of minutes before the event for an alarm reminder, if applicable.
        :type alarm_minutes_before: int | None
        :return: A string containing the ICS-formatted event data, ready to use for calendar integration or email attachments.
        :rtype: str
        """
        dtstamp = self._fmt_dt(datetime.utcnow())
        dtstart = self._fmt_dt(start)
        dtend = self._fmt_dt(end)
        uid_val = uid or f"{dtstart}-{organizer_email}"

        organizer_cn = f"CN={organizer_name}" if organizer_name else ""
        organizer = (
            f"ORGANIZER;{organizer_cn}:mailto:{organizer_email}"
            if organizer_cn
            else f"ORGANIZER:mailto:{organizer_email}"
        )

        attn_lines = [
            f"ATTENDEE;CN={a};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{a}"
            for a in attendees
        ]

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
    def _escape_ics(val: str | None) -> str:
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


# if __name__ == "__main__":
#     cfg = SmtpConfig(
#         host="192.168.0.174",
#         port=25,
#         username="benoit",
#         password="R@nger&1401!",
#         sender_email="benoit@albatros.be",
#     )
#     ms = MailService(cfg)
#     start_dt = datetime.utcnow() + timedelta(days=1)
#     end_dt = start_dt + timedelta(hours=1)
#     html = """
#     <h2>Training Session</h2>
#     <p>Hello,<br/>Please find below the meeting details.</p>
#     <ul>
#       <li>Topic: Fitness Assessment</li>
#       <li>When: Tomorrow</li>
#     </ul>
#     """
#     ms.send_html("person@example.com", "Plain HTML Test", html)
#     ms.send_with_calendar_invite(
#         to=["benoit@albatros.be"],
#         subject="Fitness Assessment Invite",
#         html_body=html,
#         start=start_dt,
#         end=end_dt,
#         organizer_email="benoit@albatros.be",
#         organizer_name="Coach",
#         location="Gym Hall A",
#     )
