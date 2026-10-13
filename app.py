import os
import random
import json
import hmac
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import smtplib
import ssl
from email.message import EmailMessage
from flask import Flask, abort, flash, redirect, render_template, request, Response, session, url_for

app = Flask(__name__)

# Load environment variables from a local .env file if present.
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    candidate = Path(__file__).resolve().parent / ".env"
    if candidate.exists():
        dotenv_path = str(candidate)

if dotenv_path:
    load_dotenv(dotenv_path)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_urlsafe(32)
app.config["DATABASE_PATH"] = Path(app.instance_path) / "club.sqlite3"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

MAIL_SERVER = (os.environ.get("MAIL_SERVER") or "localhost").strip() or "localhost"
MAIL_PORT = int(os.environ.get("MAIL_PORT", "25" if MAIL_SERVER == "localhost" else "587"))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false" if MAIL_SERVER == "localhost" else "true").lower() in ("1", "true", "yes")
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_FROM = os.environ.get("MAIL_FROM") or MAIL_USERNAME or "noreply@localhost"
MAIL_TO = os.environ.get("MAIL_TO") or MAIL_FROM

club_info = {
    "name": "Colchester Rangers FC",
    "tagline": "One Club, One City, One Goal",
    "description": "Welcome to the official site for Colchester Rangers FC. Discover the club staff, players, results, and get in touch with the team. We are a community-focused football club in Essex, bringing people together through local football and community engagement.",
}

sponsors = [
    {"name": "HCDW Commercial", "description": "Main club sponsor for Colchester Rangers FC. Proudly sponsoring the home kit for the next 2 years", "logo": "hcdw-logo.png", "url": "https://www.instagram.com/hcdwcommercial/"},
    {"name": "BC Python Development", "description": "Leading Python development, proud website provider and sponsor.", "logo": "BClogo.png", "url": "https://bcpythondev.co.uk"},
    {"name": "Helpful Essay Plans", "description": "The club are delighted to welcome on board HEP who help those in education take the stress out of essay planning.", "logo": "HEP-logo.jpg", "url": "https://www.facebook.com/share/1JesxRBreA/"},
    ]


staff = [
   
    {"name": "Henry Wright", "role": "Club Chairman, fixture secretary", "bio": "Proud founder of Colchester Rangers FC, overseeing all club operations.", "image": "henry-wright.jpg"},
    {"name": "Barry Calver", "role": "Vice Chairman, Website Developer", "bio": "Vice chairman of Colchester Rangers FC, supporting the club's operations and development.", "image": "barry-calver.jpg"},
    {"name": "Jamie LePage", "role": "First Team Manager", "bio": "Leading the first team as manager of Colchester Rangers FC.", "image": "Jamie-LePage.jpg"},
    {"name": "Ben Burnett", "role": "Club Nutritionist & Club Secretary", "bio": "Helping with the day-to-day running of the club and providing nutritional guidance to enhance performance.", "image": "ben-burnett.jpg"},
    {"name": "Alex Gooding", "role": "Treasurer", "bio": "Overseeing the club's financial operations and ensuring the club financial health.", "image": "alex-gooding.jpg"},
    {"name": "Tom Williams", "role": "Club Welfare Officer, IT Technician", "bio": "Providing graphics and designs for social media posts and club communications.", "image": "tom-williams.jpg"},
    ]
