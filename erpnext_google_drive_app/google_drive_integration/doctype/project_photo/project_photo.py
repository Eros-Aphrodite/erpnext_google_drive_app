from __future__ import annotations

import mimetypes
from pathlib import Path

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils.file_manager import get_file_path

from erpnext_google_drive_app.google_drive_integration.doctype.google_drive_project_folder.google_drive_project_folder import (
    get_by_project,
)
from erpnext_google_drive_app.google_drive_integration.google_drive_client import GoogleDriveClient


def _get_settings():
    return frappe.get_single("Google Drive Settings")


def _get_client(settings) -> GoogleDriveClient:
    client_secret = settings.get_password("client_secret") or ""
    access_token = settings.get_password("access_token") if settings.access_token else None
    refresh_token = settings.get_password("refresh_token") if settings.refresh_token else None
    client = GoogleDriveClient(
        client_id=settings.client_id or "",
        client_secret=client_secret,
        redirect_uri=settings.redirect_uri or "",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=settings.token_expires_at or None,
    )
    # refresh if needed and persist
    before_access = client.access_token
    before_exp = client.token_expires_at
    if client.access_token:
        client.ensure_valid_token()
    if client.access_token != before_access or client.token_expires_at != before_exp:
        settings.access_token = client.access_token
        settings.token_expires_at = client.token_expires_at
        settings.save(ignore_permissions=True)
        frappe.db.commit()
    return client


def _ensure_before_after_folders(mapping, client: GoogleDriveClient, settings):
    """Ensure both Before and After subfolders exist for a project folder mapping.
    Creates missing subfolders and updates the mapping so a single project can
    receive both before and after photos.
    """
    if not mapping or not mapping.drive_folder_id:
        return mapping
    before_name = settings.before_folder_name or "Before"
    after_name = settings.after_folder_name or "After"
    updated = False
    if not mapping.before_folder_id:
        mapping.before_folder_id = client.get_or_create_folder(
            name=before_name, parent_id=mapping.drive_folder_id
        )
        updated = True
    if not mapping.after_folder_id:
        mapping.after_folder_id = client.get_or_create_folder(
            name=after_name, parent_id=mapping.drive_folder_id
        )
        updated = True
    if updated:
        mapping.save(ignore_permissions=True)
        frappe.db.commit()
    return mapping


def _ensure_project_folders(project_name: str, client: GoogleDriveClient, settings):
    """Ensure one Drive folder per project with Before and After subfolders.
    Multiple before and multiple after photos can be uploaded to the same project.
    """
    mapping = get_by_project(project_name)
    if mapping and mapping.drive_folder_id and mapping.before_folder_id and mapping.after_folder_id:
        return mapping
    # Existing mapping but missing Before/After subfolders (e.g. manually created)
    if mapping and mapping.drive_folder_id:
        return _ensure_before_after_folders(mapping, client, settings)

    project = frappe.get_doc("Project", project_name)
    folder_name = project.project_name or project.name

    parent_id = settings.root_folder_id or None
    project_folder_id = client.get_or_create_folder(name=folder_name, parent_id=parent_id)

    before_name = settings.before_folder_name or "Before"
    after_name = settings.after_folder_name or "After"
    before_id = client.get_or_create_folder(name=before_name, parent_id=project_folder_id)
    after_id = client.get_or_create_folder(name=after_name, parent_id=project_folder_id)

    drive_url = f"https://drive.google.com/drive/folders/{project_folder_id}"

    if mapping:
        mapping.drive_folder_id = project_folder_id
        mapping.drive_folder_url = drive_url
        mapping.before_folder_id = before_id
        mapping.after_folder_id = after_id
        mapping.save(ignore_permissions=True)
    else:
        mapping = frappe.get_doc(
            {
                "doctype": "Google Drive Project Folder",
                "project": project_name,
                "drive_folder_id": project_folder_id,
                "drive_folder_url": drive_url,
                "before_folder_id": before_id,
                "after_folder_id": after_id,
            }
        )
        mapping.insert(ignore_permissions=True)

    frappe.db.commit()
    return mapping


class ProjectPhoto(Document):
    def after_insert(self):
        self._maybe_upload()

    def on_update(self):
        self._maybe_upload()

    def _maybe_upload(self):
        settings = _get_settings()
        if not settings.auto_upload_project_photos:
            return

        if self.google_drive_file_id:
            return

        if not self.photo:
            return

        client = _get_client(settings)

        if settings.auto_create_project_folder:
            mapping = _ensure_project_folders(self.project, client, settings)
        else:
            mapping = get_by_project(self.project)
            if not mapping or not mapping.drive_folder_id:
                frappe.throw(
                    "Drive folder mapping not found. Enable auto-create project folder or create a Google Drive Project Folder record."
                )
            # Ensure both Before and After subfolders exist so both can be used for this project
            mapping = _ensure_before_after_folders(mapping, client, settings)

        target_folder_id = mapping.before_folder_id if self.stage == "Before" else mapping.after_folder_id
        if not target_folder_id:
            frappe.throw("Target Drive subfolder not found (Before/After).")

        file_url = self.photo
        path = Path(get_file_path(file_url))
        filename = path.name
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        content_bytes = path.read_bytes()

        uploaded = client.upload_file(
            filename=filename,
            content_bytes=content_bytes,
            parent_id=target_folder_id,
            mime_type=mime_type,
        )
        self.google_drive_file_id = uploaded.get("id")
        self.google_drive_url = uploaded.get("webViewLink")
        self.uploaded_at = now_datetime()
        self.db_update()


__all__ = ["ProjectPhoto"]

