"""Page and task routes for the Trello-style application."""

from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .database import get_db_connection

main = Blueprint("main", __name__)
STATUSES = ("To Do", "In Progress", "Completed")
PRIORITIES = ("Low", "Medium", "High")


def db():
    return get_db_connection(current_app.config["DATABASE_PATH"])


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with db() as connection:
        return connection.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "info")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def owned_board(board_id):
    user = current_user()
    with db() as connection:
        board = connection.execute(
            "SELECT * FROM boards WHERE id = ? AND user_id = ?", (board_id, user["id"])
        ).fetchone()
    if board is None:
        abort(404)
    return board


@main.get("/")
def index():
    if current_user():
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main.get("/health")
def health():
    return {"status": "ok"}


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or len(name) > 80 or "@" not in email or len(email) > 254 or len(password) < 8:
            flash("Enter a name, valid email, and password with at least 8 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            try:
                with db() as connection:
                    connection.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    user_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
                session.clear()
                session["user_id"] = user_id
                session["user_name"] = name
                flash("Your account is ready. Welcome aboard!", "success")
                return redirect(url_for("main.dashboard"))
            except Exception as error:
                if "UNIQUE" in str(error):
                    flash("An account with that email already exists.", "error")
                else:
                    raise
    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db() as connection:
            user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            destination = request.args.get("next", "")
            if destination.startswith("/") and not destination.startswith("//"):
                return redirect(destination)
            return redirect(url_for("main.dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@main.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@main.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    today = date.today().isoformat()
    with db() as connection:
        boards = connection.execute("SELECT COUNT(*) FROM boards WHERE user_id = ?", (user["id"],)).fetchone()[0]
        total = connection.execute(
            "SELECT COUNT(*) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=?", (user["id"],)
        ).fetchone()[0]
        completed = connection.execute(
            "SELECT COUNT(*) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? AND t.status='Completed'", (user["id"],)
        ).fetchone()[0]
        overdue = connection.execute(
            "SELECT COUNT(*) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? AND t.status!='Completed' AND t.due_date < ?", (user["id"], today)
        ).fetchone()[0]
        recent = connection.execute(
            "SELECT t.*, b.title AS board_title FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? ORDER BY t.created_at DESC LIMIT 6", (user["id"],)
        ).fetchall()
        status_counts = [connection.execute(
            "SELECT COUNT(*) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? AND t.status=?", (user["id"], status)
        ).fetchone()[0] for status in STATUSES]
    return render_template("dashboard.html", user=user, boards=boards, total=total, completed=completed,
                           pending=total-completed, overdue=overdue, recent=recent,
                           completion=round(completed * 100 / total) if total else 0,
                           statuses=STATUSES, status_counts=status_counts)


@main.route("/boards", methods=["GET", "POST"])
@login_required
def boards():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or len(title) > 100:
            flash("Board name is required and must be under 100 characters.", "error")
        else:
            with db() as connection:
                connection.execute("INSERT INTO boards (user_id, title, description) VALUES (?, ?, ?)",
                                   (user["id"], title, description[:500]))
            flash("Board created.", "success")
            return redirect(url_for("main.boards"))
    with db() as connection:
        all_boards = connection.execute(
            "SELECT b.*, COUNT(t.id) AS task_count FROM boards b LEFT JOIN tasks t ON t.board_id=b.id WHERE b.user_id=? GROUP BY b.id ORDER BY b.created_at DESC",
            (user["id"],),
        ).fetchall()
    return render_template("boards.html", boards=all_boards)


@main.post("/boards/<int:board_id>/delete")
@login_required
def delete_board(board_id):
    board = owned_board(board_id)
    with db() as connection:
        connection.execute("DELETE FROM boards WHERE id=?", (board["id"],))
    flash("Board and its tasks deleted.", "success")
    return redirect(url_for("main.boards"))


@main.post("/boards/<int:board_id>/edit")
@login_required
def edit_board(board_id):
    board = owned_board(board_id)
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    if not title or len(title) > 100:
        flash("Board name is required and must be under 100 characters.", "error")
    else:
        with db() as connection:
            connection.execute("UPDATE boards SET title=?, description=? WHERE id=?",
                               (title, description[:500], board["id"]))
        flash("Board details updated.", "success")
    return redirect(url_for("main.board_detail", board_id=board_id))


@main.route("/boards/<int:board_id>", methods=["GET", "POST"])
@login_required
def board_detail(board_id):
    board = owned_board(board_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "") or None
        priority = request.form.get("priority", "Medium")
        complexity = request.form.get("complexity", "3")
        try:
            hours = float(request.form.get("estimated_hours", "1"))
            complexity_value = int(complexity)
            if not title or len(title) > 160 or priority not in PRIORITIES or not 1 <= complexity_value <= 5 or hours < 0:
                raise ValueError
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            flash("Check the task title, priority, complexity, hours, and due date.", "error")
        else:
            with db() as connection:
                connection.execute(
                    "INSERT INTO tasks (board_id,title,description,assigned_user_id,priority,status,complexity,estimated_hours,due_date) VALUES (?,?,?,?,?,'To Do',?,?,?)",
                    (board_id, title, description[:2000], current_user()["id"], priority, complexity_value, hours, due_date),
                )
            flash("Task added to To Do.", "success")
            return redirect(url_for("main.board_detail", board_id=board_id))
    with db() as connection:
        tasks = connection.execute("SELECT * FROM tasks WHERE board_id=? ORDER BY created_at DESC", (board_id,)).fetchall()
    return render_template("board.html", board=board, tasks=tasks, statuses=STATUSES)


@main.post("/tasks/<int:task_id>/update")
@login_required
def update_task(task_id):
    with db() as connection:
        task = connection.execute("SELECT t.* FROM tasks t JOIN boards b ON b.id=t.board_id WHERE t.id=? AND b.user_id=?",
                                  (task_id, current_user()["id"])).fetchone()
        if task is None:
            abort(404)
        status = request.form.get("status", task["status"])
        if status not in STATUSES:
            abort(400)
        connection.execute("UPDATE tasks SET status=?, completed_at=CASE WHEN ?='Completed' THEN CURRENT_TIMESTAMP ELSE NULL END WHERE id=?",
                           (status, status, task_id))
        if status != task["status"]:
            connection.execute("INSERT INTO task_history(task_id,previous_status,new_status) VALUES(?,?,?)",
                               (task_id, task["status"], status))
    flash("Task status updated.", "success")
    return redirect(url_for("main.board_detail", board_id=task["board_id"]))


@main.post("/tasks/<int:task_id>/edit")
@login_required
def edit_task(task_id):
    with db() as connection:
        task = connection.execute("SELECT t.* FROM tasks t JOIN boards b ON b.id=t.board_id WHERE t.id=? AND b.user_id=?",
                                  (task_id, current_user()["id"])).fetchone()
        if task is None:
            abort(404)
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date = request.form.get("due_date", "") or None
        try:
            hours = float(request.form.get("estimated_hours", "1"))
            complexity = int(request.form.get("complexity", "3"))
            if not title or len(title) > 160 or priority not in PRIORITIES or not 1 <= complexity <= 5 or hours < 0:
                raise ValueError
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            flash("Check the task title, priority, complexity, hours, and due date.", "error")
        else:
            connection.execute(
                "UPDATE tasks SET title=?,description=?,priority=?,estimated_hours=?,complexity=?,due_date=? WHERE id=?",
                (title, description[:2000], priority, hours, complexity, due_date, task_id),
            )
            flash("Task details updated.", "success")
    return redirect(url_for("main.board_detail", board_id=task["board_id"]))


@main.post("/tasks/<int:task_id>/delete")
@login_required
def delete_task(task_id):
    with db() as connection:
        task = connection.execute("SELECT t.id,t.board_id FROM tasks t JOIN boards b ON b.id=t.board_id WHERE t.id=? AND b.user_id=?",
                                  (task_id, current_user()["id"])).fetchone()
        if task is None:
            abort(404)
        connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    flash("Task deleted.", "success")
    return redirect(url_for("main.board_detail", board_id=task["board_id"]))


@main.get("/analytics")
@login_required
def analytics():
    user = current_user()
    with db() as connection:
        counts = [connection.execute("SELECT COUNT(*) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? AND t.status=?",
                                     (user["id"], status)).fetchone()[0] for status in STATUSES]
        hours = connection.execute("SELECT COALESCE(SUM(t.estimated_hours),0) FROM tasks t JOIN boards b ON b.id=t.board_id WHERE b.user_id=? AND t.status!='Completed'",
                                   (user["id"],)).fetchone()[0]
    return render_template("analytics.html", statuses=STATUSES, status_counts=counts, open_hours=hours,
                           completion=round(counts[2] * 100 / sum(counts)) if sum(counts) else 0)


@main.get("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user())


@main.post("/profile/edit")
@login_required
def edit_profile():
    user = current_user()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not name or len(name) > 80 or "@" not in email or len(email) > 254:
        flash("Enter a name and valid email address.", "error")
    else:
        try:
            with db() as connection:
                connection.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, user["id"]))
            session["user_name"] = name
            flash("Profile updated.", "success")
        except Exception as error:
            if "UNIQUE" in str(error):
                flash("That email address is already in use.", "error")
            else:
                raise
    return redirect(url_for("main.profile"))