players = [
    {"name": "James Gentry", "position": "Goalkeeper", "number": 1, "image": "james-gentry.jpg", "bio": "A reliable shot-stopper with great reflexes and command of the box."},
    {"name": "Joshua Hill", "position": "Right wing / striker", "number":17, "image": "joshua-hill.jpg", "bio": "Pacy forward, likes to put crosses in from the right or cut inside for a shot. Loves running onto balls in behind the defence."},
    {"name": "Bradley Ashworth", "position": "Central Midfielder/Defensive Midfielder", "number": 6, "image": "brad-ashworth.jpg", "bio": "Ball playing defensive midfielder, with a great work rate."},
    {"name": "Michael Knight", "position": "Central Attacking Midfielder", "number": 10, "image": "michael-knight.jpg", "bio": "Calm on the ball, keen eye for a pass and great in possesion."},
    {"name": "Cameron Marcello", "position": "Central Midfielder/Defensive Midfielder", "number":4, "image": "cameron-marcello.jpg", "bio": "Strong Physical Midfielder, Loves a tackle and looks to move the ball forward quickly."},
    {"name": "Rui Sousa", "position": "Midfielder", "number": 13, "image": "rui-sousa.jpg", "bio": "Rui is a versatile player who is comfortable in multiple positions, enjoys playing out from the back, carrying the ball forward and picking a pass into space."},
    {"name": "Fernando Orellana", "position": "Forward", "number": 20, "image": "fernando-orellana.jpg", "bio": "Fernando is a dynamic forward who excels in the final third, known for his pace and clinical finishing."},
    {"name": "Jamie Mayes-Allen", "position": "Full Back", "number": 2, "image": "jamie-mayes-allen.jpg", "bio": "A solid ball winning full back who is very versatile and can be depended on at the back."},
    {"name": "Bobby Clarke", "position": "Fullback", "number": 5, "image": "bobby-clarke.jpg", "bio": "Athletic full back with excellent pace and defensive capabilities."},
    {"name": "Will Ashton", "position": "Forward", "number": 9, "image": "will-ashton.jpg", "bio": "Versatile forward with bags of pace and power and a passion for scoring and creating goals."},
    {"name": "Noah Gray", "position": "Centre Midfielder", "number":21, "image": "noah-gray.jpg", "bio": "A technically gifted midfielder with a great eye for a pass and the ability to control the tempo of the game. Also cover fullback if required."},
    {"name": "Joshua Wordingham", "position": "Right Winger / Central Midfielder", "number": 16, "image": "josh-wordingham.jpg", "bio": "Determined player, never gives up, and will always push himself to the limit! "},
    {"name": "Arthur Cox", "position": "Wing back", "number": 15, "image": "arthur-cox.jpg", "bio": "Enjoys simple football, doesn't overcomplicate things, simple passes keep possesion and look for the early pass."},
    {"name": "Daniel Walsh", "position": "Winger/Centre Attacking Midfielder", "number": 8, "image": "dan-walsh.jpg", "bio": "Direct, fast paced football, always looking to play through balls into the channels and to create shooting opportunities for himself and team mates."},
    {"name": "Finlay Parry", "position": "striker", "number": 18, "image": "finlay-parry.jpg", "bio": "Finlay is a powerful striker who loves running onto balls behind the defence."},
    {"name": "Jordan Lucky", "position": "Left Wing", "number": 7, "image": "jordan-lucky.jpg", "bio": "Jordan is from an athletics background so has pace to burn, and uses it effectively in an attacking capacity as well as defensively."},
    {"name": "Ronnie Mason", "position": "Winger", "number": 11, "image": "ronnie-mason.jpg", "bio": "A winger who loves driving forwards, picking out passes and getting into the box. Looks to pass and get an assist more than he does shoot."},
    {"name": "Jake Nailer", "position": "Left Winger", "number": 26, "image": "jake-nailer.jpg", "bio": "An inverted winger or inside forward who loves roaming in from the channels to get involved in play through the middle."},
    {"name": "Akinbusuyi Solomon", "position": "Defensive Midfield", "number": 30, "image": "akinbusuyi-solomon.jpg", "bio": "Loves winning the ball back, and breaking up opposition play to get us back on the front foot."},
    {"name": "Ryan Doggett", "position": "Centre Back", "number": 33, "image": "ryan-doggett.jpg", "bio": "Old school centre back, body on the line, strong tackling and aerial ability."},
    {"name": "Ben Swanster", "position": "Defender", "number": 31, "image": "ben-swanster.jpg", "bio": "An experienced and versatile defender, with a good understanding of the game. Good ability to read the game and cut out danger before it develops, and loves to get forward to!"},
    {"name": "Henry Wright", "position": "Winger", "number": 14, "image": "henry-wright-p.jpg", "bio": "A direct pacy winger with a good eye for a pass and also for a goal."},
    {"name": "Dan Pearce", "position": "Defender", "number": 34, "image": "dan-pearce.jpg", "bio": "Experienced defender, good in the air, comfortable on the ball, looking to play forward passes and also good at breaking up play."},
    {"name": "Danny Dibell", "position": "Defensive Midfielder", "number": 32, "image": "colchester-rangers-logo.jpg", "bio": "A left-footed defensive midfielder who is strong in the tackle, good at reading the game, breaking up play, and progressing the ball forward."},
]

