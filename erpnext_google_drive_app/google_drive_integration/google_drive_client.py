from __future__ import annotations

import datetime as dt
import json
import logging
import mimetypes
import secrets
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GoogleAuthError(RuntimeError):
    pass


class GoogleDriveClient:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
    DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_expires_at: dt.datetime | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self._session = requests.Session()

    # ---------------- OAuth ----------------

    def build_auth_url(self, *, scopes: list[str], state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        from urllib.parse import urlencode

        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        resp = self._session.post(self.TOKEN_URL, data=data, timeout=30)
        if not resp.ok:
            raise GoogleAuthError(resp.text)
        return resp.json()

    def refresh_access_token(self) -> dict[str, Any]:
        if not self.refresh_token:
            raise GoogleAuthError("Missing refresh token.")
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        resp = self._session.post(self.TOKEN_URL, data=data, timeout=30)
        if not resp.ok:
            raise GoogleAuthError(resp.text)
        return resp.json()

    def ensure_valid_token(self, *, refresh_skew_seconds: int = 120) -> None:
        if not self.access_token:
            raise GoogleAuthError("Missing access token. Connect to Google first.")

        if not self.token_expires_at:
            return

        now = dt.datetime.utcnow()
        if self.token_expires_at.tzinfo is not None:
            now = dt.datetime.now(dt.timezone.utc)

        if self.token_expires_at <= now + dt.timedelta(seconds=refresh_skew_seconds):
            token_data = self.refresh_access_token()
            self.access_token = token_data.get("access_token")
            expires_in = int(token_data.get("expires_in") or 3600)
            self.token_expires_at = now + dt.timedelta(seconds=expires_in)

    # ---------------- HTTP helpers ----------------

    def _headers(self) -> Dict[str, str]:
        self.ensure_valid_token()
        return {"Authorization": f"Bearer {self.access_token}"}

    def test_connection(self) -> dict[str, Any]:
        """
        Lightweight call to confirm auth works: list 1 file.
        """
        params = {"pageSize": 1, "fields": "files(id,name)"}
        resp = self._session.get(self.DRIVE_FILES_URL, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---------------- Drive: folders ----------------

    def find_folder(self, *, name: str, parent_id: str | None) -> str | None:
        # Search for a folder with a given name (not trashed)
        # Escape quotes in name for Google Drive API query
        escaped_name = name.replace('"', '\\"')
        q = [
            'mimeType="application/vnd.google-apps.folder"',
            f'name="{escaped_name}"',
            "trashed=false",
        ]
        if parent_id:
            q.append(f'"{parent_id}" in parents')
        else:
            q.append("'root' in parents")

        params = {"q": " and ".join(q), "fields": "files(id,name)", "pageSize": 1}
        resp = self._session.get(self.DRIVE_FILES_URL, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        files = resp.json().get("files") or []
        return files[0]["id"] if files else None

    def create_folder(self, *, name: str, parent_id: str | None) -> str:
        body: Dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            body["parents"] = [parent_id]
        else:
            body["parents"] = ["root"]

        params = {"fields": "id"}
        resp = self._session.post(self.DRIVE_FILES_URL, headers={**self._headers(), "Content-Type": "application/json"}, params=params, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()["id"]

    def get_or_create_folder(self, *, name: str, parent_id: str | None) -> str:
        existing = self.find_folder(name=name, parent_id=parent_id)
        return existing or self.create_folder(name=name, parent_id=parent_id)

    # ---------------- Drive: upload ----------------

    def upload_file(
        self,
        *,
        filename: str,
        content_bytes: bytes,
        parent_id: str | None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        mime_type = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        meta: Dict[str, Any] = {"name": filename}
        if parent_id:
            meta["parents"] = [parent_id]
        else:
            meta["parents"] = ["root"]

        boundary = secrets.token_hex(16)
        meta_json = json.dumps(meta).encode("utf-8")

        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                meta_json,
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                f"Content-Type: {mime_type}\r\n\r\n".encode(),
                content_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )

        headers = {
            **self._headers(),
            "Content-Type": f'multipart/related; boundary="{boundary}"',
        }
        params = {"uploadType": "multipart", "fields": "id,webViewLink"}
        resp = self._session.post(self.DRIVE_UPLOAD_URL, headers=headers, params=params, data=body, timeout=60)
        resp.raise_for_status()
        return resp.json()


__all__ = ["GoogleDriveClient", "GoogleAuthError"]

