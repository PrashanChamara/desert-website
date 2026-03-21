from flask import Flask, render_template, request, abort
import os
import math
from datetime import datetime

app = Flask(__name__)

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BLOG_DIR = 'content/posts'
POSTS_PER_PAGE = 6

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
            {"name": "Vishwa Fernandopulle", "role": "Coach", "qual": "SL Level 1 / Umpire", "img": "coach_vishwa.jpg"}
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
            {"name": "Shahzada Saleem", "role": "Senior Coach", "qual": "ACC Level 3", "img": "coach_shahzada.jpg"}
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
            {"name": "Manish Yadav", "role": "Coach", "qual": "SL Level 2", "img": "coach_manish.jpg"}
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
                clean_title = slug[11:].replace('-', ' ').title()
                posts.append({
                    'title': clean_title,
                    'date': date_part,
                    'slug': slug,
                    'filename': filename,
                    'image': f"{slug}.jpg"
                })
            except:
                continue
    return posts


def get_active_tournament():
    """Returns the tournament currently active based on the current month."""
    current_month = datetime.now().month
    active = [t for t in TOURNAMENTS if t['month_start'] <= current_month <= t['month_end']]
    if not active:
        return TOURNAMENTS[0]
    return active[0]


import json

def get_global_seo():
    try:
        with open('content/seo.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}

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
        canonical="https://www.desertcubs.com/"
    )
    return render_template('index.html', meta=meta, branches=BRANCHES, active_tournament=active_tournament, sponsors=SPONSORS, tours=TOURS)


@app.route('/tours')
def tours():
    meta = seo(
        title="International Cricket Tours | Desert Cubs UAE | UK, Australia, Sri Lanka",
        description="Desert Cubs junior cricket tours — UK, Australia, Sri Lanka, South Africa. First UAE academy to tour Australia. 2026 UK tour registration open now!",
        keywords="cricket tour UAE, junior cricket tour Dubai, international cricket UAE, cricket tour UK UAE, cricket academy tour",
        canonical="https://www.desertcubs.com/tours"
    )
    return render_template('tours.html', meta=meta, tours=TOURS)


@app.route('/blog')
def blog():
    all_posts = get_blog_posts()
    query = request.args.get('q')
    if query:
        all_posts = [p for p in all_posts if query.lower() in p['title'].lower()]

    page = request.args.get('page', 1, type=int)
    total_posts = len(all_posts)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE) if total_posts > 0 else 1

    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    current_posts = all_posts[start:end]

    meta = seo(
        title="Cricket Training Tips & Blog | Desert Cubs Academy UAE",
        description="Expert cricket coaching tips, nutrition advice, and academy news for junior cricketers and parents in the UAE.",
        keywords="junior cricket tips UAE, cricket training advice Dubai, cricket nutrition UAE, academy cricket blog",
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

    title = safe_slug[11:].replace('-', ' ').title()
    meta = seo(
        title=f"{title} | Desert Cubs Cricket Blog",
        description=f"Read: {title} — Cricket training tips and insights from Desert Cubs Academy UAE.",
        canonical=f"https://www.desertcubs.com/blog/{slug}"
    )
    return render_template('post.html', content=content, title=title, meta=meta, slug=slug)


@app.route('/locations/<branch_id>')
def location_detail(branch_id):
    branch = next((b for b in BRANCHES if b['id'] == branch_id), None)
    if branch is None:
        abort(404)

    meta = seo(
        title=f"Cricket Coaching in {branch['area']} | {branch['name']} | Desert Cubs",
        description=f"Junior cricket training at {branch['name']}, {branch['area']}. {branch['desc']} Join Desert Cubs today.",
        keywords=f"cricket coaching {branch['area']}, cricket classes {branch['area']}, {branch['name']} cricket, junior cricket {branch['area']}",
        canonical=f"https://www.desertcubs.com/locations/{branch_id}"
    )
    return render_template('location_detail.html', branch=branch, meta=meta)


@app.route('/tournaments')
def tournaments():
    meta = seo(
        title="Cricket Tournaments & Season Calendar | Desert Cubs UAE",
        description="Desert Cubs tournament schedule: DC Premier League, ECB National Junior Tournament, Gulf Cup, and more. Full season September to June.",
        keywords="junior cricket tournament UAE, cricket league Dubai, ECB tournament UAE, kids cricket competition UAE",
        canonical="https://www.desertcubs.com/tournaments"
    )
    return render_template('tournaments.html', meta=meta, tournaments=TOURNAMENTS)


@app.route('/events')
def events():
    meta = seo(
        title="Cricket Master Classes & Events | Desert Cubs UAE | Legends Program",
        description="Desert Cubs hosted world cricket legends: Jonty Rhodes, Marvan Atapattu, Dinesh Karthik, R. Ashwin, Chaminda Vaas. Learn from the best.",
        keywords="cricket master class UAE, Jonty Rhodes Dubai, cricket legends UAE, cricket events Dubai, junior cricket masterclass",
        canonical="https://www.desertcubs.com/events"
    )
    return render_template('events.html', meta=meta, master_classes=MASTER_CLASSES, events=EVENTS)


# ---------------------------------------------------------
# SITEMAP
# ---------------------------------------------------------
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        ('/', '1.0', 'daily'),
        ('/tournaments', '0.8', 'weekly'),
        ('/tours', '0.8', 'monthly'),
        ('/events', '0.8', 'monthly'),
        ('/blog', '0.9', 'daily'),
    ]
    for branch in BRANCHES:
        pages.append((f'/locations/{branch["id"]}', '0.7', 'monthly'))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page, priority, freq in pages:
        xml += f'  <url>\n'
        xml += f'    <loc>https://www.desertcubs.com{page}</loc>\n'
        xml += f'    <changefreq>{freq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += f'  </url>\n'
    xml += '</urlset>'

    from flask import Response
    return Response(xml, mimetype='application/xml')


# ---------------------------------------------------------
# ROBOTS.TXT
# ---------------------------------------------------------
@app.route('/robots.txt')
def robots():
    from flask import Response
    content = """User-agent: *
Allow: /
Disallow: /static/img/

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
