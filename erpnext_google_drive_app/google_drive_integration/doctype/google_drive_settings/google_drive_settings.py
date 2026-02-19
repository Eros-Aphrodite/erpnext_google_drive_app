from __future__ import annotations

import frappe
from frappe.model.document import Document

from erpnext_google_drive_app.google_drive_integration.google_drive_client import (
    GoogleDriveClient,
)


class GoogleDriveSettings(Document):
    def get_client(self) -> GoogleDriveClient:
        client_secret = self.get_password("client_secret") or ""
        access_token = self.get_password("access_token") if self.access_token else None
        refresh_token = self.get_password("refresh_token") if self.refresh_token else None
        return GoogleDriveClient(
            client_id=self.client_id or "",
            client_secret=client_secret,
            redirect_uri=self.redirect_uri or "",
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=self.token_expires_at or None,
        )


__all__ = ["GoogleDriveSettings"]

