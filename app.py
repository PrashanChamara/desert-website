from flask import Flask, render_template, request, abort
import os
import math
from datetime import datetime

app = Flask(__name__)

# CONFIGURATION
BLOG_DIR = 'content/posts'
POSTS_PER_PAGE = 6

# --- DATA: BRANCH NETWORK ---
BRANCHES = [
    {
        "id": "sharjah-english-school",
        "name": "Sharjah English School (SES)",
        "area": "Sharjah (Maliha Road)",
        "map_url": "https://maps.app.goo.gl/6SmMmAASK5GRcmwp9",
        "img": "SES_Location.jpg",
        "schedule_img": "SES_Schedule.jpg",
        "desc": "The crown jewel of our academy. Featuring a full natural grass ground and six natural grass turf center pitches with floodlights. We offer digital scoreboards, live streaming, and a viewing pavilion.",
        "facilities": ["Natural Grass Ground", "6 Center Turf Pitches", "Floodlights", "Video Analysis Room", "Gymnasium"],
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
        "desc": "Located in Festival City, this centre boasts a natural grass ground and an Astro turf center pitch. It is equipped with four side practice nets and modern bowling machines.",
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
        "name": "Baseline Sports Academy",
        "area": "Dubai Investment Park (DIP)",
        "map_url": "https://maps.app.goo.gl/K5Azn4sgXpHTkJo8A",
        "img": "BSA_Location.jpg",
        "schedule_img": "BSA_Schedule.jpg",
        "desc": "State-of-the-art indoor facility, one of a kind in the UAE. Perfect for summer training, equipped with 5 specialized cricket lanes and video analysis tech.",
        "facilities": ["Indoor Facility", "5 Cricket Lanes", "Video Analysis", "AC Controlled"],
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

# --- DATA: TOURS ---
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
            "desc": "First UAE academy to tour Australia (Brisbane).",
            "gallery": None
        }
    ]
}

# --- NEW DATA: TOURNAMENTS ---
# defined with approximate months for logic
TOURNAMENTS = [
    {"name": "DC Premier League", "month_start": 9, "month_end": 9, "type": "Internal", "desc": "The season opener."},
    {"name": "DC Emerging League", "month_start": 10, "month_end": 10, "type": "Internal", "desc": "For our rising stars."},
    {"name": "ECB National Junior Tournament", "month_start": 10, "month_end": 1, "type": "External", "desc": "UAE National Junior Cricket tournament."},
    {"name": "Gulf Cup", "month_start": 11, "month_end": 1, "type": "External", "desc": "Regional championship."},
    {"name": "DC Winter Cup", "month_start": 11, "month_end": 12, "type": "Internal", "desc": "Holiday season competitive series."},
    {"name": "DC Super League", "month_start": 1, "month_end": 1, "type": "Internal", "desc": "High intensity league."},
    {"name": "DC Ramadan Cup", "month_start": 1, "month_end": 2, "type": "Internal", "desc": "Evening matches under floodlights."},
    {"name": "DC Junior Cups", "month_start": 2, "month_end": 2, "type": "Internal", "desc": "Focus on U10 and U12 development."},
    {"name": "4 Nation Tournament", "month_start": 3, "month_end": 4, "type": "External", "desc": "International academy clash."},
    {"name": "DC Summer Bash", "month_start": 4, "month_end": 5, "type": "Internal", "desc": "End of season celebration."},
]

# --- NEW DATA: MASTER CLASSES ---
MASTER_CLASSES = [
    {
        "legend": "Marvan Atapattu",
        "date": "Sept 2022",
        "desc": "Former Sri Lankan Captain & Coach. Technical batting masterclass.",
        "folder": "master_class",
        "prefix": "marven_atapattu", 
        "count": 10,
        "id": "marvan"
    },
    {
        "legend": "Chaminda Vaas",
        "date": "Feb 2022",
        "desc": "The legend of swing bowling.",
        "folder": None, 
        "count": 0,
        "id": "vaas"
    },
    {
        "legend": "Ravichandran Ashwin",
        "date": "Past Visit",
        "desc": "Spin wizardry and tactical analysis.",
        "folder": None,
        "count": 0,
        "id": "ashwin"
    }
]

