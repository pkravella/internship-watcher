"""
notifier.py
~~~~~~~~~~~
Send an HTML email containing the new internship listings.
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import List, Dict

def _smtp_params() -> tuple[str, int, str, str]:
    """Read SMTP settings from environment variables."""
    return (
        os.getenv("SMTP_SERVER", ""),
        int(os.getenv("SMTP_PORT", "465")),
        os.getenv("SMTP_USER", ""),
        os.getenv("SMTP_PASS", ""),
    )

def notify(new_rows: List[Dict[str, str]]) -> None:
    server, port, user, password = _smtp_params()
    if not all([server, port, user, password]):
        raise RuntimeError("Missing SMTP_* environment variables!")

    # --- Build email ---
    msg          = EmailMessage()
    msg["From"]  = os.getenv("EMAIL_FROM", user)
    msg["To"]    = os.getenv("EMAIL_TO", user)
    msg["Subject"] = f"[Internship Alert] {len(new_rows)} new listing(s)"

    # Plain‑text alternative (spam filters like multipart emails)
    plain = "New internships:\n\n" + "\n".join(
        f"- {r['company']} — {r['role']} ({r['link']})"
        for r in new_rows
    )
    msg.set_content(plain)

    # HTML part
    html_rows = "\n".join(
        f"<li><b>{r['company']}</b> — {r['role']} — "
        f"<a href='{r['link']}'>Apply</a></li>"
        for r in new_rows
    )
    msg.add_alternative(
        f"<h2>🚀 New internship listings</h2><ul>{html_rows}</ul>"
        "<p style='font-size:smaller'>Source: "
        "<a href='https://github.com/vanshb03/Summer2026-Internships'>GitHub list</a></p>",
        subtype="html",
    )

    # --- Send email ---
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(server, port, context=context) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
