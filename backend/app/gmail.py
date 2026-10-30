"""Local Gmail OAuth connection and explicitly approved message delivery."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import getaddresses
from html import escape
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GOOGLE_FRONTEND_URL
from .db import connect, now_iso

router = APIRouter(prefix="/api/gmail", tags=["gmail"])
SCOPE = "openid email https://www.googleapis.com/auth/gmail.send"


def _configured():
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def _form_post(url: str, values: dict):
    request = urllib.request.Request(url, data=urllib.parse.urlencode(values).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(502, f"Google request failed: {exc}") from exc


def _api_get(url: str, token: str):
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        message = exc.read().decode(errors="replace")[:400]
        raise HTTPException(502, f"Gmail API returned HTTP {exc.code}: {message}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(502, f"Gmail API is unavailable: {exc}") from exc


def _account():
    with connect() as db:
        row = db.execute("SELECT * FROM gmail_accounts ORDER BY updated_at DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def _fresh_access_token(account: dict):
    if float(account["expires_at"]) > time.time() + 60:
        return account["access_token"]
    values = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": account["refresh_token"],
        "grant_type": "refresh_token",
    }
    result = _form_post("https://oauth2.googleapis.com/token", values)
    expires = time.time() + int(result.get("expires_in", 3600))
    with connect() as db:
        db.execute("UPDATE gmail_accounts SET access_token=?,expires_at=?,updated_at=? WHERE id=?",
                   (result["access_token"], str(expires), now_iso(), account["id"]))
    return result["access_token"]


@router.get("/status")
def gmail_status():
    account = _account()
    return {"configured": _configured(), "connected": bool(account), "email": account["email"] if account else None,
            "scope": "Send email only"}


@router.get("/connect")
def gmail_connect():
    if not _configured():
        raise HTTPException(503, "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, then restart Threadline.")
    state = uuid4().hex + uuid4().hex
    with connect() as db:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(timespec="seconds")
        db.execute("DELETE FROM gmail_oauth_states WHERE created_at < ?", (cutoff,))
        db.execute("INSERT INTO gmail_oauth_states(state,created_at) VALUES(?,?)", (state, now_iso()))
    params = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/oauth/callback", response_class=HTMLResponse)
def gmail_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return HTMLResponse("<h2>Gmail connection cancelled</h2><p>Return to Threadline and try again when ready.</p>", status_code=400)
    if not code or not state:
        raise HTTPException(400, "Google did not return an authorization code and state.")
    with connect() as db:
        saved = db.execute("SELECT created_at FROM gmail_oauth_states WHERE state=?", (state,)).fetchone()
        db.execute("DELETE FROM gmail_oauth_states WHERE state=?", (state,))
    if not saved or (datetime.now(timezone.utc) - datetime.fromisoformat(saved["created_at"]).astimezone(timezone.utc)).total_seconds() > 900:
        raise HTTPException(400, "Gmail authorization expired or state did not match. Start again from Threadline.")
    tokens = _form_post("https://oauth2.googleapis.com/token", {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if not tokens.get("refresh_token"):
        raise HTTPException(400, "Google did not return offline access. Disconnect the app from your Google account and reconnect with consent.")
    profile = _api_get("https://openidconnect.googleapis.com/v1/userinfo", tokens["access_token"])
    email = profile.get("email")
    if not email or not profile.get("email_verified"):
        raise HTTPException(400, "Google did not verify an email address for this account.")
    now = now_iso()
    with connect() as db:
        db.execute("DELETE FROM gmail_accounts")
        db.execute("INSERT INTO gmail_accounts(id,email,access_token,refresh_token,expires_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                   (str(uuid4()), email, tokens["access_token"], tokens["refresh_token"], str(time.time() + int(tokens.get("expires_in", 3600))), now, now))
    page = f"<meta http-equiv='refresh' content='2;url={escape(GOOGLE_FRONTEND_URL, quote=True)}'><h2>Gmail connected</h2><p>{escape(email)} is connected to Threadline. Return to the app to continue.</p>"
    return HTMLResponse(page)


@router.delete("/disconnect")
def gmail_disconnect():
    account = _account()
    if account:
        try:
            revoke = urllib.request.Request("https://oauth2.googleapis.com/revoke",
                                            data=urllib.parse.urlencode({"token": account["refresh_token"]}).encode(),
                                            headers={"Content-Type": "application/x-www-form-urlencoded"})
            urllib.request.urlopen(revoke, timeout=10).close()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            pass
    with connect() as db:
        db.execute("DELETE FROM gmail_accounts")
    return {"connected": False}


def send_gmail_message(to: str, subject: str, body: str):
    """Send only after the existing action approval checkpoint."""
    account = _account()
    if not account:
        raise HTTPException(409, "Connect Gmail before approving this email.")
    parsed = getaddresses([to])
    parsed_email = parsed[0][1] if len(parsed) == 1 else ""
    if not parsed_email or "@" not in parsed_email or "\n" in to or "\r" in to:
        raise HTTPException(422, "Enter a valid recipient email address before approving.")
    message = EmailMessage()
    message["To"] = parsed_email
    message["From"] = account["email"]
    message["Subject"] = subject.replace("\r", " ").replace("\n", " ")[:250]
    message.set_content(body[:100_000])
    import base64
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    access_token = _fresh_access_token(account)
    request = urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                                     data=json.dumps({"raw": raw}).encode(),
                                     headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                                     method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            receipt = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:400]
        raise HTTPException(502, f"Gmail could not send this message (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(502, f"Gmail could not be reached: {exc}") from exc
    return {"message": f"Email sent from {account['email']} to {parsed_email}.", "sent": True,
            "from": account["email"], "to": parsed_email, "subject": subject, "gmail_message_id": receipt.get("id")}
