// Opens the contact form and hands the completed message to the visitor's email app.

(() => {
	"use strict";

	const dialog = document.getElementById("contact-dialog");
	const form = document.getElementById("contact-form");

	document.querySelectorAll("[data-open-contact]").forEach((button) => {
		button.addEventListener("click", (event) => {
			event.preventDefault();
			dialog.showModal();
			form.elements.name.focus();
		});
	});

	document.querySelector("[data-close-contact]").addEventListener("click", () => dialog.close());

	form.addEventListener("submit", (event) => {
		event.preventDefault();

		const { name, email, subject, message } = Object.fromEntries(new FormData(form));
		const body = `From: ${name}\nEmail: ${email}\n\n${message}`;
		const mailto = `mailto:charleszedrickdelmundo22@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

		dialog.close();
		window.location.href = mailto;
	});
})();
