// Projects section: talks to the Flask API (/api/projects) with fetch().
// Create = POST, Read = GET, Update = PUT, Delete = DELETE.

(() => {
	"use strict";

	const API_URL = "/api/projects";
	const STATUS_CLASS = {
		"Planned": "status-planned",
		"In progress": "status-progress",
		"Completed": "status-completed",
	};

	const grid = document.getElementById("project-grid");
	const loading = document.getElementById("loading");
	const emptyMessage = document.getElementById("empty");
	const pageAlert = document.getElementById("page-alert");
	const liveStatus = document.getElementById("live-status");
	const dialog = document.getElementById("project-dialog");
	const form = document.getElementById("project-form");
	const formAlert = document.getElementById("form-alert");
	const dialogTitle = document.getElementById("dialog-title");
	const saveButton = document.getElementById("save-project");
	const filterButtons = document.querySelectorAll(".filter-btn");

	let currentFilter = "All";
	let editingId = null; // null = the form is adding a new project

	// ---- helpers -----------------------------------------------------------

	class ApiError extends Error {
		constructor(message, fieldErrors = {}) {
			super(message);
			this.fieldErrors = fieldErrors;
		}
	}

	// Talk to the API. Throws ApiError with a readable message when something fails.
	async function api(path = "", options = {}) {
		let response;
		try {
			response = await fetch(API_URL + path, {
				headers: { "Content-Type": "application/json" },
				...options,
			});
		} catch (error) {
			throw new ApiError(
				"Cannot reach the server. Make sure run.py is running, then open this page at http://127.0.0.1:5000"
			);
		}
		if (response.status === 204) return null;

		const data = await response.json().catch(() => ({}));
		if (!response.ok) {
			throw new ApiError(data.error || "Please fix the highlighted fields.", data.errors || {});
		}
		return data;
	}

	// Build an element. Text is added as text (never as HTML), so anything a
	// visitor types into the form is displayed safely.
	function el(tag, props = {}, ...children) {
		const node = document.createElement(tag);
		for (const [key, value] of Object.entries(props)) {
			if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
			else node.setAttribute(key, value);
		}
		node.append(...children.filter((child) => child != null && child !== false));
		return node;
	}

	function announce(message) {
		liveStatus.textContent = "";
		// A short delay makes screen readers announce repeated messages.
		setTimeout(() => (liveStatus.textContent = message), 50);
	}

	function showAlert(box, message) {
		box.textContent = message;
		box.hidden = !message;
	}

	function formatDate(iso) {
		const date = new Date(iso);
		if (Number.isNaN(date.getTime())) return "";
		return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
	}

	// ---- READ: load and draw the list ---------------------------------------

	async function loadProjects() {
		const query = currentFilter === "All" ? "" : `?status=${encodeURIComponent(currentFilter)}`;
		try {
			const projects = await api(query);
			showAlert(pageAlert, "");
			render(projects);
		} catch (error) {
			grid.replaceChildren();
			loading.hidden = true;
			emptyMessage.hidden = true;
			showAlert(pageAlert, error.message);
		}
	}

	function render(projects) {
		loading.hidden = true;
		emptyMessage.hidden = projects.length > 0;
		grid.replaceChildren(...projects.map(renderCard));
	}

	function renderCard(project) {
		const technologies = project.tech_stack
			.split(",")
			.map((item) => item.trim())
			.filter(Boolean);

		return el("article", { class: "project-card" },
			el("div", { class: "project-card-top" },
				el("h3", {}, project.title),
				el("span", { class: `status-badge ${STATUS_CLASS[project.status] || ""}` }, project.status)
			),
			project.description && el("p", { class: "project-desc" }, project.description),
			technologies.length > 0 && el("ul", { class: "tech-list", "aria-label": "Technologies used" },
				...technologies.map((tech) => el("li", {}, tech))
			),
			el("div", { class: "project-card-foot" },
				el("div", { class: "project-meta" },
					project.project_url && el("a", {
						href: project.project_url, target: "_blank", rel: "noopener noreferrer",
					}, "View project ↗"),
					el("span", {}, `Added ${formatDate(project.created_at)}`)
				),
				el("div", { class: "project-actions" },
					el("button", {
						type: "button", class: "btn btn-sm btn-outline-primary btn-pill",
						"aria-label": `Edit ${project.title}`, onclick: () => openEditForm(project.id),
					}, "Edit"),
					el("button", {
						type: "button", class: "btn btn-sm btn-outline-danger btn-pill",
						"aria-label": `Delete ${project.title}`, onclick: () => deleteProject(project),
					}, "Delete")
				)
			)
		);
	}

	// ---- the add / edit form ------------------------------------------------

	function clearFieldErrors() {
		showAlert(formAlert, "");
		form.querySelectorAll(".is-invalid").forEach((input) => {
			input.classList.remove("is-invalid");
			input.removeAttribute("aria-invalid");
		});
	}

	function showFieldErrors(fieldErrors) {
		for (const [name, message] of Object.entries(fieldErrors)) {
			const input = form.elements[name];
			const box = document.getElementById(`error-${name}`);
			if (!input || !box) continue;
			input.classList.add("is-invalid");
			input.setAttribute("aria-invalid", "true");
			box.textContent = message;
		}
		const firstInvalid = form.querySelector(".is-invalid");
		if (firstInvalid) firstInvalid.focus();
	}

	function openAddForm() {
		editingId = null;
		form.reset();
		clearFieldErrors();
		dialogTitle.textContent = "Add project";
		saveButton.textContent = "Save project";
		dialog.showModal();
		form.elements.title.focus();
	}

	async function openEditForm(id) {
		try {
			// READ (one): fetch the latest copy of this row before editing it.
			const project = await api(`/${id}`);
			editingId = project.id;
			form.reset();
			clearFieldErrors();
			for (const name of ["title", "status", "tech_stack", "project_url", "description"]) {
				form.elements[name].value = project[name];
			}
			dialogTitle.textContent = "Edit project";
			saveButton.textContent = "Save changes";
			dialog.showModal();
			form.elements.title.focus();
		} catch (error) {
			showAlert(pageAlert, error.message);
			loadProjects(); // the row may have been deleted elsewhere, so refresh
		}
	}

	// ---- CREATE / UPDATE ------------------------------------------------------

	form.addEventListener("submit", async (event) => {
		event.preventDefault();
		clearFieldErrors();

		const payload = Object.fromEntries(new FormData(form));
		const isEditing = editingId !== null;
		saveButton.disabled = true;

		try {
			await api(isEditing ? `/${editingId}` : "", {
				method: isEditing ? "PUT" : "POST",
				body: JSON.stringify(payload),
			});
			dialog.close();
			announce(isEditing ? "Project updated." : "Project added.");
			await loadProjects();
		} catch (error) {
			if (Object.keys(error.fieldErrors).length > 0) showFieldErrors(error.fieldErrors);
			else showAlert(formAlert, error.message);
		} finally {
			saveButton.disabled = false;
		}
	});

	document.getElementById("cancel-dialog").addEventListener("click", () => dialog.close());
	document.getElementById("add-project").addEventListener("click", openAddForm);

	// ---- DELETE -------------------------------------------------------------

	async function deleteProject(project) {
		if (!confirm(`Delete "${project.title}"? This cannot be undone.`)) return;
		try {
			await api(`/${project.id}`, { method: "DELETE" });
			announce("Project deleted.");
		} catch (error) {
			showAlert(pageAlert, error.message);
		}
		await loadProjects();
	}

	// ---- filter buttons -------------------------------------------------------

	filterButtons.forEach((button) => {
		button.addEventListener("click", () => {
			currentFilter = button.dataset.filter;
			filterButtons.forEach((other) => {
				const active = other === button;
				other.classList.toggle("active", active);
				other.setAttribute("aria-pressed", String(active));
			});
			loadProjects();
		});
	});

	loadProjects();
})();
