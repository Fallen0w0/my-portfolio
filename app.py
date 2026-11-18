"""Flask application: serves the portfolio page and the JSON API behind it.

Run it with:  python app.py   (then open http://127.0.0.1:5000)
"""

from flask import Flask, jsonify, render_template, request

import database
from models import Project
from seed import seed_projects


def init_db():
    """Create the table on first run and add the sample records once."""
    if Project.create_table():
        seed_projects()


def create_app(db_path=None):
    app = Flask(__name__)

    if db_path is not None:
        database.configure(db_path)
    init_db()

    # ---- Page ------------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html")

    # ---- API: the four CRUD operations -------------------------------------
    @app.get("/api/projects")
    def list_projects():
        """READ (many): optionally filtered with ?status=Completed"""
        status = request.args.get("status")
        if status:
            if status not in Project.STATUSES:
                return jsonify(error="Unknown status."), 400
            projects = Project.filter(order_by="-id", status=status)
        else:
            projects = Project.all(order_by="-id")
        return jsonify([p.to_dict() for p in projects])

    @app.get("/api/projects/<int:project_id>")
    def get_project(project_id):
        """READ (one)"""
        project = Project.get(project_id)
        if project is None:
            return jsonify(error="Project not found."), 404
        return jsonify(project.to_dict())

    @app.post("/api/projects")
    def create_project():
        """CREATE"""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send the project as a JSON object."), 400
        cleaned, errors = Project.clean(data, require_title=True)
        if errors:
            return jsonify(errors=errors), 400
        project = Project.create(**cleaned)
        return jsonify(project.to_dict()), 201

    @app.put("/api/projects/<int:project_id>")
    def update_project(project_id):
        """UPDATE: only the fields that are sent are changed."""
        project = Project.get(project_id)
        if project is None:
            return jsonify(error="Project not found."), 404
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send the project as a JSON object."), 400
        cleaned, errors = Project.clean(data)
        if errors:
            return jsonify(errors=errors), 400
        project.update(**cleaned)
        return jsonify(project.to_dict())

    @app.delete("/api/projects/<int:project_id>")
    def delete_project(project_id):
        """DELETE"""
        project = Project.get(project_id)
        if project is None:
            return jsonify(error="Project not found."), 404
        project.delete()
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run()
