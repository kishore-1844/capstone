# AI-Powered Trello Task Management System

A beginner-friendly Flask and SQLite capstone project for task tracking, deadline estimates, workload analysis, and project analytics.

## Current phase

The current working slice includes the Flask application, responsive frontend, registration and login, SQLite-backed boards and Kanban tasks, a dashboard, analytics, and account profile. The database is created automatically when the app starts. Local machine-learning predictions and team collaboration are planned for later phases.

## Requirements

- Python 3.10 or newer
- VS Code (recommended)

## Run locally

Open a terminal in the project folder and create a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

If PowerShell blocks environment activation, use Command Prompt with `.venv\Scripts\activate.bat`, or call `.venv\Scripts\python.exe` directly.

Open `http://127.0.0.1:5000/` to use the app. Register an account, create a board, then add and move tasks between the three Kanban columns. `http://127.0.0.1:5000/health` is a simple health check. The SQLite database is created at `instance/trello.db` on startup.

Set `TRELLO_SECRET_KEY` to a private random value before using the app beyond local development. `TRELLO_DATABASE_PATH` can optionally point to a different SQLite file.

## Database

The schema includes users, boards, board members, tasks, and task history. Foreign key checks and indexes are enabled. The database file is generated automatically; there is no manual database setup step.
