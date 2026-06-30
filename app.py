from resume_analyzer import analyze_resume
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from flask_session import Session
from werkzeug.utils import secure_filename
import bcrypt
import json
import os
from dotenv import load_dotenv   # load .env

from ai_helper import generate_career_advice
from db import (
    accounts,
    users,
    analysis
)

# ==========================================
# Flask Configuration
# ==========================================

load_dotenv()   # load environment variables

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Upload configuration
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # ensure folder exists

Session(app)

# ==========================================
# Load JSON Files
# ==========================================

with open("data/skills.json", "r") as file:
    skills_data = json.load(file)

with open("data/roadmap.json", "r") as file:
    roadmap_data = json.load(file)

with open("data/projects.json", "r") as file:
    projects_data = json.load(file)

with open("data/courses.json", "r") as file:
    courses_data = json.load(file)

# ==========================================
# Home Page
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")

# ==========================================
# Register
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        existing = accounts.find_one({"email": email})
        if existing:
            return "Email already registered!"

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        accounts.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password
        })

        return redirect(url_for("login"))

    return render_template("register.html")

# ==========================================
# Login
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = accounts.find_one({"email": email})

        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"]
        ):
            session["user"] = email
            return redirect(url_for("dashboard"))

        return "Invalid email or password!"

    return render_template("login.html")

# ==========================================
# Dashboard
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    user_data = accounts.find_one({
        "email": user_email
    })

    # Guard against a missing account record so the template never
    # has to deal with `user` being None.
    if user_data is None:
        session.clear()
        return redirect(url_for("login"))

    latest_analysis = analysis.find_one(
        {"email": user_email},
        sort=[("_id", -1)]
    )

    if latest_analysis is None:
        latest_analysis = {}

    latest_analysis.setdefault("career", "")
    latest_analysis.setdefault("score", 0)
    latest_analysis.setdefault("missing_skills", [])
    latest_analysis.setdefault("courses", [])
    latest_analysis.setdefault("projects", [])
    latest_analysis.setdefault("roadmap", [])
    latest_analysis.setdefault("ai_advice", "")

    # Resume defaults
    latest_analysis.setdefault("resume_score", 0)
    latest_analysis.setdefault("resume_skills", [])

    return render_template(
        "dashboard.html",
        user=user_data,
        analysis=latest_analysis
    )

# ==========================================
# Logout
# ==========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================================
# Profile Page
# ==========================================

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user = accounts.find_one({"email": session["user"]})

    return render_template(
        "profile.html",
        user=user
    )

# ==========================================
# Resume Page
# ==========================================

@app.route("/resume", methods=["GET"])
def resume_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("resume.html")


@app.route("/resume", methods=["POST"])
def upload_resume():

    if "user" not in session:
        return redirect(url_for("login"))

    if "resume" not in request.files:
        return "No file selected"

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    result = analyze_resume(filepath)

    user_email = session["user"]

    # Find the user's most recent analysis document so the resume
    # results land on the same record the dashboard reads from.
    latest = analysis.find_one(
        {"email": user_email},
        sort=[("_id", -1)]
    )

    if latest:
        analysis.update_one(
            {"_id": latest["_id"]},
            {
                "$set": {
                    "resume_score": result["score"],
                    "resume_skills": result["skills"],
                    "missing_skills": result["missing"]
                }
            }
        )
    else:
        analysis.insert_one({
            "email": user_email,
            "resume_score": result["score"],
            "resume_skills": result["skills"],
            "missing_skills": result["missing"]
        })

    return render_template(
        "resume_result.html",
        result=result
    )

# ==========================================
# Analyze Function
# ==========================================

@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form["name"]
    degree = request.form["degree"]
    branch = request.form["branch"]
    year = request.form["year"]
    career = request.form["career"]

    email = ""
    if "user" in session:
        email = session["user"]

    skills = request.form["skills"]
    user_skills = [
        skill.strip().lower()
        for skill in skills.split(",")
    ]

    ai_advice = generate_career_advice(
        name,
        degree,
        branch,
        year,
        skills,
        career
    )

    required_skills = skills_data[career]["required_skills"]
    missing_skills = []

    for skill in required_skills:
        if skill.lower() not in user_skills:
            missing_skills.append(skill)

    score = int(
        (
            (len(required_skills) - len(missing_skills))
            / len(required_skills)
        ) * 100
    )

    roadmap = roadmap_data[career]["roadmap"]

    if isinstance(projects_data[career], dict):
        projects = projects_data[career]["projects"]
    else:
        projects = projects_data.get(career, [])

    if isinstance(courses_data[career], dict):
        courses = courses_data[career]["courses"]
    else:
        courses = courses_data.get(career, [])

    users.insert_one({
        "email": email,
        "name": name,
        "degree": degree,
        "branch": branch,
        "year": year,
        "career": career,
        "skills": user_skills
    })

    analysis.insert_one({
        "email": email,
        "name": name,
        "degree": degree,
        "branch": branch,
        "year": year,
        "career": career,
        "skills": user_skills,
        "score": score,
        "missing_skills": missing_skills,
        "roadmap": roadmap,
        "projects": projects,
        "courses": courses,
        "ai_advice": ai_advice
    })

    return render_template(
        "result.html",
        name=name,
        degree=degree,
        branch=branch,
        year=year,
        career=career,
        skills=skills,
        score=score,
        missing_skills=missing_skills,
        roadmap=roadmap,
        projects=projects,
        courses=courses,
        ai_advice=ai_advice
    )

# ==========================================
# Run Flask
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)