from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class GoogleDriveProjectFolder(Document):
    def autoname(self):
        # Stable name per project
        self.name = self.project

    def before_save(self):
        self.last_checked_at = now_datetime()


def get_by_project(project: str) -> GoogleDriveProjectFolder | None:
    if frappe.db.exists("Google Drive Project Folder", project):
        return frappe.get_doc("Google Drive Project Folder", project)
    return None


__all__ = ["GoogleDriveProjectFolder", "get_by_project"]

