from __future__ import annotations

import datetime as dt
from typing import Any

import frappe
from frappe.utils import now_datetime

from erpnext_google_drive_app.google_drive_integration.google_drive_client import (
    GoogleDriveClient,
)


SCOPES_DEFAULT = [
    # Full drive is simplest for folder + upload. Can be narrowed later.
    "https://www.googleapis.com/auth/drive",
]


def _get_settings():
    return frappe.get_single("Google Drive Settings")


def _get_client(settings: Any) -> GoogleDriveClient:
    client_secret = settings.get_password("client_secret") or ""
    access_token = settings.get_password("access_token") if settings.access_token else None
    refresh_token = settings.get_password("refresh_token") if settings.refresh_token else None
    return GoogleDriveClient(
        client_id=settings.client_id or "",
        client_secret=client_secret,
        redirect_uri=settings.redirect_uri or "",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=settings.token_expires_at or None,
    )


@frappe.whitelist()
def get_google_auth_url() -> dict[str, Any]:
    settings = _get_settings()
    if not settings.client_id or not settings.redirect_uri:
        frappe.throw("Set Client ID and Redirect URI in Google Drive Settings first.")

    client = _get_client(settings)
    state = "erpnext-google-drive"
    url = client.build_auth_url(scopes=SCOPES_DEFAULT, state=state)
    return {"auth_url": url}


@frappe.whitelist(allow_guest=True)
def google_oauth_callback(code: str | None = None, state: str | None = None) -> str:
    if not code:
        return """
        <html><body>
            <h2>Google OAuth Error</h2>
            <p>No authorization code received.</p>
            <p><a href="/app/google-drive-settings">Go to Google Drive Settings</a></p>
        </body></html>
        """

    try:
        settings = _get_settings()
        client_secret = settings.get_password("client_secret") or ""
        if not settings.client_id or not client_secret:
            return """
            <html><body>
                <h2>Google OAuth Error</h2>
                <p>Client ID/Secret not configured in Google Drive Settings.</p>
                <p><a href="/app/google-drive-settings">Go to Google Drive Settings</a></p>
            </body></html>
            """

        client = _get_client(settings)
        token_data = client.exchange_code_for_token(code)

        settings.access_token = token_data.get("access_token")
        if token_data.get("refresh_token"):
            settings.refresh_token = token_data.get("refresh_token")
        expires_in = int(token_data.get("expires_in") or 3600)
        settings.token_expires_at = now_datetime() + dt.timedelta(seconds=expires_in)
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        return """
        <html><body>
            <h2>Google OAuth Success</h2>
            <p>Connected to Google Drive successfully.</p>
            <p><a href="/app/google-drive-settings">Go to Google Drive Settings</a></p>
        </body></html>
        """
    except Exception as exc:
        frappe.log_error(f"Google OAuth callback error: {exc}", "Google Drive OAuth Error")
        return f"""
        <html><body>
            <h2>Google OAuth Error</h2>
            <p>Error: {exc}</p>
            <p><a href="/app/google-drive-settings">Go to Google Drive Settings</a></p>
        </body></html>
        """


@frappe.whitelist()
def test_google_drive_connection() -> dict[str, Any]:
    settings = _get_settings()
    client = _get_client(settings)

    # refresh if needed
    before_access = client.access_token
    before_exp = client.token_expires_at
    if client.access_token:
        client.ensure_valid_token()
    if client.access_token != before_access or client.token_expires_at != before_exp:
        settings.access_token = client.access_token
        settings.token_expires_at = client.token_expires_at
        settings.save(ignore_permissions=True)
        frappe.db.commit()

    data = client.test_connection()
    return {"ok": True, "message": "Connection OK.", "data": data}


__all__ = [
    "get_google_auth_url",
    "google_oauth_callback",
    "test_google_drive_connection",
]

