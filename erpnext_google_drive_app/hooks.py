from __future__ import annotations

app_name = "erpnext_google_drive_app"
app_title = "ERPNext Google Drive Integration"
app_publisher = "Your Name"
app_description = "Connect ERPNext to Google Drive and auto-store project photos (Before/After) in Drive folders."
app_email = "you@example.com"
app_license = "MIT"

# Add app to apps screen
add_to_apps_screen = [
    {
        "name": "erpnext_google_drive_app",
        "logo": "/assets/erpnext_google_drive_app/images/google-drive-logo.svg",
        "title": "Google Drive",
        "route": "/app/google-drive-integration",
    }
]

