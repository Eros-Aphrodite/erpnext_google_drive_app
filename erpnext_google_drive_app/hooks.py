from __future__ import annotations

app_name = "erpnext_google_drive_app"
app_title = "ERPNext Google Drive Integration"
app_publisher = "Your Name"
app_description = "Connect ERPNext to Google Drive and auto-store project photos (Before/After) in Drive folders."
app_email = "you@example.com"
app_license = "MIT"

# Extend Project form to show Before/After photos for the current project
doctype_js = {
    "Project": "public/js/project_photos.js",
}

app_include_js = ["assets/erpnext_google_drive_app/js/sidebar_icon.js"]

# Add app to apps screen
add_to_apps_screen = [
    {
        "name": "erpnext_google_drive_app",
        "logo": "/assets/erpnext_google_drive_app/images/google-drive-origin-icon.png",
        "title": "Google Drive",
        "route": "/app/google-drive-integration",
    }
]

