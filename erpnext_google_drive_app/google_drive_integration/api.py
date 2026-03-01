from __future__ import annotations

import datetime as dt
from typing import Any

import frappe
import requests
from frappe.utils import now_datetime

from erpnext_google_drive_app.google_drive_integration.google_drive_client import (
    GoogleAuthError,
    GoogleDriveClient,
)


SCOPES_DEFAULT = [
    # Full drive is simplest for folder + upload. Can be narrowed later.
    "https://www.googleapis.com/auth/drive",
]


def _get_settings():
    return frappe.get_single("Google Drive Settings")


def _get_client(settings: Any) -> GoogleDriveClient:
    settings.reload()
    client_secret = settings.get_password(fieldname="client_secret", raise_exception=False) or ""
    access_token = settings.get_password(fieldname="access_token", raise_exception=False)
    refresh_token = settings.get_password(fieldname="refresh_token", raise_exception=False)
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


_SETTINGS_PATH = "/app/google-drive-settings"


@frappe.whitelist(allow_guest=True)
def google_oauth_callback(code: str | None = None, state: str | None = None):
    if not code:
        frappe.respond_as_web_page(
            title="Google OAuth Error",
            html="No authorization code received.",
            primary_action=_SETTINGS_PATH,
            primary_label="Go to Google Drive Settings",
            success=False,
        )
        return

    try:
        settings = _get_settings()
        client_secret = settings.get_password("client_secret") or ""
        if not settings.client_id or not client_secret:
            frappe.respond_as_web_page(
                title="Google OAuth Error",
                html="Client ID/Secret not configured in Google Drive Settings.",
                primary_action=_SETTINGS_PATH,
                primary_label="Go to Google Drive Settings",
                success=False,
            )
            return

        client = _get_client(settings)
        token_data = client.exchange_code_for_token(code)

        settings.access_token = token_data.get("access_token")
        if token_data.get("refresh_token"):
            settings.refresh_token = token_data.get("refresh_token")
        expires_in = int(token_data.get("expires_in") or 3600)
        settings.token_expires_at = now_datetime() + dt.timedelta(seconds=expires_in)
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        # Redirect back to Google Drive Settings so user sees the app, not raw JSON
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = frappe.utils.get_url(_SETTINGS_PATH)
    except Exception as exc:
        frappe.log_error(f"Google OAuth callback error: {exc}", "Google Drive OAuth Error")
        frappe.respond_as_web_page(
            title="Google OAuth Error",
            html=f"Error: {exc}",
            primary_action=_SETTINGS_PATH,
            primary_label="Go to Google Drive Settings",
            success=False,
        )


@frappe.whitelist()
def test_google_drive_connection() -> dict[str, Any]:
    settings = _get_settings()
    client = _get_client(settings)

    # Must have connected at least once (need access_token or refresh_token)
    if not client.access_token and not client.refresh_token:
        return {
            "ok": False,
            "message": "Connect to Google first. Click 'Connect to Google Drive', authorize in the popup, then try Test Connection again.",
        }

    try:
        # Ensure we have a valid access_token (refresh if needed)
        before_access = client.access_token
        before_exp = client.token_expires_at
        if client.access_token:
            client.ensure_valid_token()
        elif client.refresh_token:
            token_data = client.refresh_access_token()
            client.access_token = token_data.get("access_token")
            expires_in = int(token_data.get("expires_in") or 3600)
            client.token_expires_at = now_datetime() + dt.timedelta(seconds=expires_in)
            settings.access_token = client.access_token
            settings.token_expires_at = client.token_expires_at
            settings.save(ignore_permissions=True)
            frappe.db.commit()

        if client.access_token != before_access or client.token_expires_at != before_exp:
            settings.access_token = client.access_token
            settings.token_expires_at = client.token_expires_at
            settings.save(ignore_permissions=True)
            frappe.db.commit()

        # Must have access_token before testing
        if not client.access_token:
            return {
                "ok": False,
                "message": "Could not obtain access token. Click 'Connect to Google Drive' to re-authorize.",
            }

        data = client.test_connection()
        return {"ok": True, "message": "Connection OK.", "data": data}
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            return {
                "ok": False,
                "message": (
                    "Google Drive returned 403 Forbidden. "
                    "In Google Cloud Console: enable 'Google Drive API' (APIs & Services → Library → search 'Google Drive API' → Enable). "
                    "Then click 'Connect to Google Drive' to re-authorize with Drive access."
                ),
            }
        return {"ok": False, "message": f"Google Drive request failed: {e}"}
    except GoogleAuthError as e:
        msg = str(e)
        if "Connect" in msg or "Missing" in msg:
            friendly = "Click 'Connect to Google Drive' to authorize, then try Test Connection again."
        else:
            friendly = f"{msg} Try reconnecting via 'Connect to Google Drive'."
        return {"ok": False, "message": friendly}


__all__ = [
    "get_google_auth_url",
    "google_oauth_callback",
    "test_google_drive_connection",
]