results = [
    { "opponent": "Bradfield Rovers Reserves", "score": "2-6", "date": "August 8,2026", "venue": "Harwich High School", "competition": "Friendly", "goalscorers": "Finlay Parry (2)"},
    {"opponent": "Dedham Reserves","score":"0-5", "date": "August 15, 2026", "venue": "The Duchy, Dedham", "competition": "Friendly", "goalscorers": "None"},
    {"opponent": "Wivenhoe United FC", "score":"1-4", "date": "August 29, 2026", "venue": "Clacton Leisure Centre", "competition": "friendly", "goalscorers": "Finlay Parry"},
    {"opponent": "Silver End United Reservers","score":"0-1", "date": "September 5, 2026", "venue": "Silver End Village Hall", "competition": "League", "goalscorers": "None"},
]
matches = [
        
        {"opponent": "Mersea Island First", "date": "September 12, 2026", "venue": "The Glebe (Colchester) #2 ", "competition": "League"},
        {"opponent": "Broomfield A", "date": "September 19, 2026", "venue": "Broomfield Football Club", "competition": "Cup"},

]
   

FIXTURE_DATE_FORMATS = (
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
    "%d/%m/%Y",
)


def parse_fixture_date(value):
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        for date_format in FIXTURE_DATE_FORMATS:
            try:
                return datetime.strptime(value.strip(), date_format).date()
            except ValueError:
                continue
    return None


def get_upcoming_matches(today=None):
    current_date = today or date.today()
    return [
        match
        for match in get_collection("fixtures")
        if (fixture_date := parse_fixture_date(match.get("date", ""))) is None
        or fixture_date >= current_date
    ]


COLLECTION_FIELDS = {
    "players": ("name", "position", "number", "image", "bio"),
    "staff": ("name", "role", "bio", "image"),
    "results": ("opponent", "score", "date", "venue", "competition", "goalscorers"),
    "fixtures": ("opponent", "date", "venue", "competition"),
}
COLLECTION_SCHEMAS = {
    "players": """
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            number INTEGER NOT NULL,
            image TEXT NOT NULL,
            bio TEXT NOT NULL
        )
    """,
    "staff": """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            bio TEXT NOT NULL,
            image TEXT NOT NULL
        )
    """,
    "results": """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opponent TEXT NOT NULL,
            score TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            competition TEXT NOT NULL,
            goalscorers TEXT NOT NULL
        )
    """,
    "fixtures": """
        CREATE TABLE IF NOT EXISTS fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opponent TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            competition TEXT NOT NULL
        )
    """,
}


