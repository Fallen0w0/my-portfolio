"""Tests for the ORM layer and the CRUD API.

Run from the project folder with:  python -m unittest -v
Each test uses its own temporary database file, so your real data is untouched.
"""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from models import Project


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.app = create_app(db_path=self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()


class OrmTests(BaseTest):
    def test_create_assigns_id_and_timestamps(self):
        project = Project.create(title="ORM test")
        self.assertIsNotNone(project.id)
        self.assertEqual(project.status, "Planned")  # default value
        self.assertTrue(project.created_at)
        self.assertTrue(project.updated_at)

    def test_get_returns_saved_row_or_none(self):
        project = Project.create(title="Find me", tech_stack="Python")
        found = Project.get(project.id)
        self.assertEqual(found.title, "Find me")
        self.assertEqual(found.tech_stack, "Python")
        self.assertIsNone(Project.get(99999))

    def test_save_updates_existing_row(self):
        project = Project.create(title="Before")
        project.title = "After"
        project.save()
        self.assertEqual(Project.get(project.id).title, "After")

    def test_delete_removes_row(self):
        project = Project.create(title="Temporary")
        project.delete()
        self.assertIsNone(Project.get(project.id))

    def test_filter_and_ordering(self):
        a = Project.create(title="A", status="Completed")
        b = Project.create(title="B", status="Completed")
        Project.create(title="C", status="Planned")
        completed = Project.filter(order_by="-id", status="Completed")
        ids = [p.id for p in completed]
        # (the seeded sample data contains one "Completed" project too)
        self.assertTrue(all(p.status == "Completed" for p in completed))
        self.assertEqual(ids[:2], [b.id, a.id])
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(ValueError):
            Project.filter(nope="x")
        with self.assertRaises(ValueError):
            Project.all(order_by="title; DROP TABLE projects")
        with self.assertRaises(TypeError):
            Project(nope="x")

    def test_values_are_not_treated_as_sql(self):
        nasty = "x'); DROP TABLE projects; --"
        project = Project.create(title=nasty)
        self.assertEqual(Project.get(project.id).title, nasty)
        self.assertTrue(Project.table_exists())


class ApiTests(BaseTest):
    def test_first_run_adds_portfolio_projects(self):
        response = self.client.get("/api/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.get_json()
        self.assertEqual(len(projects), 4)
        self.assertEqual(
            {project["project_url"] for project in projects if project["project_url"]},
            {
                "https://github.com/Fallen0w0/student-information-system",
                "https://github.com/Fallen0w0/tic-tac-toe",
                "https://github.com/Fallen0w0/my-portfolio",
            },
        )

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Charles Zedrick Del Mundo", response.data)

    def test_create_project(self):
        response = self.client.post("/api/projects", json={
            "title": "  New idea  ",
            "description": "Something fun",
            "tech_stack": "Python ,  Flask,, SQLite",
            "status": "In progress",
            "project_url": "https://example.com",
        })
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["title"], "New idea")
        self.assertEqual(body["tech_stack"], "Python, Flask, SQLite")
        self.assertEqual(Project.get(body["id"]).status, "In progress")

    def test_create_requires_title(self):
        response = self.client.post("/api/projects", json={"description": "no title"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.get_json()["errors"])

    def test_create_rejects_bad_values(self):
        response = self.client.post("/api/projects", json={
            "title": "x" * 101,
            "status": "Maybe",
            "project_url": "javascript:alert(1)",
            "description": 123,
        })
        self.assertEqual(response.status_code, 400)
        errors = response.get_json()["errors"]
        for field in ("title", "status", "project_url", "description"):
            self.assertIn(field, errors)

    def test_create_rejects_non_json_body(self):
        response = self.client.post("/api/projects", data="hello")
        self.assertEqual(response.status_code, 400)

    def test_client_cannot_set_id_or_timestamps(self):
        response = self.client.post("/api/projects", json={
            "title": "Sneaky", "id": 9999, "created_at": "2000-01-01T00:00:00+00:00",
        })
        body = response.get_json()
        self.assertNotEqual(body["id"], 9999)
        self.assertNotEqual(body["created_at"], "2000-01-01T00:00:00+00:00")

    def test_read_one_and_not_found(self):
        created = self.client.post("/api/projects", json={"title": "Readable"}).get_json()
        found = self.client.get(f"/api/projects/{created['id']}")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.get_json()["title"], "Readable")
        self.assertEqual(self.client.get("/api/projects/99999").status_code, 404)

    def test_update_changes_only_sent_fields(self):
        created = self.client.post("/api/projects", json={
            "title": "Original", "description": "Keep me", "status": "Planned",
        }).get_json()
        response = self.client.put(f"/api/projects/{created['id']}", json={
            "title": "Renamed", "status": "Completed",
        })
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["title"], "Renamed")
        self.assertEqual(body["status"], "Completed")
        self.assertEqual(body["description"], "Keep me")

    def test_update_validates_and_handles_missing(self):
        created = self.client.post("/api/projects", json={"title": "Valid"}).get_json()
        bad = self.client.put(f"/api/projects/{created['id']}", json={"title": "   "})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(Project.get(created["id"]).title, "Valid")
        self.assertEqual(self.client.put("/api/projects/99999", json={"title": "x"}).status_code, 404)

    def test_delete_project(self):
        created = self.client.post("/api/projects", json={"title": "Bye"}).get_json()
        response = self.client.delete(f"/api/projects/{created['id']}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(f"/api/projects/{created['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/projects/{created['id']}").status_code, 404)

    def test_filter_by_status(self):
        response = self.client.get("/api/projects?status=Completed")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(p["status"] == "Completed" for p in response.get_json()))
        self.assertEqual(self.client.get("/api/projects?status=Nope").status_code, 400)

    def test_data_persists_after_restart(self):
        created = self.client.post("/api/projects", json={"title": "Still here"}).get_json()
        # "Restart": build a brand-new app on the same database file.
        restarted = create_app(db_path=self.db_path).test_client()
        found = restarted.get(f"/api/projects/{created['id']}")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.get_json()["title"], "Still here")

    def test_deleted_samples_do_not_come_back_after_restart(self):
        for project in self.client.get("/api/projects").get_json():
            self.client.delete(f"/api/projects/{project['id']}")
        restarted = create_app(db_path=self.db_path).test_client()
        self.assertEqual(restarted.get("/api/projects").get_json(), [])


if __name__ == "__main__":
    unittest.main()
