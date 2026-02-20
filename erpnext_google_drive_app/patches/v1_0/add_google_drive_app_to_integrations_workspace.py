"""
Add Google Drive (Project Photos) app links to Integrations workspace.
"""
import frappe


def execute():
	"""Add Google Drive Settings, Google Drive Project Folder, Project Photo to Integrations workspace."""
	if not frappe.db.exists("Workspace", "Integrations"):
		return

	workspace = frappe.get_doc("Workspace", "Integrations")

	# Skip if our links already exist
	if any(link.link_to == "Google Drive Settings" for link in workspace.links):
		return

	last_idx = max([link.idx for link in workspace.links], default=0)

	# Card break for this app
	card_exists = any(
		link.label == "Google Drive (Project Photos)" and link.type == "Card Break"
		for link in workspace.links
	)
	if not card_exists:
		workspace.append("links", {
			"label": "Google Drive (Project Photos)",
			"type": "Card Break",
			"link_count": 3,
			"idx": last_idx + 1,
		})
		last_idx += 1

	for label, link_to in [
		("Google Drive Settings", "Google Drive Settings"),
		("Google Drive Project Folder", "Google Drive Project Folder"),
		("Project Photo", "Project Photo"),
	]:
		workspace.append("links", {
			"label": label,
			"type": "Link",
			"link_type": "DocType",
			"link_to": link_to,
			"idx": last_idx + 1,
		})
		last_idx += 1

	workspace.save(ignore_permissions=True)
	frappe.db.commit()