@contextmanager
def get_db_connection():
    database_path = Path(app.config["DATABASE_PATH"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_db_connection() as connection:
        for collection, schema in COLLECTION_SCHEMAS.items():
            connection.execute(schema)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for collection in ("players", "staff", "results"):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {collection}"
            ).fetchone()[0]
            if count == 0:
                fields = COLLECTION_FIELDS[collection]
                placeholders = ", ".join("?" for _ in fields)
                field_names = ", ".join(fields)
                connection.executemany(
                    f"INSERT INTO {collection} ({field_names}) VALUES ({placeholders})",
                    [
                        tuple(item.get(field, "") for field in fields)
                        for item in globals()[collection]
                    ],
                )
        fixture_migration = "seed_fixtures"
        if connection.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?", (fixture_migration,)
        ).fetchone() is None:
            if connection.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0] == 0:
                connection.executemany(
                    "INSERT INTO fixtures (opponent, date, venue, competition) VALUES (?, ?, ?, ?)",
                    [
                        tuple(fixture.get(field, "") for field in COLLECTION_FIELDS["fixtures"])
                        for fixture in matches
                    ],
                )
            connection.execute(
                "INSERT INTO schema_migrations (name) VALUES (?)", (fixture_migration,)
            )
        migration_name = "add_jamie_lepage_as_first_team_manager"
        migration = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?", (migration_name,)
        ).fetchone()
        if migration is None:
            existing_manager = connection.execute(
                "SELECT id FROM staff WHERE name = ? COLLATE NOCASE LIMIT 1",
                ("Jamie LePage",),
            ).fetchone()
            if existing_manager:
                connection.execute(
                    "UPDATE staff SET role = ? WHERE id = ?",
                    ("First Team Manager", existing_manager["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO staff (name, role, bio, image)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        "Jamie LePage",
                        "First Team Manager",
                        "Leading the first team as manager of Colchester Rangers FC.",
                        "Jamie-LePage.jpg",
                    ),
                )
            connection.execute(
                "INSERT INTO schema_migrations (name) VALUES (?)", (migration_name,)
            )


def get_collection(collection):
    if collection not in COLLECTION_FIELDS:
        raise ValueError(f"Unknown collection: {collection}")
    with get_db_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM {collection} ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


initialize_database()


def csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf_token():
    submitted_token = request.form.get("csrf_token", "")
    expected_token = session.get("_csrf_token", "")
    if not submitted_token or not expected_token or not hmac.compare_digest(submitted_token, expected_token):
        abort(400, description="Invalid or missing CSRF token.")


def admin_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            abort(503, description="Admin login is not configured.")
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def validate_image_upload(image):
    if not image or not image.filename:
        return None

    suffix = Path(image.filename).suffix.lower()
    allowed_headers = {
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".gif": (b"GIF87a", b"GIF89a"),
        ".webp": (b"RIFF",),
    }
    if suffix not in allowed_headers:
        raise ValueError("Use a JPG, PNG, GIF or WebP image.")

    header = image.stream.read(12)
    image.stream.seek(0)
    if not any(header.startswith(prefix) for prefix in allowed_headers[suffix]):
        raise ValueError("The uploaded file does not match its image extension.")
    if suffix == ".webp" and header[8:12] != b"WEBP":
        raise ValueError("The uploaded file is not a valid WebP image.")

    filename = f"{uuid.uuid4().hex}{suffix}"
    upload_directory = Path(app.static_folder) / "uploads"
    upload_directory.mkdir(parents=True, exist_ok=True)
    image.save(upload_directory / filename)
    return f"uploads/{filename}"


def remove_unused_upload(image_path):
    if not image_path or not image_path.startswith("uploads/"):
        return
    with get_db_connection() as connection:
        for collection in ("players", "staff"):
            if connection.execute(
                f"SELECT 1 FROM {collection} WHERE image = ? LIMIT 1", (image_path,)
            ).fetchone():
                return
    upload_path = Path(app.static_folder) / image_path
    if upload_path.is_file():
        upload_path.unlink()


def admin_sections():
    field_definitions = {
        "players": [
            ("name", "Player name", "text", True),
            ("position", "Position", "text", True),
            ("number", "Squad number", "number", True),
            ("bio", "Biography", "textarea", False),
            ("image", "Portrait image", "file", False),
        ],
        "staff": [
            ("name", "Staff member name", "text", True),
            ("role", "Role", "text", True),
            ("bio", "Biography", "textarea", False),
            ("image", "Portrait image", "file", False),
        ],
        "results": [
            ("date", "Date", "text", True),
            ("opponent", "Opponent", "text", True),
            ("score", "Score", "text", True),
            ("venue", "Venue", "text", True),
            ("competition", "Competition", "text", True),
            ("goalscorers", "Goalscorers", "text", False),
        ],
        "fixtures": [
            ("date", "Date", "date", True),
            ("opponent", "Opponent", "text", True),
            ("venue", "Venue", "text", True),
            ("competition", "Competition", "text", True),
        ],
    }
    labels = {
        "players": ("Players", "Player"),
        "staff": ("Staff", "Staff member"),
        "results": ("Results", "Result"),
        "fixtures": ("Fixtures", "Fixture"),
    }
    return [
        {
            "key": collection,
            "label": labels[collection][0],
            "singular": labels[collection][1],
            "records": get_collection(collection),
            "fields": field_definitions[collection],
        }
        for collection in ("players", "staff", "results", "fixtures")
    ]


@app.route("/admin", methods=["GET"])
@admin_login_required
def admin_dashboard():
    return render_template(
        "admin.html",
        title="Admin Control Panel | Colchester Rangers FC",
        sections=admin_sections(),
        csrf_token=csrf_token(),
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        abort(503, description="Admin login is not configured.")
    if session.get("admin_authenticated"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        validate_csrf_token()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        valid_username = hmac.compare_digest(username.encode("utf-8"), ADMIN_USERNAME.encode("utf-8"))
        valid_password = hmac.compare_digest(password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
        if valid_username and valid_password:
            session.clear()
            session["admin_authenticated"] = True
            session.permanent = True
            csrf_token()
            return redirect(url_for("admin_dashboard"))
        flash("The username or password was incorrect.", "error")
    return render_template(
        "admin_login.html",
        title="Admin Login | Colchester Rangers FC",
        csrf_token=csrf_token(),
    )


@app.route("/admin/logout", methods=["POST"])
@admin_login_required
def admin_logout():
    validate_csrf_token()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin/<collection>/save", methods=["POST"])
@admin_login_required
def admin_save(collection):
    if collection not in COLLECTION_FIELDS:
        abort(404)
    validate_csrf_token()
    record_id = request.form.get("id", "").strip()
    fields = COLLECTION_FIELDS[collection]
    values = {field: request.form.get(field, "").strip() for field in fields if field != "image"}
    required_fields = {
        "players": ("name", "position", "number"),
        "staff": ("name", "role"),
        "results": ("opponent", "score", "date", "venue", "competition"),
        "fixtures": ("opponent", "date", "venue", "competition"),
    }[collection]
    if any(not values[field] for field in required_fields):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("admin_dashboard"))
    if collection == "players":
        try:
            values["number"] = int(values["number"])
            if values["number"] < 1:
                raise ValueError
        except ValueError:
            flash("Squad number must be a positive whole number.", "error")
            return redirect(url_for("admin_dashboard"))

    existing = None
    if record_id:
        if not record_id.isdigit():
            abort(400, description="Invalid record id.")
        with get_db_connection() as connection:
            existing = connection.execute(
                f"SELECT * FROM {collection} WHERE id = ?", (int(record_id),)
            ).fetchone()
        if existing is None:
            abort(404)

    if collection == "players":
        with get_db_connection() as connection:
            duplicate = connection.execute(
                "SELECT 1 FROM players WHERE number = ? AND id != ? LIMIT 1",
                (values["number"], int(record_id) if record_id else -1),
            ).fetchone()
        if duplicate:
            flash("That squad number is already in use.", "error")
            return redirect(url_for("admin_dashboard"))

    try:
        uploaded_image = validate_image_upload(request.files.get("image"))
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("admin_dashboard"))

    if "image" in fields:
        values["image"] = uploaded_image or (existing["image"] if existing else "")
        if collection == "players" and not values["image"]:
            values["image"] = "staff-placeholder.svg"

    field_names = tuple(field for field in fields)
    try:
        with get_db_connection() as connection:
            if existing:
                assignments = ", ".join(f"{field} = ?" for field in field_names)
                connection.execute(
                    f"UPDATE {collection} SET {assignments} WHERE id = ?",
                    tuple(values[field] for field in field_names) + (int(record_id),),
                )
            else:
                placeholders = ", ".join("?" for _ in field_names)
                connection.execute(
                    f"INSERT INTO {collection} ({', '.join(field_names)}) VALUES ({placeholders})",
                    tuple(values[field] for field in field_names),
                )
    except sqlite3.Error:
        if uploaded_image:
            remove_unused_upload(uploaded_image)
        raise

    if existing and uploaded_image and existing["image"] != uploaded_image:
        remove_unused_upload(existing["image"])
    flash(f"{'Updated' if existing else 'Added'} {collection[:-1] if collection != 'staff' else 'staff member'}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/<collection>/<int:record_id>/delete", methods=["POST"])
@admin_login_required
def admin_delete(collection, record_id):
    if collection not in COLLECTION_FIELDS:
        abort(404)
    validate_csrf_token()
    with get_db_connection() as connection:
        record = connection.execute(
            f"SELECT * FROM {collection} WHERE id = ?", (record_id,)
        ).fetchone()
        if record is None:
            abort(404)
        connection.execute(f"DELETE FROM {collection} WHERE id = ?", (record_id,))
    remove_unused_upload(record["image"] if "image" in record.keys() else None)
    flash(f"Removed item from {collection}.", "success")
    return redirect(url_for("admin_dashboard"))


def send_contact_email(name, email, message_text):
    recipients = [item.strip() for item in (MAIL_TO or "").split(",") if item.strip()]
    if not recipients:
        return False

    msg = EmailMessage()
    msg["Subject"] = f"CRFC Contact Form: {name}"
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_text}\n"
    )

    try:
        if MAIL_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=context) as server:
                if MAIL_USERNAME and MAIL_PASSWORD:
                    server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
                if MAIL_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                if MAIL_USERNAME and MAIL_PASSWORD:
                    server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.send_message(msg)
        return True
    except Exception as exc:
        print("Email delivery failed:", exc)
        return False


