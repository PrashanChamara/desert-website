from flask import Flask, render_template, request, abort, Response, redirect
from flask_compress import Compress
import os
import math
import json
import re
import hmac
from datetime import datetime

app = Flask(__name__)
Compress(app)

# ---------------------------------------------------------
# PERFORMANCE: Cache static assets for 30 days
# ---------------------------------------------------------
@app.after_request
def add_performance_headers(response):
    # Cache static files aggressively
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
    # Add security headers
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BLOG_DIR = 'content/posts'
POSTS_PER_PAGE = 6
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')

# ---------------------------------------------------------
# DATA: BRANCH NETWORK
# (6 centres across Dubai and Sharjah)
# ---------------------------------------------------------
BRANCHES = [
    {
        "id": "sharjah-english-school",
        "name": "Sharjah English School (SES)",
        "area": "Sharjah (Maliha Road)",
        "map_url": "https://maps.app.goo.gl/6SmMmAASK5GRcmwp9",
        "img": "SES_Location.jpg",
        "schedule_img": "SES_Schedule.jpg",
        "desc": "The crown jewel of our academy. Featuring a full natural grass ground and six natural grass turf center pitches with floodlights. We offer digital scoreboards, live streaming, and a viewing pavilion.",
        "facilities": ["Natural Grass Ground", "6 Center Turf Pitches", "Floodlights", "Video Analysis Room", "Gymnasium", "Digital Scoreboard"],
        "coaches": [
            {"name": "Murali Sockalingam", "role": "Deputy Head Coach", "qual": "ICC Level 3 / ACC Level 2", "img": "coach_murali.jpg"},
            {"name": "Aruna Bandaranayaka", "role": "Senior Coach", "qual": "ICC Level 3 / Cricket Aus Level 2", "img": "coach_aruna.jpg"},
            {"name": "Vishwa Fernandopulle", "role": "Coach", "qual": "SL Level 1 / Umpire", "img": "coach_vishwa.jpg"},
            {"name": "Janaka Senevirathna", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_janaka.jpg"},
            {"name": "Shanesh Weerawansha", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_shanesh.jpg"}
        ]
    },
    {
        "id": "delhi-private-school",
        "name": "Delhi Private School (DPS)",
        "area": "Jebel Ali, Dubai",
        "map_url": "https://maps.app.goo.gl/sojJP1fK8g18sFsE7",
        "img": "DPS_Location.jpg",
        "schedule_img": "DPS_Schedule.jpg",
        "desc": "A premium facility in The Gardens. Features a high-quality Astro turf ground with a center pitch and floodlights, perfect for evening high-performance training.",
        "facilities": ["Astro Turf Ground", "Floodlights", "3 Practice Nets", "Bowling Machine", "Pavilion"],
        "coaches": [
            {"name": "Prosanta Chanda", "role": "Centre In-Charge", "qual": "ICC Level 3 / Cricket Aus Level 2", "img": "coach_prosanta.jpg"},
            {"name": "Chanaka Ediriweerage", "role": "Coach", "qual": "SL Level 2", "img": "coach_chanaka.jpg"},
            {"name": "Judith Jose Peter", "role": "Coach (Girls)", "qual": "ICC Level 1 / Ex-UAE Player", "img": "coach_judith.jpg"}
        ]
    },
    {
        "id": "deira-international-school",
        "name": "Deira Intl. School (DIS)",
        "area": "Dubai Festival City",
        "map_url": "https://maps.app.goo.gl/uuRBPjNs5UN61Nmw7",
        "img": "DIS_Location.jpg",
        "schedule_img": "DIS_Schedule.jpg",
        "desc": "Located in Festival City, this centre boasts a natural grass ground and an Astro turf center pitch. Equipped with four side practice nets and modern bowling machines.",
        "facilities": ["Natural Grass Ground", "Astro Center Pitch", "4 Side Nets", "Bowling Machine"],
        "coaches": [
            {"name": "Hashan Silva", "role": "Centre In-Charge", "qual": "ICC Level 1 / Winning Coach U16", "img": "coach_hashan.jpg"},
            {"name": "Shahzada Saleem", "role": "Senior Coach", "qual": "ACC Level 3", "img": "coach_shahzada.jpg"},
            {"name": "Priyantha Ganegoda", "role": "Coach", "qual": "ICC Level 1", "img": "coach_priyantha.jpg"}
        ]
    },
    {
        "id": "star-international-school",
        "name": "Star Intl. School (SIS)",
        "area": "Al Qusais 3, Dubai",
        "map_url": "https://g.co/kgs/wnL4YE",
        "img": "SIS_Location.jpg",
        "schedule_img": "SIS_Schedule.jpg",
        "desc": "A versatile sports hub in Al Qusais. Features an Astro turf ground, six practice nets with floodlights, and access to an indoor pool for cross-training.",
        "facilities": ["Astro Turf Ground", "6 Practice Nets", "Indoor Pool", "Floodlights"],
        "coaches": [
            {"name": "Muhammad Ejaz", "role": "Centre In-Charge", "qual": "ICC Level 1 / PCB Level 1", "img": "coach_ejaz.jpg"},
            {"name": "Manish Yadav", "role": "Coach", "qual": "SL Level 2", "img": "coach_manish.jpg"},
            {"name": "Nipuna Ratnayake", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_nipuna.jpg"}
        ]
    },
    {
        "id": "baseline-sports-academy",
        "name": "Baseline Sports Academy (BSA)",
        "area": "Dubai Investment Park (DIP)",
        "map_url": "https://maps.app.goo.gl/K5Azn4sgXpHTkJo8A",
        "img": "BSA_Location.jpg",
        "schedule_img": "BSA_Schedule.jpg",
        "desc": "State-of-the-art indoor cricket facility — one of a kind in the UAE. Perfect for summer training, equipped with 5 specialized cricket lanes and video analysis technology.",
        "facilities": ["Indoor Facility", "5 Cricket Lanes", "Video Analysis", "AC Controlled", "Year-Round Training"],
        "coaches": [
            {"name": "Manju Abeysekera", "role": "Coach", "qual": "ICC Level 1", "img": "coach_manju.jpg"},
            {"name": "Anjalo Silva", "role": "Centre In-Charge", "qual": "SL Level 1", "img": "coach_anjalo.jpg"}
        ]
    },
    {
        "id": "apple-international-school",
        "name": "Apple Intl. School (AIS)",
        "area": "Al Karama, Dubai",
        "map_url": "https://maps.app.goo.gl/YKw7RVALgojj7K8a9?g_st=awb",
        "img": "AIS_Location.jpg",
        "schedule_img": "AIS_Schedule.jpg",
        "desc": "Serving the heart of Dubai in Karama. Features three side practice nets with Astro turf pitches and a dedicated fielding and fitness area.",
        "facilities": ["3 Astro Nets", "Fielding Area", "Floodlights", "Bowling Machine"],
        "coaches": [
            {"name": "Ruwan Jayakody", "role": "Centre In-Charge", "qual": "ICC Level 2", "img": "coach_ruwan.jpg"},
            {"name": "Moin Sabir", "role": "Coach", "qual": "PCB Level 1", "img": "coach_moin.jpg"}
        ]
    },
]

# ---------------------------------------------------------
# DATA: TOURS
# ---------------------------------------------------------
TOURS = {
    "upcoming": [
        {
            "year": "2026",
            "dest": "United Kingdom",
            "type": "Elite Exposure Tour",
            "status": "Registration Open",
            "desc": "Join us for the ultimate cricketing experience. Play against top English counties, train at historic venues, and experience the home of cricket. Open for U10 to U19 squads.",
            "reg_link": "https://forms.gle/CzHzU4WhzkvwAYBx5",
            "pdf": "DC_UK_2026.pdf"
        }
    ],
    "history": [
        {
            "year": "2025",
            "dest": "Sri Lanka",
            "desc": "High Performance Tour featuring 40/50 Overs format games & GCCA T20 Championship.",
            "gallery": {
                "folder": "DC_Srilanka_2025",
                "prefix": "DC_Srilanka",
                "count": 10
            }
        },
        {
            "year": "2024",
            "dest": "Brisbane, Australia",
            "desc": "ICCA Global Academy Championship with Queensland Cricket.",
            "gallery": {
                "folder": "DC_Australia_2024",
                "prefix": "DC_Australia",
                "count": 10
            }
        },
        {
            "year": "2023",
            "dest": "UK & Wales",
            "desc": "Largest ever academy tour: 220 players & parents, 10 teams.",
            "gallery": {
                "folder": "DC_UK_2023",
                "prefix": "DC_UK",
                "count": 10
            }
        },
        {
            "year": "2022",
            "dest": "South Africa",
            "desc": "Pretoria, Johannesburg & Rustenburg tour.",
            "gallery": None
        },
        {
            "year": "2015",
            "dest": "Australia",
            "desc": "First UAE academy to tour Australia (Brisbane) — a historic milestone.",
            "gallery": None
        }
    ]
}

# ---------------------------------------------------------
# DATA: TOURNAMENTS
# ---------------------------------------------------------
TOURNAMENTS = [
    {"name": "DC Premier League", "month_start": 9, "month_end": 9, "type": "Internal", "desc": "The season opener — our flagship academy league to kick off the year."},
    {"name": "DC Emerging League", "month_start": 10, "month_end": 10, "type": "Internal", "desc": "For our rising stars — a dedicated league for promising new talent."},
    {"name": "ECB National Junior Tournament", "month_start": 10, "month_end": 1, "type": "External", "desc": "UAE National Junior Cricket Tournament organised by Emirates Cricket Board."},
    {"name": "Gulf Cup", "month_start": 11, "month_end": 1, "type": "External", "desc": "Regional championship with teams from across the Gulf."},
    {"name": "DC Winter Cup", "month_start": 11, "month_end": 12, "type": "Internal", "desc": "Holiday season competitive series — the most exciting time of year."},
    {"name": "DC Super League", "month_start": 1, "month_end": 1, "type": "Internal", "desc": "High intensity academy league for our most competitive players."},
    {"name": "DC Ramadan Cup", "month_start": 1, "month_end": 2, "type": "Internal", "desc": "Special evening matches under floodlights during the holy month."},
    {"name": "DC Junior Cups", "month_start": 2, "month_end": 2, "type": "Internal", "desc": "Focused on U10 and U12 development — our youngest champions shine."},
    {"name": "4 Nation Tournament", "month_start": 3, "month_end": 4, "type": "External", "desc": "International academy clash featuring teams from 4 nations."},
    {"name": "DC Summer Bash", "month_start": 4, "month_end": 5, "type": "Internal", "desc": "End of season celebration league — have fun, play hard!"},
]

# ---------------------------------------------------------
# DATA: MASTER CLASSES
# ---------------------------------------------------------
MASTER_CLASSES = [
    {
        "legend": "Jonty Rhodes",
        "date": "Nov 2019",
        "desc": "South African fielding legend. 3-day masterclass at SES and DPS centres.",
        "folder": None,
        "count": 0,
        "id": "jonty"
    },
    {
        "legend": "Dinesh Karthik",
        "date": "Oct 2021",
        "desc": "India's elite wicketkeeper-batsman. 1-day session at DPS centre.",
        "folder": None,
        "count": 0,
        "id": "dk"
    },
    {
        "legend": "Marvan Atapattu",
        "date": "Sept 2022",
        "desc": "Former Sri Lankan Captain & Head Coach. Technical batting masterclass.",
        "folder": "master_class",
        "prefix": "marven_atapattu",
        "count": 10,
        "id": "marvan"
    },
    {
        "legend": "Chaminda Vaas",
        "date": "Feb 2022",
        "desc": "Sri Lankan swing bowling legend — mastering the art of seam and swing.",
        "folder": None,
        "count": 0,
        "id": "vaas"
    },
    {
        "legend": "Ravichandran Ashwin",
        "date": "Nov 2018",
        "desc": "India's world-class off-spinner. Spin wizardry and tactical analysis at SES & DIS.",
        "folder": None,
        "count": 0,
        "id": "ashwin"
    },
    {
        "legend": "Dav Whatmore",
        "date": "Nov 2017",
        "desc": "World Cup winning coach — tactical and technical coaching masterclass.",
        "folder": None,
        "count": 0,
        "id": "whatmore"
    },
    {
        "legend": "Romesh Kaluwitharana",
        "date": "Mar 2018",
        "desc": "World Cup winning Sri Lanka opener. High performance batting program.",
        "folder": None,
        "count": 0,
        "id": "kalu"
    },
    {
        "legend": "Rumesh Ratnayake",
        "date": "Oct 2016",
        "desc": "Pace Foundation program by Sri Lanka fast bowling legend & ACC official.",
        "folder": None,
        "count": 0,
        "id": "rumesh"
    },
]

# ---------------------------------------------------------
# DATA: EVENTS
# ---------------------------------------------------------
EVENTS = [
    {
        "title": "Annual Sports Day 2025",
        "date": "December 2025",
        "desc": "Our biggest annual gathering. Parents vs Coaches, Fun Games, Talent Shows, and Awards Night.",
        "folder": "event",
        "prefix": "dc_sports_day",
        "count": 10,
        "id": "sportsday25"
    }
]

# ---------------------------------------------------------
# DATA: SPONSORS (NEW)
# ---------------------------------------------------------
SPONSORS = {
    "venue_partners": [
        {"name": "Sharjah English School", "short": "SES", "location": "Sharjah"},
        {"name": "Delhi Private School", "short": "DPS", "location": "Jebel Ali, Dubai"},
        {"name": "Deira International School", "short": "DIS", "location": "Festival City, Dubai"},
        {"name": "Star International School", "short": "SIS", "location": "Al Qusais, Dubai"},
        {"name": "Apple International School", "short": "AIS", "location": "Al Karama, Dubai"},
        {"name": "Baseline Sports Academy", "short": "BSA", "location": "DIP, Dubai"},
    ],
    "cricket_bodies": [
        {"name": "Emirates Cricket Board", "role": "Affiliated Academy"},
        {"name": "ICC", "role": "ICC Certified Coaching"},
        {"name": "GCCA", "role": "Gulf Cricket & Cultural Association"},
    ]
}

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def extract_post_meta(content):
    """Extract SEO metadata embedded by N8N as an HTML comment at the top of the post.
    N8N writes: <!-- DC_META: {"seo_title":"...","seo_description":"...","blog_title":"..."} -->
    Returns a dict, or None if no comment found (falls back to slug-derived values).
    """
    match = re.search(r'<!--\s*DC_META:\s*(\{.*?\})\s*-->', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def get_blog_posts():
    posts = []
    if not os.path.exists(BLOG_DIR):
        os.makedirs(BLOG_DIR)

    files = sorted(os.listdir(BLOG_DIR), reverse=True)

    for filename in files:
        if filename.endswith(".html"):
            try:
                date_part = filename[:10]
                slug = filename[:-5]
                fallback_title = slug[11:].replace('-', ' ').title()

                # Read DC_META comment for real title and description
                filepath = os.path.join(BLOG_DIR, filename)
                meta = None
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        head = f.read(512)  # Only read first 512 bytes — DC_META is always first line
                    meta = extract_post_meta(head)
                except Exception:
                    pass

                posts.append({
                    'title': meta.get('blog_title', fallback_title) if meta else fallback_title,
                    'description': meta.get('seo_description', '') if meta else '',
                    'date': date_part,
                    'slug': slug,
                    'filename': filename,
                    'image': f"{slug}.jpg",
                    'category': meta.get('category', 'Cricket Tips') if meta else 'Cricket Tips'
                })
            except Exception:
                continue
    return posts


def get_active_tournament():
    """Returns the tournament currently active based on the current month."""
    current_month = datetime.now().month
    active = [t for t in TOURNAMENTS if t['month_start'] <= current_month <= t['month_end']]
    if not active:
        return TOURNAMENTS[0]
    return active[0]


def get_global_seo():
    try:
        seo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content', 'seo.json')
        with open(seo_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def verify_webhook(req):
    """Check X-Webhook-Token header against WEBHOOK_SECRET. Open if no secret configured."""
    if not WEBHOOK_SECRET:
        return True
    token = req.headers.get('X-Webhook-Token', '')
    return hmac.compare_digest(token, WEBHOOK_SECRET)

def seo(title=None, description=None, keywords=None, canonical=None, og_image=None):
    global_seo = get_global_seo()
    
    return {
        'title': title or global_seo.get('title', 'Desert Cubs Cricket Academy UAE | Junior Cricket Dubai & Sharjah | Est. 2007'),
        'description': description or global_seo.get('description', "UAE's largest junior cricket academy. 15,000+ alumni. 6 training centres across Dubai & Sharjah. ICC-certified coaches. Ages 4–19. Enroll today!"),
        'keywords': keywords or global_seo.get('keywords', 'cricket academy UAE, junior cricket Dubai, cricket coaching Sharjah, kids cricket UAE, Desert Cubs'),
        'canonical': canonical or 'https://www.desertcubs.com',
        'og_image': og_image or 'https://www.desertcubs.com/static/img/Desert_cubs_logo.png'
    }

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route('/')
def index():
    active_tournament = get_active_tournament()
    meta = seo(
        title="Desert Cubs — UAE's Best Cricket Academy | Dubai & Sharjah | Est. 2007",
        description="Desert Cubs is the best cricket academy in UAE & Dubai. 15,000+ alumni. 6 training centres across Dubai & Sharjah. ICC-certified coaches. UAE junior cricket coaching for ages 4–19. Enroll today!",
        keywords="best cricket academy UAE, best cricket academy Dubai, UAE junior cricket coaching, junior cricket Dubai, Sharjah junior cricket coaching, cricket academy UAE, cricket coaching UAE, kids cricket UAE, youth cricket academy Dubai, UAE national cricket player pathway",
        canonical="https://www.desertcubs.com/"
    )
    return render_template('index.html', meta=meta, branches=BRANCHES, active_tournament=active_tournament, sponsors=SPONSORS, tours=TOURS)


@app.route('/tours')
def tours():
    meta = seo(
        title="Junior International Cricket Tours UAE | UAE National Cricket Player Pathway | Desert Cubs",
        description="Desert Cubs runs junior international cricket tours to UK, Australia, Sri Lanka & South Africa. Build your child's UAE national cricket player pathway. First UAE academy to tour Australia. 2026 UK tour open!",
        keywords="junior international cricket tour UAE, UAE national cricket player pathway, cricket tour UAE, junior cricket tour Dubai, international cricket UAE, cricket tour UK UAE, UAE cricket development pathway, cricket academy tour",
        canonical="https://www.desertcubs.com/tours"
    )
    return render_template('tours.html', meta=meta, tours=TOURS)


@app.route('/blog')
def blog():
    all_posts = get_blog_posts()
    query = request.args.get('q')
    if query:
        q = query.lower()
        all_posts = [p for p in all_posts if q in p['title'].lower() or q in p.get('description', '').lower()]

    page = request.args.get('page', 1, type=int)
    total_posts = len(all_posts)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE) if total_posts > 0 else 1

    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    current_posts = all_posts[start:end]

    meta = seo(
        title="UAE Junior Cricket Coaching Tips & Blog | Advanced Player Analysis | Desert Cubs",
        description="Expert UAE junior cricket coaching tips, advanced player analysis, UAE summer camp cricket guides, batting & bowling advice from ICC-certified coaches. Desert Cubs Academy blog.",
        keywords="UAE junior cricket coaching, advanced player analysis junior cricket UAE, UAE summer camp cricket, cricket training tips Dubai, junior cricket blog UAE, cricket coaching advice UAE, cricket nutrition UAE",
        canonical="https://www.desertcubs.com/blog"
    )
    return render_template('blog.html', posts=current_posts, meta=meta, current_page=page, total_pages=total_pages, query=query)


@app.route('/blog/<slug>')
def blog_post(slug):
    safe_slug = "".join([c for c in slug if c.isalpha() or c.isdigit() or c in ['-', '_']])
    filepath = os.path.join(BLOG_DIR, f"{safe_slug}.html")

    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use Gemini-generated SEO metadata if N8N embedded it, else fall back to slug
    post_meta = extract_post_meta(content)
    fallback_title = safe_slug[11:].replace('-', ' ').title()
    display_title = post_meta.get('blog_title', fallback_title) if post_meta else fallback_title

    meta = seo(
        title=post_meta.get('seo_title', f"{display_title} | Desert Cubs Cricket Blog") if post_meta else f"{display_title} | Desert Cubs Cricket Blog",
        description=post_meta.get('seo_description', f"Read: {display_title} — Cricket training tips from Desert Cubs Academy UAE.") if post_meta else f"Read: {display_title} — Cricket training tips from Desert Cubs Academy UAE.",
        canonical=f"https://www.desertcubs.com/blog/{slug}",
        og_image=f"https://www.desertcubs.com/static/img/blog/{safe_slug}.jpg"
    )
    return render_template('post.html', content=content, title=display_title, meta=meta, slug=slug)


@app.route('/locations/<branch_id>')
def location_detail(branch_id):
    branch = next((b for b in BRANCHES if b['id'] == branch_id), None)
    if branch is None:
        abort(404)

    clean_area = branch['area'].split('(')[0].strip()
    city = 'Sharjah' if 'Sharjah' in branch['area'] else 'Dubai'
    meta = seo(
        title=f"Best Cricket Academy in {city} | {clean_area} Junior Cricket Coaching | {branch['name']}",
        description=f"Junior cricket training at {branch['name']}, {clean_area}. {branch['desc']} UAE junior cricket coaching for ages 4–19. Enroll at Desert Cubs today.",
        keywords=f"junior cricket coaching {clean_area}, best cricket academy {city}, cricket classes {clean_area}, {clean_area} cricket coaching, {branch['name']} cricket, best cricket ground UAE, UAE junior cricket coaching, cricket training {city}",
        canonical=f"https://www.desertcubs.com/locations/{branch_id}"
    )
    return render_template('location_detail.html', branch=branch, meta=meta)


@app.route('/tournaments')
def tournaments():
    meta = seo(
        title="Most Cricket Tournaments in UAE | Junior International Cricket Tournament | Desert Cubs",
        description="Desert Cubs runs the most cricket tournaments in UAE — 10 competitions per season. DC Premier League, ECB National Junior Tournament, Gulf Cup, 4-Nation Junior International Cricket Tournament & more.",
        keywords="most cricket tournaments UAE, junior cricket tournament UAE, junior international cricket tournament UAE, cricket league Dubai, ECB national junior tournament UAE, Gulf Cup cricket UAE, kids cricket competition UAE, cricket season UAE",
        canonical="https://www.desertcubs.com/tournaments"
    )
    return render_template('tournaments.html', meta=meta, tournaments=TOURNAMENTS)


@app.route('/events')
def events():
    meta = seo(
        title="Cricket Master Classes & Events UAE | Advanced Player Analysis | Desert Cubs Legends Program",
        description="Desert Cubs hosted world cricket legends for advanced player analysis sessions: Jonty Rhodes, Marvan Atapattu, Dinesh Karthik, R. Ashwin, Chaminda Vaas. Best cricket coaching in UAE.",
        keywords="cricket master class UAE, advanced player analysis UAE, cricket legends UAE, Jonty Rhodes Dubai, cricket events Dubai, junior cricket masterclass UAE, best cricket coaching UAE",
        canonical="https://www.desertcubs.com/events"
    )
    return render_template('events.html', meta=meta, master_classes=MASTER_CLASSES, events=EVENTS)


@app.route('/about')
def about():
    meta = seo(
        title="About Desert Cubs Cricket Academy UAE | Founded 2007 | Presley Polonnowita",
        description="Desert Cubs Cricket Academy — UAE's largest junior cricket academy, established 2007 by Presley Polonnowita. 15,000+ alumni, 6 training centres, ECB-affiliated. Meet our executive team and discover our 18-year journey.",
        keywords="Desert Cubs Cricket Academy history, Presley Polonnowita cricket coach UAE, best cricket academy UAE founded 2007, cricket academy Dubai about, GCCA UAE, ECB affiliated cricket academy UAE, Kunal Seth cricket UAE",
        canonical="https://www.desertcubs.com/about",
        og_image="https://www.desertcubs.com/static/img/mgmt_presley.webp"
    )
    return render_template('about.html', meta=meta)


@app.route('/girls-cricket')
def girls_cricket():
    meta = seo(
        title="Girls Cricket Dubai & UAE | Women's Cricket Coaching | Desert Cubs Academy",
        description="Desert Cubs runs UAE's top girls cricket programme. Home of Esha Oza — UAE Women's Cricket Captain. Female ICC-certified coaches. First ECB Women's League winners 2017. Enroll your daughter today.",
        keywords="girls cricket Dubai, girls cricket UAE, women cricket academy UAE, girls cricket coaching Dubai, female cricket UAE, girls cricket Sharjah, Esha Oza UAE women cricket captain, girls cricket classes Dubai, junior girls cricket UAE",
        canonical="https://www.desertcubs.com/girls-cricket",
        og_image="https://www.desertcubs.com/static/img/Desert_cubs_logo.png"
    )
    return render_template('girls_cricket.html', meta=meta)


@app.route('/summer-camp')
def summer_camp():
    meta = seo(
        title="Cricket Summer Camp Dubai 2026 | Holiday Cricket Camp UAE | Desert Cubs",
        description="Desert Cubs cricket summer camps in Dubai 2026. Indoor air-conditioned facility at Baseline Sports Academy, DIP. Ages 4–19. Batting, bowling, fielding & match play. Limited spots — register now!",
        keywords="cricket summer camp Dubai 2026, cricket holiday camp UAE, kids cricket camp Dubai, summer cricket camp Sharjah, indoor cricket camp Dubai, cricket camp UAE ages 4-19, best cricket summer camp Dubai, cricket camp school holidays UAE",
        canonical="https://www.desertcubs.com/summer-camp",
        og_image="https://www.desertcubs.com/static/img/Desert_cubs_logo.png"
    )
    return render_template('summer_camp.html', meta=meta)


# ---------------------------------------------------------
# N8N WEBHOOK ENDPOINTS
# Secure with WEBHOOK_SECRET env var (set X-Webhook-Token header in N8N)
# ---------------------------------------------------------

@app.route('/webhook/update-seo', methods=['POST'])
def webhook_update_seo():
    if not verify_webhook(request):
        abort(403)
    data = request.get_json(silent=True)
    if not data:
        return {'error': 'Invalid JSON'}, 400

    allowed = {'title', 'description', 'keywords'}
    update = {k: v for k, v in data.items() if k in allowed and isinstance(v, str) and v.strip()}
    if not update:
        return {'error': 'No valid fields provided'}, 400

    seo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content', 'seo.json')
    try:
        current = {}
        if os.path.exists(seo_path):
            with open(seo_path, 'r') as f:
                current = json.load(f)
        current.update(update)
        with open(seo_path, 'w') as f:
            json.dump(current, f, indent=2)
        return {'status': 'ok', 'updated': list(update.keys())}
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/webhook/create-blog', methods=['POST'])
def webhook_create_blog():
    if not verify_webhook(request):
        abort(403)
    data = request.get_json(silent=True)
    if not data:
        return {'error': 'Invalid JSON'}, 400

    title = str(data.get('title', '')).strip()
    content = str(data.get('content', '')).strip()
    date = str(data.get('date', datetime.now().strftime('%Y-%m-%d'))).strip()

    if not title or not content:
        return {'error': 'title and content are required'}, 400

    slug_title = re.sub(r'[^a-z0-9\s-]', '', title.lower())
    slug_title = re.sub(r'\s+', '-', slug_title.strip())
    slug_title = re.sub(r'-+', '-', slug_title)[:60].rstrip('-')
    slug = f"{date}_{slug_title}"

    posts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), BLOG_DIR)
    filepath = os.path.join(posts_dir, f"{slug}.html")

    if os.path.exists(filepath):
        return {'error': 'Post already exists', 'slug': slug}, 409

    os.makedirs(posts_dir, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return {'status': 'created', 'slug': slug, 'url': f'/blog/{slug}'}, 201


# ---------------------------------------------------------
# LEGACY REDIRECTS (301) — old website URLs → new structure
# Transfers SEO equity from indexed legacy pages to new pages
# ---------------------------------------------------------
LEGACY_REDIRECTS = {
    '/privacypolicy':    '/blog',
    '/services':         '/events',
    '/contactus':        '/tours',
    '/services-3':       '/locations/sharjah-english-school',
    '/services-4':       '/events',
    '/services-1':       '/tours',
    '/services-4-1-1-2': '/tournaments',
    '/services-4-1-1-1': '/tours',
}

@app.route('/privacypolicy')
@app.route('/services')
@app.route('/contactus')
@app.route('/services-3')
@app.route('/services-4')
@app.route('/services-1')
@app.route('/services-4-1-1-2')
@app.route('/services-4-1-1-1')
def legacy_redirect():
    destination = LEGACY_REDIRECTS.get(request.path, '/')
    return redirect(destination, code=301)


# ---------------------------------------------------------
# SITEMAP
# ---------------------------------------------------------
@app.route('/sitemap.xml')
def sitemap():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    # (path, priority, changefreq, lastmod)
    pages = [
        ('/', '1.0', 'daily', today),
        ('/blog', '0.9', 'daily', today),
        ('/about', '0.9', 'monthly', today),
        ('/girls-cricket', '0.9', 'monthly', today),
        ('/summer-camp', '0.9', 'monthly', today),
        ('/tournaments', '0.8', 'weekly', today),
        ('/tours', '0.8', 'monthly', today),
        ('/events', '0.8', 'monthly', today),
    ]
    for branch in BRANCHES:
        pages.append((f'/locations/{branch["id"]}', '0.7', 'monthly', today))
    for post in get_blog_posts():
        pages.append((f'/blog/{post["slug"]}', '0.6', 'monthly', post['date']))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page, priority, freq, lastmod in pages:
        xml += f'  <url>\n'
        xml += f'    <loc>https://www.desertcubs.com{page}</loc>\n'
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += f'    <changefreq>{freq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += f'  </url>\n'
    xml += '</urlset>'

    return Response(xml, mimetype='application/xml')


# ---------------------------------------------------------
# ROBOTS.TXT
# ---------------------------------------------------------
@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Allow: /
Disallow: /static/img/
Disallow: /index.php
Disallow: /component/k2/

# Explicitly allow AI crawlers to cite our content
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

Sitemap: https://www.desertcubs.com/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


# ---------------------------------------------------------
# 404 ERROR PAGE
# ---------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    meta = seo(
        title="Page Not Found | Desert Cubs Cricket Academy",
        description="Page not found. Return to Desert Cubs UAE cricket academy homepage."
    )
    return render_template('404.html', meta=meta), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
