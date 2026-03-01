frappe.ui.form.on("Project", {
	onload: function (frm) {
		if (!frm.dashboard) return;
		// Section will be refreshed when doc is loaded
		frm.trigger("render_project_photos_section");
	},
	refresh: function (frm) {
		frm.trigger("render_project_photos_section");
	},
	render_project_photos_section: function (frm) {
		if (!frm.dashboard || !frm.doc.name) return;

		// Remove previous section so we don't duplicate on refresh
		$(frm.dashboard.parent).find(".project-photos-dashboard-section").remove();

		frappe.db
			.get_list("Project Photo", {
				filters: { project: frm.doc.name },
				fields: ["name", "stage", "photo", "google_drive_url", "uploaded_at"],
				order_by: "stage asc, modified desc",
			})
			.then((photos) => {
				const before = photos.filter((p) => p.stage === "Before");
				const after = photos.filter((p) => p.stage === "After");

				const row = (p) => {
					const link = p.google_drive_url
						? `<a href="${p.google_drive_url}" target="_blank" class="text-muted small">${__("Open in Drive")}</a>`
						: "";
					const img = p.photo
						? `<img src="${p.photo}" class="project-photo-thumb" style="max-width: 120px; max-height: 80px; object-fit: cover; border-radius: 4px;" />`
						: "";
					return `<div class="project-photo-item mb-3">
						<div>${img}</div>
						<div class="small mt-1">
							<a href="/app/project-photo/${p.name}">${p.name}</a>
							${link ? " · " + link : ""}
						</div>
					</div>`;
				};

				let html = "";
				html += `<div class="row">`;
				html += `<div class="col-md-6"><h6 class="text-uppercase text-muted small">${__("Before")}</h6>`;
				if (before.length) {
					before.forEach((p) => (html += row(p)));
				} else {
					html += `<p class="text-muted small">${__("No before photos")}</p>`;
				}
				html += `</div>`;
				html += `<div class="col-md-6"><h6 class="text-uppercase text-muted small">${__("After")}</h6>`;
				if (after.length) {
					after.forEach((p) => (html += row(p)));
				} else {
					html += `<p class="text-muted small">${__("No after photos")}</p>`;
				}
				html += `</div>`;
				html += `</div>`;
				html += `<div class="mt-2"><a href="/app/project-photo?project=${encodeURIComponent(frm.doc.name)}" class="btn btn-sm btn-default">${__("Add / view all Project Photos")}</a></div>`;

				const body = frm.dashboard.add_section(html, __("Project Photos"));
				if (body && body.length) body.closest(".form-dashboard-section").addClass("project-photos-dashboard-section");
			})
			.catch(() => {
				// No permission or doctype not found
			});
	},
});
