from datetime import date, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from models import Habit, HabitLog, User, db


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


QUOTES = [
    "Consistency turns ordinary days into extraordinary results.",
    "Small habits orbit big dreams.",
    "Win today. Let the streak speak tomorrow.",
    "Discipline is choosing your future one checkbox at a time.",
]

DEFAULT_HABITS = [
    ("Study", 2, "hours", "#58d6ff"),
    ("Gym", 1, "session", "#ff9f43"),
    ("Sleep", 8, "hours", "#a78bfa"),
    ("Coding", 1, "hour", "#2ee59d"),
    ("Learn English", 30, "minutes", "#ff6b9a"),
]


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])


def get_or_create_today_log(user_id, habit):
    today = date.today()
    log = HabitLog.query.filter_by(user_id=user_id, habit_id=habit.id, log_date=today).first()
    if log is None:
        log = HabitLog(user_id=user_id, habit_id=habit.id, log_date=today)
        db.session.add(log)
    return log


def day_score(user_id, selected_date):
    habits = Habit.query.filter_by(user_id=user_id, active=True).all()
    if not habits:
        return 0
    completed = HabitLog.query.filter_by(user_id=user_id, log_date=selected_date, completed=True).count()
    return round((completed / len(habits)) * 100)


def streak_for(user_id, max_days=365):
    streak = 0
    cursor = date.today()
    for _ in range(max_days):
        score = day_score(user_id, cursor)
        if score < 100:
            break
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def best_streak(user_id, days=365):
    best = 0
    running = 0
    start = date.today() - timedelta(days=days - 1)
    for index in range(days):
        cursor = start + timedelta(days=index)
        if day_score(user_id, cursor) == 100:
            running += 1
            best = max(best, running)
        else:
            running = 0
    return best


def score_series(user_id, days):
    start = date.today() - timedelta(days=days - 1)
    labels = []
    scores = []
    for index in range(days):
        cursor = start + timedelta(days=index)
        labels.append(cursor.strftime("%d %b"))
        scores.append(day_score(user_id, cursor))
    return labels, scores


@app.before_request
def create_tables():
    db.create_all()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please log in.", "error")
            return redirect(url_for("login"))

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        for habit_name, target, unit, color in DEFAULT_HABITS:
            db.session.add(Habit(user_id=user.id, name=habit_name, target=target, unit=unit, color=color))
        db.session.commit()
        session["user_id"] = user.id
        flash("Welcome to Achievo Trackr. Your first streak starts today.", "success")
        return redirect(url_for("dashboard"))
    return render_template("signup.html", quote=QUOTES[0])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html", quote=QUOTES[1])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()
    habits = Habit.query.filter_by(user_id=user.id, active=True).all()

    if request.method == "POST":
        old_score = day_score(user.id, date.today())
        completed_count = 0
        for habit in habits:
            log = get_or_create_today_log(user.id, habit)
            progress = int(request.form.get(f"progress_{habit.id}", 0) or 0)
            log.progress = max(progress, 0)
            log.completed = log.progress >= habit.target
            if log.completed:
                completed_count += 1

        today_score = round((completed_count / len(habits)) * 100) if habits else 0
        user.points = max(user.points + today_score - old_score, 0)
        db.session.commit()
        flash(f"Today score saved: {today_score}/100. Points updated!", "success")
        return redirect(url_for("dashboard"))

    logs = {log.habit_id: log for log in HabitLog.query.filter_by(user_id=user.id, log_date=date.today()).all()}
    labels7, scores7 = score_series(user.id, 7)
    labels30, scores30 = score_series(user.id, 30)
    today_score = day_score(user.id, date.today())

    return render_template(
        "dashboard.html",
        user=user,
        habits=habits,
        logs=logs,
        quote=QUOTES[date.today().day % len(QUOTES)],
        today_score=today_score,
        week_score=round(sum(scores7) / 7),
        month_score=round(sum(scores30) / 30),
        current_streak=streak_for(user.id),
        best_streak=best_streak(user.id),
        labels7=labels7,
        scores7=scores7,
        labels30=labels30,
        scores30=scores30,
    )


@app.route("/habit/add", methods=["GET", "POST"])
@login_required
def add_habit():
    user = current_user()
    if request.method == "POST":
        habit = Habit(
            user_id=user.id,
            name=request.form["name"].strip(),
            target=max(int(request.form["target"] or 1), 1),
            unit=request.form["unit"].strip() or "times",
            color=request.form.get("color", "#58d6ff"),
        )
        db.session.add(habit)
        db.session.commit()
        flash("Habit added.", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_habit.html", habit=None, title="Add Goal")


@app.route("/habit/<int:habit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_habit(habit_id):
    user = current_user()
    habit = Habit.query.filter_by(id=habit_id, user_id=user.id).first_or_404()
    if request.method == "POST":
        if "delete" in request.form:
            habit.active = False
            db.session.commit()
            flash("Habit removed from active goals.", "success")
            return redirect(url_for("dashboard"))
        habit.name = request.form["name"].strip()
        habit.target = max(int(request.form["target"] or 1), 1)
        habit.unit = request.form["unit"].strip() or "times"
        habit.color = request.form.get("color", habit.color)
        db.session.commit()
        flash("Goal updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_habit.html", habit=habit, title="Edit Goal")


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    habits = Habit.query.filter_by(user_id=user.id, active=True).all()
    return render_template(
        "profile.html",
        user=user,
        habits=habits,
        current_streak=streak_for(user.id),
        best_streak=best_streak(user.id),
        today_score=day_score(user.id, date.today()),
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
