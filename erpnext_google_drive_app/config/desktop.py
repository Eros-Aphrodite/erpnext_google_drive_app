from __future__ import annotations


def get_data():
    return [
        {
            "label": "Integrations",
            "items": [
                {
                    "type": "doctype",
                    "name": "Google Drive Settings",
                    "label": "Google Drive Settings",
                    "description": "Connect to Google Drive and configure auto-folder & photo uploads.",
                    "icon": "octicon octicon-cloud-upload",
                },
                {
                    "type": "doctype",
                    "name": "Google Drive Project Folder",
                    "label": "Google Drive Project Folder",
                    "description": "Drive folder mapping per Project.",
                    "icon": "octicon octicon-file-directory",
                },
                {
                    "type": "doctype",
                    "name": "Project Photo",
                    "label": "Project Photo",
                    "description": "Before/After project photos uploaded to Google Drive.",
                    "icon": "octicon octicon-device-camera",
                },
            ],
        }
    ]

