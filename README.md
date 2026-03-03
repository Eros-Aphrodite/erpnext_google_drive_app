### ERPNext Google Drive Integration

Connect ERPNext to Google Drive and automatically store project photos in Drive folders.

### Purpose

Use this app to **link ERPNext Projects to Google Drive**, optionally **auto-create a Drive folder per Project**, and **upload Before/After photos** so your project media stays organized outside ERPNext.

### What's included

- **Google Drive Settings** (Single): OAuth credentials, token storage, folder rules, automation toggles
- **Google Drive Project Folder**: stores the Drive folder created/linked per Project
- **Project Photo / Project Photo Item**: stores Before/After photos and the Drive file link after upload
- Client-side enhancement for **Project** to show Before/After photos

### Installation

Install via bench:

```bash
cd /path/to/frappe-bench
bench get-app $URL_OF_THIS_REPO
bench install-app erpnext_google_drive_app
bench migrate
bench clear-cache
```

### Configuration (high level)

- Create OAuth credentials in Google Cloud Console (Drive API)
- In ERPNext open **Google Drive Settings** and set:
  - **Client ID**, **Client Secret**, **Redirect URI**
  - Optional **Root Folder ID** (if you want all project folders under a parent folder)
  - Folder names for **Before** and **After**
  - Enable/disable **Auto-create Drive Folder per Project** and **Auto-upload Project Photos to Drive**

### Desk route

- App route: `/app/google-drive-integration`