@app.context_processor
def inject_sponsors():
    css_path = Path(app.static_folder) / "css" / "style.css"
    try:
        css_version = css_path.stat().st_mtime_ns
    except OSError:
        css_version = 1

    return {
        "club_info": club_info,
        "sponsors": sponsors,
        "css_version": css_version,
    }


DEFAULT_KEYWORDS = "Colchester Rangers FC, football club, local football, Essex, youth football, club news, trials, sponsors"


def render_seo_template(template, title, description, keywords=None, canonical_url=None, image_url=None, page_type="WebPage", meta_image=None, **context):
    canonical_url = canonical_url or request.base_url
    resolved_image_url = meta_image or image_url or url_for("static", filename="images/colchester-rangers-logo.jpg", _external=True)
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": club_info["name"],
                "url": request.url_root.rstrip("/"),
                "description": club_info["description"],
                "publisher": {
                    "@type": "SportsOrganization",
                    "name": club_info["name"],
                },
            },
            {
                "@type": "SportsTeam",
                "name": club_info["name"],
                "description": club_info["description"],
                "url": request.url_root.rstrip("/"),
                "logo": image_url,
                "sameAs": [
                    "https://www.instagram.com/colchesterrangers/"
                ],
            },
            {
                "@type": page_type,
                "name": title,
                "url": canonical_url,
                "description": description,
                "inLanguage": "en-GB",
            },
        ],
    }
    return render_template(
        template,
        title=title,
        meta_description=description,
        meta_keywords=keywords or DEFAULT_KEYWORDS,
        canonical_url=canonical_url,
        meta_image=resolved_image_url,
        schema_data=json.dumps(schema_data, indent=2),
        **context,
    )


