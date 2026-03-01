/**
 * Replace "Google Drive Integration" sidebar item icon with the Google Drive origin/logo image.
 * Runs after the workspace sidebar is rendered and when it updates.
 */
(function () {
	const WORKSPACE_TITLE = "Google Drive Integration";
	const ICON_IMAGE = "/assets/erpnext_google_drive_app/images/google-drive-origin-icon.png";

	function replace_sidebar_icons() {
		var sections = document.querySelectorAll(".desk-sidebar .standard-sidebar-section");
		sections.forEach(function (sidebar) {
			sidebar.querySelectorAll(".standard-sidebar-item").forEach(function (item) {
				var labelEl = item.querySelector(".sidebar-item-label");
				if (!labelEl) return;
				var label = labelEl.textContent.trim();
				if (label !== WORKSPACE_TITLE) return;

				var iconEl = item.querySelector(".sidebar-item-icon");
				if (!iconEl || iconEl.querySelector("img.sidebar-custom-icon")) return;

				var img = document.createElement("img");
				img.src = ICON_IMAGE;
				img.alt = WORKSPACE_TITLE;
				img.className = "sidebar-custom-icon";
				img.onerror = function () { img.src = "/assets/erpnext_google_drive_app/images/google-drive-logo.svg"; };
				iconEl.innerHTML = "";
				iconEl.appendChild(img);
			});
		});
	}

	function runWhenReady() {
		if (typeof frappe === "undefined") {
			setTimeout(runWhenReady, 100);
			return;
		}
		frappe.ready(function () {
			replace_sidebar_icons();
			setTimeout(replace_sidebar_icons, 300);
			setTimeout(replace_sidebar_icons, 1000);
			var deskSidebar = document.querySelector(".desk-sidebar");
			if (deskSidebar) {
				var observer = new MutationObserver(function () {
					replace_sidebar_icons();
				});
				observer.observe(deskSidebar, { childList: true, subtree: true });
			}
		});
	}

	// Ensure custom icon matches sidebar icon size
	var style = document.createElement("style");
	style.textContent = ".sidebar-custom-icon { width: 20px; height: 20px; object-fit: contain; display: block; }";
	document.head.appendChild(style);

	runWhenReady();
})();
