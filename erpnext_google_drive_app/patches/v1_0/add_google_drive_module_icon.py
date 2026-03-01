import frappe


def ensure_module_def(module_name: str, app_name: str, icon: str) -> None:
    """Create or update a Module Def with the given icon."""
    if frappe.db.exists("Module Def", module_name):
        module_def = frappe.get_doc("Module Def", module_name)
        module_def.app_name = app_name
        module_def.icon = icon
        module_def.save(ignore_permissions=True)
        return

    module_def = frappe.get_doc(
        {
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name,
            "icon": icon,
        }
    )
    module_def.insert(ignore_permissions=True)


def execute():
    # Sidebar icon for the Google Drive Integration module
    ensure_module_def(
        module_name="Google Drive Integration",
        app_name="erpnext_google_drive_app",
        icon="integration",
    )