@app.route("/enter")
def enter():
    return render_seo_template(
        "splash.html",
        title="Welcome | Colchester Rangers FC",
        description="Welcome to Colchester Rangers FC. Click the badge to enter the official club site.",
        canonical_url=url_for("enter", _external=True),
    )


@app.route("/")
def index():
    return redirect(url_for("enter"))


@app.route("/home")
def home():
    current_players = get_collection("players")
    star_players = random.sample(current_players, k=min(4, len(current_players)))
    return render_seo_template(
        "index.html",
        title="Home | Colchester Rangers FC",
        description="Official homepage for Colchester Rangers FC with club news, players, results, fixtures and training information.",
        canonical_url=url_for("home", _external=True),
        players=star_players,
        results=get_collection("results")[:4],
        matches=get_upcoming_matches()[:4],
    )


@app.route("/staff")
def show_staff():
    return render_seo_template(
        "staff.html",
        title="Staff | Colchester Rangers FC",
        description="Meet the Colchester Rangers FC management team and staff members.",
        canonical_url=url_for("show_staff", _external=True),
        staff=get_collection("staff"),
    )


@app.route("/players")
def show_players():
    sorted_players = sorted(get_collection("players"), key=lambda player: player["number"])
    return render_seo_template(
        "players.html",
        title="Players | Colchester Rangers FC",
        description="Explore the Colchester Rangers FC squad, positions and player profiles.",
        canonical_url=url_for("show_players", _external=True),
        players=sorted_players,
    )


