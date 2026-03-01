frappe.ui.form.on("Google Drive Settings", {
  refresh(frm) {
    // Connect to Google Drive (OAuth)
    if (frm.doc.client_id && frm.doc.redirect_uri) {
      frm.add_custom_button("Connect to Google Drive", () => {
        frappe.call({
          method: "erpnext_google_drive_app.google_drive_integration.api.get_google_auth_url",
          freeze: true,
          callback(r) {
            if (r.message && r.message.auth_url) {
              window.open(r.message.auth_url, "_blank");
              frappe.msgprint({
                title: __("OAuth Started"),
                message: __(
                  "A new window has opened. Please authorize in Google, then return here."
                ),
                indicator: "blue",
              });
            }
          },
        });
      });
    }

    // Test connection
    frm.add_custom_button("Test Connection", () => {
      frappe.call({
        method:
          "erpnext_google_drive_app.google_drive_integration.api.test_google_drive_connection",
        freeze: true,
        freeze_message: __("Testing Google Drive connection..."),
        callback(r) {
          if (!r.message) return;
          const ok = r.message.ok !== false;
          frappe.msgprint({
            title: __("Result"),
            message: r.message.message || __("Done"),
            indicator: ok ? "green" : "orange",
          });
        },
      });
    });
  },
});