# --- NEW DATA: EVENTS ---
EVENTS = [
    {
        "title": "Annual Sports Day 2025",
        "date": "December 2025",
        "desc": "Our biggest annual gathering. Parents vs Coaches, Fun Games, and Talent Shows.",
        "folder": "event",
        "prefix": "dc_sports_day",
        "count": 10,
        "id": "sportsday25"
    }
]

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
    current_month = datetime.now().month
    # Logic to find tournaments active in this month
    active = [t for t in TOURNAMENTS if t['month_start'] <= current_month <= t['month_end']]
    
    # Fallback for display if nothing matches exactly (or if checking across year boundary)
    if not active:
        return TOURNAMENTS[0] # Return the first one or a default
    return active[0]

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route('/')
def index():
    active_tournament = get_active_tournament()
    meta = {
        'title': "Desert Cubs | Legends of the Future",
        'description': "The UAE's largest and most prestigious cricket academy. Est 2007. 15,000+ Alumni."
    }
    return render_template('index.html', meta=meta, branches=BRANCHES, active_tournament=active_tournament)

@app.route('/tours')
def tours():
    meta = {
        'title': "Global Cricket Tours | Desert Cubs",
        'description': "Join our legendary international cricket tours. From Lord's to Melbourne."
    }
    return render_template('tours.html', meta=meta, tours=TOURS)

@app.route('/blog')
def blog():
    all_posts = get_blog_posts()
    query = request.args.get('q')
    if query:
        all_posts = [p for p in all_posts if query.lower() in p['title'].lower()]

    page = request.args.get('page', 1, type=int)
    total_posts = len(all_posts)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE)
    
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    current_posts = all_posts[start:end]

    meta = {
        'title': "Academy Blog | Insights & Nutrition",
        'description': "Expert advice on junior sports development."
    }
    return render_template('blog.html', posts=current_posts, meta=meta, current_page=page, total_pages=total_pages, query=query)

@app.route('/blog/<slug>')
def blog_post(slug):
    safe_slug = "".join([c for c in slug if c.isalpha() or c.isdigit() or c in ['-','_']])
    filepath = os.path.join(BLOG_DIR, f"{safe_slug}.html")
    
    if not os.path.exists(filepath):
        abort(404)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    title = safe_slug[11:].replace('-', ' ').title()
    meta = {'title': title, 'description': f"Read {title}"}
    return render_template('post.html', content=content, title=title, meta=meta, slug=slug)

@app.route('/locations/<branch_id>')
def location_detail(branch_id):
    # Find the branch with the matching ID
    branch = next((b for b in BRANCHES if b['id'] == branch_id), None)
    if branch is None:
        abort(404)
    
    meta = {
        'title': f"Cricket Coaching in {branch['area']} | {branch['name']}",
        'description': f"Join Desert Cubs at {branch['name']}. {branch['desc']}"
    }
    return render_template('location_detail.html', branch=branch, meta=meta)

@app.route('/tournaments')
def tournaments():
    meta = {
        'title': "Tournaments & Fixtures | Desert Cubs",
        'description': "DC Premier League, ECB Tournament, and more."
    }
    return render_template('tournaments.html', meta=meta, tournaments=TOURNAMENTS)

@app.route('/events')
def events():
    meta = {
        'title': "Master Classes & Events | Desert Cubs",
        'description': "Learn from Legends like Marvan Atapattu and join our Annual Sports Day."
    }
    return render_template('events.html', meta=meta, master_classes=MASTER_CLASSES, events=EVENTS)

if __name__ == '__main__':
    app.run(debug=True, port=5000)