@app.route("/results")
def show_results():
    return render_seo_template(
        "results.html",
        title="Results | Colchester Rangers FC",
        description="Review recent match results and club performance summaries.",
        canonical_url=url_for("show_results", _external=True),
        results=get_collection("results"),
    )


@app.route("/fixtures")
def show_fixtures():
    return render_seo_template(
        "fixtures.html",
        title="Fixtures | Colchester Rangers FC",
        description="See upcoming fixtures, opponents and match venues for Colchester Rangers FC.",
        canonical_url=url_for("show_fixtures", _external=True),
        matches=get_upcoming_matches(),
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message_text = request.form.get("message", "").strip()

        if not name or not email or not message_text:
            flash("Please complete all fields before sending your message.", "error")
            return redirect(url_for("contact"))

        if send_contact_email(name, email, message_text):
            flash(f"Thanks for your message, {name}! Your message has been sent.", "success")
        else:
            if MAIL_SERVER and MAIL_USERNAME and MAIL_PASSWORD and MAIL_TO:
                flash(
                    "We could not send your message right now. Please try again later or contact the club directly.",
                    "error",
                )
            else:
                flash(
                    "Email delivery is not configured. Your message was received, but the club will not get an automatic email.",
                    "warning",
                )
        return redirect(url_for("contact"))

    return render_seo_template(
        "contact.html",
        title="Contact | Colchester Rangers FC",
        description="Contact Colchester Rangers FC for enquiries about trials, sponsorship or club information.",
        canonical_url=url_for("contact", _external=True),
        meta_image=url_for("static", filename="images/contact-page-image.jpg", _external=True) if os.path.exists(Path(__file__).resolve().parent / "static" / "images" / "contact-page-image.jpg") else None,
        email_enabled=bool(MAIL_TO and MAIL_SERVER),
    )


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        url_for("enter", _external=True),
        url_for("home", _external=True),
        url_for("show_staff", _external=True),
        url_for("show_players", _external=True),
        url_for("show_results", _external=True),
        url_for("show_fixtures", _external=True),
        url_for("contact", _external=True),
    ]
    lastmod = datetime.utcnow().date().isoformat()
    sitemap_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        sitemap_xml.append("  <url>")
        sitemap_xml.append(f"    <loc>{page}</loc>")
        sitemap_xml.append(f"    <lastmod>{lastmod}</lastmod>")
        sitemap_xml.append("    <changefreq>weekly</changefreq>")
        sitemap_xml.append("    <priority>0.8</priority>")
        sitemap_xml.append("  </url>")
    sitemap_xml.append("</urlset>")
    return Response("\n".join(sitemap_xml), mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    sitemap_url = url_for("sitemap", _external=True)
    content = """
User-agent: *
Allow: /
Sitemap: %s
""" % sitemap_url
    return Response(content.strip() + "\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
