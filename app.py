import os
import random
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


# ================= APP SETUP =================
app = Flask(__name__)

# Secure secret key (use environment variable in production)
app.secret_key = os.getenv("SECRET_KEY", "fr0m.ab0ve.secret")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------- DATABASE CONFIG ----------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"sslmode": "require"}
    }
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ================= MODELS =================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship(
        "Profile",
        backref="user",
        uselist=False,
        cascade="all, delete"
    )


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    display_name = db.Column(db.String(80))
    bio = db.Column(db.String(160))
    avatar = db.Column(db.String(200), default="default.jpg")
    city = db.Column(db.String(80))
    mood = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= AUTO CREATE TABLES (IMPORTANT FIX) =================
with app.app_context():
    db.create_all()


# ================= HELPERS =================
def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


# ================= AUTH ROUTES =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("signup"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("signup"))

        hashed_pw = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        profile = Profile(user_id=new_user.id, display_name=username)
        db.session.add(profile)
        db.session.commit()

        flash("Account created. Welcome to fr0m.ab0ve.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash(f"Welcome back, {user.username}.", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


# ================= MAIN ROUTES =================
@app.route("/")
def home():
    photos_folder = os.path.join(app.static_folder, "media/photos")
    photos = []

    if os.path.exists(photos_folder):
        for file in os.listdir(photos_folder):
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                photos.append(file)

    random.shuffle(photos)
    return render_template("home.html", photos=photos)


@app.route("/feed")
def feed():
    posts_folder = os.path.join(app.static_folder, "media/posts")
    posts = []

    if os.path.exists(posts_folder):
        for file in os.listdir(posts_folder):
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                posts.append({"type": "image", "file": file})
            elif file.lower().endswith((".mp4", ".webm")):
                posts.append({"type": "video", "file": file})

    random.shuffle(posts)
    return render_template("feed.html", posts=posts)


@app.route("/shop")
def shop():
    products = [
        {"id": 1, "name": "From Above Jacket", "price": 1199.99, "image": "From Above Jacket.jpg", "in_stock": True},
        {"id": 2, "name": "Make Nai Fly Again Tee", "price": 699.99, "image": "Make Nai Fly Again Tee.jpg", "in_stock": True},
        {"id": 3, "name": "From Above Sweats", "price": 2499.99, "image": "From Above Sweats.jpg", "in_stock": True},
        {"id": 4, "name": "From Above Cap", "price": 799.99, "image": "From Above Cap.jpg", "in_stock": True}
    ]
    return render_template("shop.html", products=products)


@app.route("/about")
def about():
    return render_template("about.html")


# ================= PROFILE ROUTES =================
@app.route("/profile")
def profile():
    user = current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template("profile.html", user=user, profile=user.profile)


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    user = current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    profile = user.profile

    if request.method == "POST":
        username = request.form.get("username")
        display_name = request.form.get("display_name")
        bio = request.form.get("bio")
        city = request.form.get("city")
        mood = request.form.get("mood")

        if username != user.username:
            if User.query.filter_by(username=username).first():
                flash("Username already taken.", "error")
                return redirect(url_for("edit_profile"))
            user.username = username
            session["username"] = username

        profile.display_name = display_name
        profile.bio = bio
        profile.city = city
        profile.mood = mood

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=user, profile=profile)


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)