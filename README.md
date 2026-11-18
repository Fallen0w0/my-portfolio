# Personal Portfolio and Projects Manager

A Flask portfolio site with a Projects section backed by SQLite. Add a project, view saved projects, edit them, or delete them. Changes remain saved after you refresh or restart the app.

## Run the app

You need Python 3.10 or newer.

1. Open a terminal in this project folder.
2. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install Flask and start the site:

   ```sh
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Visit <http://127.0.0.1:5000>.

Keep the terminal open while using the site. Press **Ctrl+C** to stop the server. Do not open `templates/index.html` directly; the page needs Flask to load projects and save changes.

## Use the Projects section

- **Add:** choose **+ Add project**, fill in the form, and save.
- **View:** browse the project cards or filter by status.
- **Edit:** choose **Edit** on a card, update the details, and save.
- **Delete:** choose **Delete** on a card and confirm.

The app validates project details and stores them in SQLite. Its ORM maps project rows to Python `Project` objects and performs the database operations.

## Database

SQLite is included with Python; no separate database server is needed. By default, the app creates `data/portfolio.db` the first time it runs. It creates the projects table automatically and adds starter projects once.

To use a different database file, set `DATABASE_PATH` before starting the app:

```powershell
# Windows PowerShell
$env:DATABASE_PATH = "C:\path\to\portfolio.db"
python app.py
```

```sh
# macOS / Linux
DATABASE_PATH=/path/to/portfolio.db python app.py
```

To reset the local database, stop the app and delete `data/portfolio.db`. The next run creates a fresh database with the starter projects. The database file is excluded from Git by `.gitignore`.

## Project layout

```text
my-portfolio/
├── app.py                  # Starts Flask and defines the projects API
├── database.py             # SQLite connection and database path
├── models.py               # Project fields and input validation
├── orm.py                  # ORM operations for database records
├── seed.py                 # Starter projects for a new database
├── requirements.txt        # Python packages needed to run the app
├── README.md               # Setup and project instructions
├── data/
│   └── portfolio.db        # Created on first run; excluded from Git
├── templates/
│   └── index.html          # Portfolio page
├── static/
│   ├── css/style.css
│   ├── images/profile.jpg
│   └── js/
│       ├── contact.js
│       └── projects.js
└── tests/
    └── test_crud.py        # ORM, API, and persistence tests
```

Keep application code in the root Python modules, page markup in `templates/`, browser assets in `static/`, and tests in `tests/`. The `data/` folder is created automatically when the app first runs.

## Technologies

- Python and Flask
- SQLite and a small project ORM built on Python's `sqlite3`
- HTML, CSS, Bootstrap, and JavaScript
- `unittest` for tests

## Run the tests

```sh
python -m unittest discover -s tests -v
```

Tests use a temporary database, so they do not change your saved projects.

## Notes

- The contact form opens your email app with the message ready to review and send. It does not send or store messages on the server.
- Project management has no login. Keep the write API private, or add authentication before hosting the site publicly.
- Fonts, Bootstrap, and icons load from external CDNs, so an internet connection is needed for those assets.
