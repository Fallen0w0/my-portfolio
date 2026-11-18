"""The data models of the app. Each model class is one database table."""

from urllib.parse import urlparse

from .orm import DateTimeField, IntegerField, Model, TextField


class Project(Model):
    """One entry in the Projects section of the portfolio."""

    __tablename__ = "projects"

    STATUSES = ("Planned", "In progress", "Completed")

    id = IntegerField(primary_key=True)
    title = TextField(nullable=False)
    description = TextField(default="")
    tech_stack = TextField(default="")          # comma-separated, e.g. "Python, Flask"
    status = TextField(nullable=False, default="Planned")
    project_url = TextField(default="")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    @classmethod
    def clean(cls, data, require_title=False):
        """Validate input from the browser.

        Returns (cleaned, errors). Only the editable fields are copied, so a
        client cannot set id, created_at or updated_at.
        """
        cleaned, errors = {}, {}

        def read_text(name):
            """Return the stripped string for `name`, or None if it was not sent."""
            if name not in data:
                return None
            value = data[name]
            if value is None:
                return ""
            if not isinstance(value, str):
                errors[name] = "Must be text."
                return None
            return value.strip()

        title = read_text("title")
        if title is not None or require_title:
            if not title:
                errors["title"] = "Title is required."
            elif len(title) > 100:
                errors["title"] = "Title must be 100 characters or fewer."
            else:
                cleaned["title"] = title

        description = read_text("description")
        if description is not None and "description" not in errors:
            if len(description) > 500:
                errors["description"] = "Description must be 500 characters or fewer."
            else:
                cleaned["description"] = description

        tech_stack = read_text("tech_stack")
        if tech_stack is not None and "tech_stack" not in errors:
            tidy = ", ".join(p.strip() for p in tech_stack.split(",") if p.strip())
            if len(tidy) > 200:
                errors["tech_stack"] = "Tech stack must be 200 characters or fewer."
            else:
                cleaned["tech_stack"] = tidy

        status = read_text("status")
        if status is not None and "status" not in errors:
            if status not in cls.STATUSES:
                errors["status"] = "Status must be one of: " + ", ".join(cls.STATUSES) + "."
            else:
                cleaned["status"] = status

        url = read_text("project_url")
        if url is not None and "project_url" not in errors:
            if url and not cls._is_http_url(url):
                errors["project_url"] = "Enter a full link starting with http:// or https://"
            elif len(url) > 300:
                errors["project_url"] = "Link must be 300 characters or fewer."
            else:
                cleaned["project_url"] = url

        return cleaned, errors

    @staticmethod
    def _is_http_url(value):
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
