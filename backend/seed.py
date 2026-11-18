"""Starter records for a new database."""

from .models import Project

STARTER_PROJECTS = [
    {
        "title": "Student Information System",
        "description": "A web application for managing student records.",
        "tech_stack": "React, Node.js, Express, MySQL, Prisma",
        "status": "Completed",
        "project_url": "https://github.com/Fallen0w0/student-information-system",
    },
    {
        "title": "Tic-Tac-Toe",
        "description": "A browser-based Tic-Tac-Toe game.",
        "tech_stack": "JavaScript, CSS, HTML",
        "status": "Completed",
        "project_url": "https://github.com/Fallen0w0/tic-tac-toe",
    },
    {
        "title": "Personal Portfolio Website",
        "description": "This site: a responsive landing page with a projects section "
                       "that reads from a database.",
        "tech_stack": "HTML, CSS, Bootstrap, JavaScript",
        "status": "In progress",
        "project_url": "https://github.com/Fallen0w0/my-portfolio",
    },
    {
        "title": "Projects Manager",
        "description": "The CRUD app on this page. A Flask API and an ORM layer "
                       "save every project in a SQLite database.",
        "tech_stack": "Python, Flask, SQLite, ORM",
        "status": "Completed",
        "project_url": "",
    },
]


def seed_projects():
    # Oldest first, so the newest record ends up on top of the list.
    for data in reversed(STARTER_PROJECTS):
        Project.create(**data)
