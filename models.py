from datetime import date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    habits = db.relationship("Habit", backref="user", lazy=True, cascade="all, delete-orphan")
    logs = db.relationship("HabitLog", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    target = db.Column(db.Integer, default=1, nullable=False)
    unit = db.Column(db.String(30), default="times", nullable=False)
    color = db.Column(db.String(20), default="#58d6ff", nullable=False)
    created_at = db.Column(db.Date, default=date.today, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    logs = db.relationship("HabitLog", backref="habit", lazy=True, cascade="all, delete-orphan")


class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today, nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "log_date", name="unique_habit_log_day"),
    )
