import os
import random
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import smtplib
import ssl
from email.message import EmailMessage
from flask import Flask, render_template, request, flash, redirect, url_for, Response

app = Flask(__name__)

# Load environment variables from a local .env file if present.
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    candidate = Path(__file__).resolve().parent / ".env"
    if candidate.exists():
        dotenv_path = str(candidate)

if dotenv_path:
    load_dotenv(dotenv_path)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace-with-a-secure-key")

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
    {"name": "BC Python Development", "description": "Leading Python development, proud website provider.", "logo": "BClogo.png", "url": "https://mysite-production-e447.up.railway.app/"},
    ]


staff = [
    {"name": "Mark Pilgrim", "role": "Manager", "bio": "First team manager, with a wealth of experience locally at ESBL premier level.", "image": "mark-pilgrim.jpg"},
    {"name": "George Pilgrim", "role": "Assistant Manager", "bio": "George is joining the club as assistant manager, to work alongside Mark, having worked together previously and forming a great partnership!", "image": "george-pilgrim.jpg"},
    {"name": "Henry Wright", "role": "Club Chairman, Welfare Officer", "bio": "Proud founder of Colchester Rangers FC, overseeing all club operations.", "image": "henry-wright.jpg"},
    {"name": "Ben Burnett", "role": "Club Nutritionist & Club Secretary", "bio": "Helping with the day to day running of the club, and providing nutritional guidance to enhance perfromance.", "image": "ben-burnett.jpg"},
    {"name": "Alex Gooding", "role": "Treasurer", "bio": "Overseeing the club's financial operations and ensuring the club financial health.", "image": "alex-gooding.jpg"},
    {"name": "Chera Asefa", "role": "Fixture Secretary", "bio": "We are delighted to have Chera on board helping us out as our new fixture secretary.", "image": "static/images/chera-asefa.jpg"}, 
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
    {"name": "Charlie Offord", "position": "Centre Midfielder", "number": 23, "image": "charlie-offord.jpg", "bio": "Big strengths are through balls, holding the ball up under pressure and creating space for team mates. Can also provide defensive cover when required."},
    {"name": "Bobby Clarke", "position": "Fullback", "number": 5, "image": "bobby-clarke.jpg", "bio": "Athletic full back with excellent pace and defensive capabilities."},
    {"name": "Will Ashton", "position": "Forward", "number": 9, "image": "will-ashton.jpg", "bio": "Versatile forward with bags of pace and power and a passion for scoring and creating goals."},
    {"name": "Noah Gray", "position": "Centre Midfielder", "number":21, "image": "noah-gray.jpg", "bio": "A technically gifted midfielder with a great eye for a pass and the ability to control the tempo of the game. Also cover fullback if required."},
    {"name": "Williams Franklin", "position": "Centre Back", "number": 27, "image": "williams-franklin.jpg", "bio": "Calm, Vocal, and disciplined, leads and controls the defence with authority and is a strong presence in the air."},
    {"name": "Joshua Wordingham", "position": "Right Winger / Central Midfielder", "number": 16, "image": "josh-wordingham.jpg", "bio": "Determined player, never gives up, and will always push himself to the limit! "},
    {"name": "Arthur Cox", "position": "Wing back", "number": 15, "image": "arthur-cox.jpg", "bio": "Enjoys simple football, doesn't overcomplicate things, simple passes keep possesion and look for the early pass."},
    {"name": "Alfie Beard", "position": "Fullback", "number": 22, "image": "alfie-beard.jpg", "bio": "Defensive fullback, possesses great pace and defensive capabilities."},
    {"name": "Daniel Walsh", "position": "Winger/Centre Attacking Midfielder", "number": 8, "image": "dan-walsh.jpg", "bio": "Direct, fast paced football, always looking to play through balls into the channels and to create shooting opportunities for himself and team mates."},
    {"name": "Finlay Parry", "position": "striker", "number": 18, "image": "finlay-parry.jpg", "bio": "Finlay is a powerful striker who loves running onto balls behind the defence."},
    {"name": "Jordan Lucky", "position": "Left Wing", "number": 7, "image": "jordan-lucky.jpg", "bio": "Jordan is from an athletics background so has pace to burn, and uses it effectively in an attacking capacity as well as defensively."},
    {"name": "Ronnie Mason", "position": "Winger", "number": 11, "image": "ronnie-mason.jpg", "bio": "A winger who loves driving forwards, picking out passes and getting into the box. Looks to pass and get an assist more than he does shoot."},
    {"name": "Adam Lancaster", "position": "Left Back", "number": 12, "image": "adam-lancaster.jpg", "bio": "An explosive full back who loves to get forward when he can and in possesion loves to play an inverted full back role."},
    {"name": "Jake Nailer", "position": "Left Winger", "number": 26, "image": "jake-nailer.jpg", "bio": "An inverted winger or inside forward who loves roaming in from the channels to get involved in play through the middle."},
    {"name": "Nouman Sher", "position": "Striker", "number": 19, "image": "nouman-sher.jpg", "bio": "A centre Forward with a keen eye for goal, and always willing to put the work in."},
    {"name": "Akinbusuyi Solomon", "position": "Defensive Midfield", "number": 30, "image": "akinbusuyi-solomon.jpg", "bio": "Loves winning the ball back, and breaking up opposition play to get us back on the front foot."},
]

results = [
    {
        "opponent": "TBA",
        "score": "TBA",
        "date": "TBA",
        "venue": "TBA",
        "competition": "TBA",
        "goalscorers": "TBA",
    },
]
matches = [
    {"opponent": "Stillwaters FC", "date": "July 11, 2026", "venue": "TBC", "competition": "Friendly"},
    {"opponent": "Tekkers FC",  "date": "July 15, 2026", "venue": "TBC", "competition": "Friendly"},
    {"opponent": "East Bergholt A",  "date": "August 1, 2026", "venue": "TBC", "competition": "Friendly"},
    {"opponent": "Bradfield Rovers Reserves", "date": "August 8, 2026", "venue": "TBC", "competition": "Friendly"}
]
   



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
    return {
        "club_info": club_info,
        "sponsors": sponsors,
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
    star_players = random.sample(players, k=min(3, len(players)))
    return render_seo_template(
        "index.html",
        title="Home | Colchester Rangers FC",
        description="Official homepage for Colchester Rangers FC with club news, players, results, fixtures and training information.",
        canonical_url=url_for("home", _external=True),
        players=star_players,
        results=results[:3],
        matches=matches,
    )


@app.route("/staff")
def show_staff():
    return render_seo_template(
        "staff.html",
        title="Staff | Colchester Rangers FC",
        description="Meet the Colchester Rangers FC management team and staff members.",
        canonical_url=url_for("show_staff", _external=True),
        staff=staff,
    )


@app.route("/players")
def show_players():
    sorted_players = sorted(players, key=lambda player: player["number"])
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
        results=results,
    )


@app.route("/fixtures")
def show_fixtures():
    return render_seo_template(
        "fixtures.html",
        title="Fixtures | Colchester Rangers FC",
        description="See upcoming fixtures, opponents and match venues for Colchester Rangers FC.",
        canonical_url=url_for("show_fixtures", _external=True),
        matches=matches,
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
