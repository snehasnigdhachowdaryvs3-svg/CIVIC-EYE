from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)
import sqlite3
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "civic-eye-final-project-key"

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "civic_eye.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# ---------------- DATABASE CONNECTION ----------------

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- PHOTO VALIDATION ----------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ---------------- CREATE DATABASE ----------------

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            latitude TEXT,
            longitude TEXT,
            photo TEXT,
            created_at TEXT
        )
    """)

    # Detect columns in an older existing database
    cursor.execute("PRAGMA table_info(complaints)")
    existing_columns = [
        row["name"] for row in cursor.fetchall()
    ]

    # Add missing columns without deleting existing complaints
    migrations = {
        "status": "TEXT NOT NULL DEFAULT 'Pending'",
        "latitude": "TEXT",
        "longitude": "TEXT",
        "photo": "TEXT",
        "created_at": "TEXT"
    }

    for column, definition in migrations.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE complaints ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SUBMIT COMPLAINT ----------------

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    issue_type = request.form.get("issue_type", "").strip()
    description = request.form.get("description", "").strip()

    latitude = request.form.get("latitude", "").strip() or None
    longitude = request.form.get("longitude", "").strip() or None

    # Validate required fields
    if not name or not location or not issue_type or not description:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("home"))

    photo = request.files.get("photo")
    photo_filename = None

    # Handle photo upload
    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash(
                "Invalid photo. Use JPG, JPEG, PNG or WEBP.",
                "error"
            )
            return redirect(url_for("home"))

        safe_filename = secure_filename(photo.filename)
        extension = safe_filename.rsplit(".", 1)[1].lower()

        # Unique name prevents overwriting another photo
        photo_filename = f"{uuid.uuid4().hex}.{extension}"

        photo_path = os.path.join(
            UPLOAD_FOLDER,
            photo_filename
        )

        photo.save(photo_path)

    # Store complaint in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints (
            name, location, issue_type, description,
            status, latitude, longitude, photo, created_at
        )
        VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?, ?)
    """, (
        name,
        location,
        issue_type,
        description,
        latitude,
        longitude,
        photo_filename,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    flash("Complaint submitted successfully!", "success")
    return redirect(url_for("home"))


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/complaints")
def view_complaints():
    search = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Complaint search
    if search:
        search_term = f"%{search}%"

        cursor.execute("""
            SELECT * FROM complaints
            WHERE name LIKE ?
               OR location LIKE ?
               OR issue_type LIKE ?
               OR description LIKE ?
            ORDER BY id DESC
        """, (
            search_term,
            search_term,
            search_term,
            search_term
        ))
    else:
        cursor.execute("""
            SELECT * FROM complaints
            ORDER BY id DESC
        """)

    complaints = cursor.fetchall()

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) FROM complaints")
    total_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'Pending'
    """)
    pending_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'In Progress'
    """)
    progress_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'Resolved'
    """)
    resolved_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "complaints.html",
        complaints=complaints,
        search=search,
        total_count=total_count,
        pending_count=pending_count,
        progress_count=progress_count,
        resolved_count=resolved_count
    )


# ---------------- UPDATE STATUS ----------------

@app.route("/update_status", methods=["POST"])
def update_status():
    complaint_id = request.form.get("complaint_id", "")
    status = request.form.get("status", "")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if not complaint_id.isdigit():
        flash("Invalid complaint ID.", "error")
        return redirect(url_for("view_complaints"))

    if status not in allowed_statuses:
        flash("Invalid status selection.", "error")
        return redirect(url_for("view_complaints"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    flash("Complaint status updated successfully!", "success")
    return redirect(url_for("view_complaints"))


# ---------------- FILE SIZE ERROR ----------------

@app.errorhandler(413)
def file_too_large(error):
    flash("Photo exceeds 5 MB. Please select a smaller photo.", "error")
    return redirect(url_for("home"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
