from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ================= USER =================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one-to-one relationship
    profile = db.relationship(
        "Profile",
        backref="user",
        uselist=False,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<User {self.username}>"

# ================= PROFILE =================
class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    display_name = db.Column(db.String(80))
    bio = db.Column(db.String(160))
    avatar = db.Column(db.String(200), default="default.jpg")

    city = db.Column(db.String(80))
    mood = db.Column(db.String(40))  # optional vibe text

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Profile user_id={self.user_id}>"
