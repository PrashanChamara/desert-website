from flask import Flask, render_template, request, abort, Response, redirect
from flask_compress import Compress
import os
import math
import json
import re
import hmac
import glob
import time
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
SEASON_REGISTRATION_URL = "https://www.desertcubs-admin.app/kiosk/register?utm_source=desertcubs.com&utm_medium=website&utm_campaign=season_2026_27"
NEXT_TOUR_GUESSES_FILE = os.environ.get(
    'NEXT_TOUR_GUESSES_FILE',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'next_tour_guesses.jsonl')
)
NEXT_TOUR_GUESS_LIMIT = 5
NEXT_TOUR_GUESS_WINDOW = 60 * 60
_next_tour_guess_hits = {}


@app.context_processor
def inject_site_links():
    return {'season_registration_url': SEASON_REGISTRATION_URL}

# ---------------------------------------------------------
# DATA: BRANCH NETWORK
# (5 active centres across Dubai and Sharjah for 2026/27)
# ---------------------------------------------------------
BRANCHES = [
    {
        "id": "sharjah-english-school",
        "name": "Sharjah English School (SES)",
        "area": "Sharjah (Maliha Road)",
        "map_url": "https://maps.app.goo.gl/6SmMmAASK5GRcmwp9",
        "img": "SES_Location.webp",
        "schedule_img": "SES_Schedule.webp",
        "desc": "The crown jewel of our academy. Featuring a full natural grass ground and six natural grass turf center pitches with floodlights. We offer digital scoreboards, live streaming, and a viewing pavilion.",
        "facilities": ["Natural Grass Ground", "6 Center Turf Pitches", "Floodlights", "Video Analysis Room", "Gymnasium", "Digital Scoreboard"],
        "coaches": [
            {"name": "Murali Sockalingam", "role": "Deputy Head Coach", "qual": "ICC Level 3 / ACC Level 2", "img": "coach_murali.webp"},
            {"name": "Aruna Bandaranayaka", "role": "Senior Coach", "qual": "ICC Level 3 / Cricket Aus Level 2", "img": "coach_aruna.webp"},
            {"name": "Vishwa Fernandopulle", "role": "Coach", "qual": "SL Level 1 / Umpire", "img": "coach_vishwa.webp"},
            {"name": "Janaka Senevirathna", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_janaka.webp"},
            {"name": "Shanesh Weerawansha", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_shanesh.webp"}
        ]
    },
    {
        "id": "delhi-private-school",
        "name": "Delhi Private School (DPS)",
        "area": "The Gardens / Jebel Ali, Dubai",
        "map_url": "https://maps.app.goo.gl/sojJP1fK8g18sFsE7",
        "img": "DPS_Location.webp",
        "schedule_img": "DPS_Schedule.webp",
        "desc": "A premium facility in The Gardens. Features a high-quality Astro turf ground with a center pitch and floodlights, perfect for evening high-performance training.",
        "facilities": ["Astro Turf Ground", "Floodlights", "3 Practice Nets", "Bowling Machine", "Pavilion"],
        "coaches": [
            {"name": "Prosanta Chanda", "role": "Centre In-Charge", "qual": "ICC Level 3 / Cricket Aus Level 2", "img": "coach_prosanta.webp"},
            {"name": "Chanaka Ediriweerage", "role": "Coach", "qual": "SL Level 2", "img": "coach_chanaka.webp"},
            {"name": "Judith Jose Peter", "role": "Coach (Girls)", "qual": "ICC Level 1 / Ex-UAE Player", "img": "coach_judith.webp"},
            {"name": "Ruwan Jayakody", "role": "Coach", "qual": "ICC Level 2", "img": "coach_ruwan.webp"}
        ]
    },
    {
        "id": "star-international-school",
        "name": "Star Intl. School (SIS)",
        "area": "Al Qusais 3, Dubai",
        "map_url": "https://g.co/kgs/wnL4YE",
        "img": "SIS_Location.webp",
        "schedule_img": "SIS_Schedule.webp",
        "desc": "A versatile sports hub in Al Qusais. Features an Astro turf ground, six practice nets with floodlights, and access to an indoor pool for cross-training.",
        "facilities": ["Astro Turf Ground", "6 Practice Nets", "Indoor Pool", "Floodlights"],
        "coaches": [
            {"name": "Muhammad Ejaz", "role": "Centre In-Charge", "qual": "ICC Level 1 / PCB Level 1", "img": "coach_ejaz.webp"},
            {"name": "Manish Yadav", "role": "Coach", "qual": "SL Level 2", "img": "coach_manish.webp"},
            {"name": "Nipuna Ratnayake", "role": "Senior Coach", "qual": "ICC Level 2", "img": "coach_nipuna.webp"}
        ]
    },
    {
        "id": "deira-international-school",
        "name": "Deira Intl. School (DIS)",
        "area": "Dubai Festival City, Dubai",
        "map_url": "https://maps.app.goo.gl/uuRBPjNs5UN61Nmw7",
        "img": "DIS_Location.webp",
        "schedule_img": "DIS_Schedule.webp",
        "desc": "Located in Festival City, this centre boasts a natural grass ground and an Astro turf center pitch. Equipped with four side practice nets and modern bowling machines.",
        "facilities": ["Natural Grass Ground", "Astro Center Pitch", "4 Side Nets", "Bowling Machine"],
        "coaches": [
            {"name": "Hashan Silva", "role": "Centre In-Charge", "qual": "ICC Level 1 / Winning Coach U16", "img": "coach_hashan.webp"},
            {"name": "Shahzada Saleem", "role": "Senior Coach", "qual": "ACC Level 3", "img": "coach_shahzada.webp"},
            {"name": "Priyantha Ganegoda", "role": "Coach", "qual": "ICC Level 1", "img": "coach_priyantha.webp"}
        ]
    },
    {
        "id": "baseline-sports-academy",
        "name": "Baseline Sports Academy (BSA)",
        "area": "Dubai Investment Park (DIP), Dubai",
        "map_url": "https://maps.app.goo.gl/K5Azn4sgXpHTkJo8A",
        "img": "BSA_Location.webp",
        "schedule_img": "BSA_Schedule.webp",
        "desc": "State-of-the-art indoor cricket facility — one of a kind in the UAE. Perfect for summer training, equipped with 5 specialized cricket lanes and video analysis technology.",
        "facilities": ["Indoor Facility", "5 Cricket Lanes", "Video Analysis", "AC Controlled", "Year-Round Training"],
        "coaches": [
            {"name": "Manju Abeysekera", "role": "Coach", "qual": "ICC Level 1", "img": "coach_manju.webp"},
            {"name": "Anjalo Silva", "role": "Centre In-Charge", "qual": "SL Level 1", "img": "coach_anjalo.webp"},
            {"name": "Tiran Wijesuriya", "role": "Coach", "qual": "ICC Level 1", "img": "coach_tiran.webp"}
        ]
    },
]

# ---------------------------------------------------------
# DATA: TOURS
# ---------------------------------------------------------
TOURS = {
    "upcoming": [],
    "history": [
        {
            "year": "2026",
            "dest": "United Kingdom",
            "desc": "Siraj Finance Desert Cubs completed an unforgettable UK 2026 cricket tour across England, combining competitive matches, elite exposure, historic venues and a celebration at Heathrow.",
            "gallery": {
                "folder": "DC_UK_2026",
                "prefix": "DC_UK_2026_",
                "count": 12
            }
        },
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
        {"name": "Baseline Sports Academy", "short": "BSA", "location": "DIP, Dubai"},
    ],
    "cricket_bodies": [
        {"name": "Emirates Cricket Board", "role": "Affiliated Academy"},
        {"name": "ICC", "role": "ICC Certified Coaching"},
        {"name": "GCCA", "role": "Gulf Cricket & Cultural Association"},
    ]
}

# ---------------------------------------------------------
# DATA: HOME LANDS SKYLINE PROJECTS
# Gallery images auto-loaded from static/img/homelands/{project_id}/
# Add 1.webp, 2.webp... (up to 10) to a project directory to add gallery images.
# ---------------------------------------------------------
HOMELANDS_PROJECTS = [
    {
        "id": "bayfonte_marina",
        "name": "BayFonte Marina Resort",
        "subtitle": "Sri Lanka's First Luxury Lagoon-Front Resort Living",
        "location": "Negombo Lagoon, Negombo",
        "badge": "Negombo Lagoon",
        "featured": True,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "280 apartments + villas",
        "bedrooms": "2BR & 3BR",
        "price_aed": "From AED 556,000",
        "award": "Best Waterfront Condo Development — PropertyGuru Asia Property Awards 2025",
        "description": "Sri Lanka's first tourist resort-style residential complex on the Negombo Lagoon. BayFonte Marina combines private yacht, jet ski and seaplane facilities with elegant lagoon-facing residences — a lifestyle concept unprecedented in Sri Lanka. Just 7 minutes from Bandaranaike International Airport.",
        "highlights": [
            "Sri Lanka's first lagoon-front resort residential complex",
            "Private yacht, jet ski & seaplane club",
            "7 min from Bandaranaike International Airport",
            "Best Waterfront Condo — PropertyGuru Asia 2025",
            "280 units + marina villas | 7 floors | 392 parking spaces",
        ],
        "also_includes": "Also includes BayFonte Marina Villas — private lagoon-front villa living within the same resort complex.",
    },
    {
        "id": "canterbury_lexus",
        "name": "Canterbury Lexus Golf Resort Apartments",
        "subtitle": "Sri Lanka's First 9-Hole Golf Resort — Part of Canterbury Golf City",
        "location": "Piliyandala, Colombo District",
        "badge": "Piliyandala Golf City",
        "featured": True,
        "img_right": True,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "146 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "From AED 171,000",
        "award": "",
        "description": "Sri Lanka's first-ever Golf Resort Apartments, set within a 9-hole day-and-night golf course inside the 55-acre Canterbury Golf City. Victorian architecture throughout, overlooking lush greens. 20 minutes to Colombo, 5 minutes to Kahathuduwa Southern Expressway interchange. Part of Sri Lanka's largest residential community.",
        "highlights": [
            "Sri Lanka's first Golf Resort Apartments",
            "9-hole day & night golf course within 55-acre Canterbury Golf City",
            "50+ luxury resort amenities including golf training & daycare",
            "2BR from AED 171,000 | 3BR from AED 233,000",
            "Gateway College daycare centre on-site",
        ],
        "also_includes": "Canterbury Golf City also includes Canterbury Crest (Phase 3) and the completed Canterbury Golf Villas — Sri Lanka's first Victorian-style golf resort.",
    },
    {
        "id": "oceana",
        "name": "Oceana Beach Resort",
        "subtitle": "Sri Lanka's First Integrated Luxury Beach Resort Apartments & Villas",
        "location": "Galle Road, Wadduwa",
        "badge": "Wadduwa Beachfront",
        "featured": True,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "321 apartments + 91 villas",
        "bedrooms": "1BR, 2BR & 3BR",
        "price_aed": "From AED 210,000",
        "award": "Sri Lanka's first integrated beach resort apartment complex",
        "description": "Sri Lanka's first luxury beach resort apartments & villas project on 17 acres with 400 metres of pristine Wadduwa beachfront. Buildings occupy only 15% of the land — 85% is open resort zones. 321 apartments and 91 premium Balinese-architecture villas, all with Indian Ocean views. Architect: Philip Weeraratne.",
        "highlights": [
            "400m pristine beachfront on 17 acres",
            "321 apartments + 91 Balinese beach villas",
            "Only 15% built — 85% open resort zones",
            "Apartments from AED 210,000 | 3BR villas available",
            "50+ amenities: beach club, water sports, spa, restaurant",
        ],
        "also_includes": "Oceana Beach Villas offer private Balinese-style villa living within the same 17-acre resort compound.",
    },
    {
        "id": "pentara",
        "name": "Pentara Residencies",
        "subtitle": "The Address in Colombo — Twin Towers Rising 40+ Storeys",
        "location": "Thummulla Handiya, Colombo (bordering Col. 3, 4, 5 & 7)",
        "badge": "Colombo City Centre",
        "featured": True,
        "img_right": True,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "Twin towers, 40+ floors",
        "bedrooms": "2BR, 3BR, Sky Villas, Penthouses & Sky Mansions",
        "price_aed": "On request",
        "award": "Sri Lanka's largest-ever single real estate investment by a Sri Lankan developer",
        "description": "Sri Lanka's most iconic ultra-luxury high-rise twin-tower development. Launched at Cinnamon Life Colombo on 21 June 2025 as 'Signature Night: Beyond the Skyline'. BOI-approved. 75% sales achieved within 5 months of launch. Land valued at Rs. 4.5 Billion. Structural engineer: Prof. Priyan Mendis (Eureka Tower, Melbourne).",
        "highlights": [
            "Sri Lanka's first 5-Star Floating Sky Restaurant",
            "Cantilevered Sky Pool & Sky Bridge at Level 30",
            "Sri Lanka's first Sky Mansions (6,000 sq.ft at Level 41)",
            "BOI approved | 75% sold within 5 months of launch",
            "Bordering Colombo 3, 4, 5 and 7 — most central location",
        ],
        "also_includes": "",
    },
    {
        "id": "waterdale",
        "name": "Waterdale Residencies",
        "subtitle": "Super Luxury High-Rise Bordering Colombo 7 — Borella",
        "location": "Tickle Road, Borella, Colombo 7 Border",
        "badge": "Colombo 7 Border",
        "featured": True,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "204 units",
        "bedrooms": "2BR, 3BR, Penthouses & Duplexes",
        "price_aed": "From AED 897,000",
        "award": "BOI-approved USD 61.56 million project | Completion December 2027",
        "description": "A 26-storey ultra-luxury flagship set on Tickle Road, Borella — bordering the most prestigious Colombo 7 neighbourhood. BOI-approved project valued at USD 61.56 million. LED panel fittings, fire-rated engineering timber doors with smart locks, and 10-year waterproofing warranty. Target completion: December 2027.",
        "highlights": [
            "USD 61.56 million BOI-approved project",
            "26 storeys | 2 exclusive amenity floors",
            "Penthouses to 2,300 sq.ft | Duplexes to 3,600 sq.ft",
            "Infinity pool, spa, rooftop garden, EV charging points",
            "Bordering Colombo 7 — most prestigious address",
        ],
        "also_includes": "",
    },
    {
        "id": "serene_heights",
        "name": "Serene Heights Resort Apartments",
        "subtitle": "Architectural Sanctuary Overlooking Endless Paddy Fields",
        "location": "Thalawathugoda, Sri Lanka",
        "badge": "Thalawathugoda",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "300 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "On request",
        "description": "300 elegantly designed apartments in the serene heart of Thalawathugoda with sweeping paddy field views. 45+ international-standard amenities. Minutes from Colombo and the Outer Circular Expressway.",
        "highlights": [
            "300 units | 7 floors | 45+ amenities",
            "Sweeping paddy field views",
            "Minutes from Colombo & Outer Circular Expressway",
        ],
    },
    {
        "id": "nova",
        "name": "Nova Resort Apartments",
        "subtitle": "Urban Resort Living Across Four Contemporary Towers",
        "location": "Rajagiriya, Colombo",
        "badge": "Rajagiriya",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "224 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "On request",
        "description": "Premium residential development across 4 contemporary towers in Rajagiriya — close to Colombo, Battaramulla, Nawala and Borella. 224 spacious apartments with modern resort-style amenities.",
        "highlights": [
            "224 units across 4 towers | 7 floors each",
            "Swimming pools, gym, sports courts",
            "Central to Colombo's key commercial hubs",
        ],
    },
    {
        "id": "canterbury_crest",
        "name": "Canterbury Crest Resort Apartments",
        "subtitle": "The Final Phase of Canterbury Golf City — Phase 3",
        "location": "Kahathuduwa, Piliyandala",
        "badge": "Canterbury Golf City",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "96 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "On request",
        "description": "The third and final phase of the prestigious Canterbury Golf City development. 96 elegantly designed apartments surrounded by a world-class 9-hole golf course and 55+ Canterbury facilities. Victorian-inspired architecture.",
        "highlights": [
            "96 units | 5 floors | 2 towers",
            "Access to full Canterbury Golf City (55+ facilities)",
            "20 min to Colombo | 5 min to Southern Expressway",
        ],
    },
    {
        "id": "fedora",
        "name": "Fedora Resort Apartments",
        "subtitle": "Your Personal Sanctuary — Resort Living in Athurugiriya",
        "location": "Athurugiriya, Sri Lanka",
        "badge": "Athurugiriya",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "150 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "On request",
        "description": "150 apartments in a serene Athurugiriya setting — 15 minutes to Colombo. Contemporary architecture, spacious interiors, and 50+ resort amenities designed for peace, relaxation, and everyday comfort.",
        "highlights": [
            "150 units | 6 floors | 50+ amenities",
            "Swimming pool, yoga deck, sauna, outdoor gym",
            "15 min to Colombo | Near Southern Expressway",
        ],
    },
    {
        "id": "cressida",
        "name": "Cressida Resort Apartments",
        "subtitle": "Next-Generation Resort Living in Athurugiriya",
        "location": "Athurugiriya, Sri Lanka",
        "badge": "Athurugiriya",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "392 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "From AED 443,000",
        "description": "392 luxury apartments in Athurugiriya with 50+ resort living facilities. Holistic lifestyle emphasising physical, mental and emotional wellbeing. Real estate hot spot with excellent expressway access.",
        "highlights": [
            "392 units | 6 floors | 392 parking spaces",
            "Cricket nets, tennis, basketball, spa, mini market",
            "From AED 443,000 | Easy expressway access",
        ],
    },
    {
        "id": "greendale",
        "name": "Greendale Retirement Resort",
        "subtitle": "Sri Lanka's First International-Standard Retirement Village",
        "location": "Athurugiriya, Sri Lanka",
        "badge": "Senior Living — 50+ Years",
        "featured": False,
        "status": "Under Construction",
        "status_class": "construction",
        "units": "96 apartment suites + 250 cottages",
        "bedrooms": "1BR & 2BR suites | Californian cottages",
        "price_aed": "Suites from AED 134,000",
        "description": "Sri Lanka's first international standard retirement village across 20 acres in Athurugiriya. 250 fully furnished Californian-style luxury cottages and 96 apartment suites, exclusively for senior citizens aged 50+. Designed by architect Philip Weeraratne.",
        "highlights": [
            "250 Californian cottages + 96 apartment suites",
            "Exclusively for 50+ senior citizens",
            "24/7 care, butler service, medical centre on-site",
            "Suites from AED 134,000 | Cottages on request",
        ],
    },
    {
        "id": "santorini",
        "name": "Santorini Resort Apartments",
        "subtitle": "Sri Lanka's First Theme Park-Style Resort — Negombo",
        "location": "Baseline Road, Negombo",
        "badge": "Negombo — Completed",
        "featured": False,
        "status": "Completed",
        "status_class": "completed",
        "units": "240 apartments",
        "bedrooms": "2BR & 3BR",
        "price_aed": "From AED 150,000",
        "award": "Best Completed Condo Development — PropertyGuru Asia Property Awards 2025",
        "description": "Sri Lanka's first Santorini-themed resort apartments — stark white walls with vivid blue architectural details inspired by Greece. 9 theme parks, 50+ luxury facilities, diplomatic zone with butler service. 7 min from Bandaranaike Airport. Launched and opened 2021.",
        "highlights": [
            "9 theme parks within the complex",
            "Best Completed Condo — PropertyGuru Asia 2025",
            "7 min from Bandaranaike International Airport",
            "Apartments from AED 150,000",
        ],
    },
]

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_homelands_gallery(project_id):
    """Scan static/img/homelands/{project_id}/ and return sorted list of image numbers."""
    pattern = os.path.join(os.path.dirname(__file__), 'static', 'img', 'homelands', project_id, '*.webp')
    files = glob.glob(pattern)
    nums = []
    for f in files:
        name = os.path.basename(f).replace('.webp', '')
        if name.isdigit():
            nums.append(int(name))
    return sorted(nums)


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


def sanitize_text(value, max_length):
    value = re.sub(r'\s+', ' ', str(value or '')).strip()
    return value[:max_length]


def normalize_phone(value):
    value = str(value or '').strip()
    has_plus = value.startswith('+')
    digits = re.sub(r'\D', '', value)
    if not 7 <= len(digits) <= 16:
        return ''
    return ('+' if has_plus else '+') + digits


def rate_limited(key):
    now = time.time()
    hits = [ts for ts in _next_tour_guess_hits.get(key, []) if now - ts < NEXT_TOUR_GUESS_WINDOW]
    if len(hits) >= NEXT_TOUR_GUESS_LIMIT:
        _next_tour_guess_hits[key] = hits
        return True
    hits.append(now)
    _next_tour_guess_hits[key] = hits
    return False

def seo(title=None, description=None, keywords=None, canonical=None, og_image=None):
    global_seo = get_global_seo()
    
    return {
        'title': title or global_seo.get('title', 'Desert Cubs Cricket Academy UAE | Junior Cricket Dubai & Sharjah | Est. 2007'),
        'description': description or global_seo.get('description', "UAE's largest junior cricket academy. 15,000+ alumni. 5 training centres across Dubai & Sharjah. Junior players across age-group pathways. Register today!"),
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
        title="Cricket Academy Dubai & Sharjah | 2026/27 Registration | Desert Cubs",
        description="Register for the Desert Cubs 2026/27 junior cricket season starting 05 September 2026. Five cricket coaching centres across Dubai and Sharjah for boys and girls.",
        keywords="best cricket academy UAE, best cricket academy Dubai, UAE junior cricket coaching, junior cricket Dubai, Sharjah junior cricket coaching, cricket academy UAE, cricket coaching UAE, kids cricket UAE, youth cricket academy Dubai, UAE national cricket player pathway",
        canonical="https://www.desertcubs.com/"
    )
    return render_template('index.html', meta=meta, branches=BRANCHES, active_tournament=active_tournament, sponsors=SPONSORS, tours=TOURS, season_registration_url=SEASON_REGISTRATION_URL)


@app.route('/tours')
def tours():
    meta = seo(
        title="UK Tour 2026 Gallery | Junior International Cricket Tours UAE | Desert Cubs",
        description="View the successfully completed Desert Cubs UK Tour 2026 gallery and explore our junior international cricket tour history across UK, Australia, Sri Lanka and South Africa.",
        keywords="junior international cricket tour UAE, UAE national cricket player pathway, cricket tour UAE, junior cricket tour Dubai, international cricket UAE, cricket tour UK UAE, UAE cricket development pathway, cricket academy tour",
        canonical="https://www.desertcubs.com/tours"
    )
    return render_template('tours.html', meta=meta, tours=TOURS)


@app.route('/api/next-tour-guess', methods=['POST'])
def next_tour_guess():
    data = request.get_json(silent=True) or request.form
    ip_key = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    if rate_limited(ip_key):
        return {'ok': False, 'error': 'Too many submissions. Please try again later.'}, 429

    country_name = sanitize_text(data.get('country_name') or data.get('country'), 80)
    country_code = sanitize_text(data.get('country_code'), 2).upper()
    full_name = sanitize_text(data.get('full_name'), 100)
    phone = normalize_phone(data.get('contact_number'))
    comment = sanitize_text(data.get('comment'), 500)

    errors = {}
    if not re.fullmatch(r'[A-Z]{2}', country_code) or len(country_name) < 2:
        errors['country'] = 'Select a valid country.'
    if not 2 <= len(full_name) <= 100 or not re.search(r'[A-Za-z]', full_name):
        errors['full_name'] = 'Enter your full name.'
    if not phone:
        errors['contact_number'] = 'Enter a valid contact number with country code.'
    if not 5 <= len(comment) <= 500:
        errors['comment'] = 'Comment must be 5 to 500 characters.'
    if re.search(r'https?://|www\.', comment, re.IGNORECASE):
        errors['comment'] = 'Links are not allowed in comments.'

    if errors:
        return {'ok': False, 'errors': errors}, 400

    entry = {
        'submitted_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'country_code': country_code,
        'country_name': country_name,
        'full_name': full_name,
        'contact_number': phone,
        'comment': comment,
        'status': 'pending_review',
    }
    try:
        os.makedirs(os.path.dirname(NEXT_TOUR_GUESSES_FILE), exist_ok=True)
        with open(NEXT_TOUR_GUESSES_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=True) + '\n')
    except OSError:
        return {'ok': False, 'error': 'Could not save your submission. Please call the academy team.'}, 500

    return {'ok': True, 'message': 'Thank you. Your tour destination guess has been received.'}, 201


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
        description=f"Junior cricket training at {branch['name']}, {clean_area}. {branch['desc']} UAE junior cricket coaching across structured age-group pathways. Register at Desert Cubs today.",
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
        description="Desert Cubs hosted world cricket legends including Robin Uthappa, Jonty Rhodes, Marvan Atapattu, Dinesh Karthik, R. Ashwin and Chaminda Vaas. Best cricket coaching in UAE.",
        keywords="Robin Uthappa Desert Cubs, cricket master class UAE, advanced player analysis UAE, cricket legends UAE, Jonty Rhodes Dubai, cricket events Dubai, junior cricket masterclass UAE, best cricket coaching UAE",
        canonical="https://www.desertcubs.com/events"
    )
    return render_template('events.html', meta=meta, master_classes=MASTER_CLASSES, events=EVENTS)


@app.route('/about')
def about():
    meta = seo(
        title="About Desert Cubs Cricket Academy UAE | Founded 2007 | Presley Polonnowita",
        description="Desert Cubs Cricket Academy — UAE's largest junior cricket academy, established 2007 by Presley Polonnowita. 15,000+ alumni, 5 training centres, ECB-affiliated. Meet our executive team and discover our journey.",
        keywords="Desert Cubs Cricket Academy history, Presley Polonnowita cricket coach UAE, best cricket academy UAE founded 2007, cricket academy Dubai about, GCCA UAE, ECB affiliated cricket academy UAE, Kunal Seth cricket UAE",
        canonical="https://www.desertcubs.com/about",
        og_image="https://www.desertcubs.com/static/img/mgmt_presley.jpg"
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
        description="Desert Cubs cricket summer camp 2026 for ages 8-16 from 14 July to 23 August at DPS Gardens, BSA DIP and SIS Al Qusais. Packages from AED 150. Register online now!",
        keywords="cricket summer camp Dubai 2026, cricket holiday camp UAE, kids cricket camp Dubai, summer cricket camp Sharjah, DPS Gardens cricket camp, BSA DIP cricket camp, SIS Al Qusais cricket camp, cricket camp UAE ages 8-16, best cricket summer camp Dubai",
        canonical="https://www.desertcubs.com/summer-camp",
        og_image="https://www.desertcubs.com/static/img/Desert_cubs_logo.png"
    )
    return render_template('summer_camp.html', meta=meta)


@app.route('/legends')
def legends():
    meta = seo(
        title="Legends of the Future | Desert Cubs Cricket Academy Alumni | UAE Cricket Stars",
        description="Desert Cubs Cricket Academy alumni who represent UAE nationally and internationally. Macneil Hadley Noronha, Esha Oza, ACC U16 winners, UAE U19 World Cup qualifiers and ECB Women's League champions.",
        keywords="Macneil Noronha Desert Cubs, Macneil Hadley Noronha IPL 2026, Chennai Super Kings Desert Cubs, UAE cricket academy success stories, Desert Cubs alumni achievements, UAE national cricket players academy, cricket academy Dubai results, UAE U19 cricket stars, ACC cricket champions UAE, ECB cricket league champions UAE, Akshat Rai cricket UAE, Mohamed Nafees cricket, Kavisha Kumari world record cricket, Esha Oza Desert Cubs",
        canonical="https://www.desertcubs.com/legends",
        og_image="https://www.desertcubs.com/static/img/macneil-noronha/macneil-csk-flyer.jpg"
    )
    return render_template('legends.html', meta=meta)


@app.route('/legends/macneil-noronha')
def macneil_noronha():
    meta = seo(
        title="Macneil Hadley Noronha | Desert Cubs to Chennai Super Kings IPL 2026",
        description="Macneil Hadley Noronha, Desert Cubs alumnus and Karnataka all-rounder, was selected by Chennai Super Kings as an IPL 2026 replacement player. Read his Desert Cubs journey.",
        keywords="Macneil Noronha, Macneil Hadley Noronha, Macneil Noronha IPL 2026, Macneil Noronha Chennai Super Kings, Macneil Noronha CSK, Desert Cubs IPL player, Desert Cubs Cricket Academy alumni, Dubai cricket academy IPL, UAE cricket academy IPL player, Karnataka all-rounder Macneil Noronha, Chennai Super Kings replacement player 2026",
        canonical="https://www.desertcubs.com/legends/macneil-noronha",
        og_image="https://www.desertcubs.com/static/img/macneil-noronha/macneil-csk-flyer.jpg"
    )
    return render_template('macneil_noronha.html', meta=meta)


@app.route('/homelands')
def homelands():
    meta = seo(
        title="Sri Lanka Property Investment | Desert Cubs × Home Lands Skyline | UAE Exclusive",
        description="Invest in Sri Lanka's finest luxury properties through Desert Cubs' exclusive partnership with Home Lands Skyline — Sri Lanka's #1 developer (23+ years, 3,700+ units). Desert Cubs members get exclusive discounts on BayFonte Marina, Canterbury Golf Resort, Oceana Beach, Pentara Residencies, Waterdale & 10+ more premium projects. UAE-based investors.",
        keywords="Sri Lanka property investment UAE, Home Lands Skyline Dubai, buy apartment Sri Lanka from UAE, best property investment Sri Lanka 2025, Desert Cubs Home Lands partnership, BayFonte Marina Negombo lagoon, Canterbury Golf Resort Piliyandala, Oceana Beach Resort Wadduwa, Pentara Residencies Colombo, Waterdale Colombo 7, Sri Lanka luxury apartments expats, Cressida Athurugiriya, Greendale retirement resort Sri Lanka, Serene Heights Thalawathugoda, Nova Rajagiriya, Fedora Athurugiriya, Santorini Negombo, Canterbury Crest Kahathuduwa, PropertyGuru award winner Sri Lanka developer",
        canonical="https://www.desertcubs.com/homelands",
        og_image="https://www.desertcubs.com/static/img/homelands/homelands_flyer.jpg"
    )
    import copy
    projects = copy.deepcopy(HOMELANDS_PROJECTS)
    for p in projects:
        p['gallery'] = get_homelands_gallery(p['id'])
    return render_template('homelands.html', meta=meta, projects=projects)


@app.route('/homelands/portcity')
def homelands_portcity():
    meta = seo(
        title="Home Lands Port City | The Indian Ocean's Next Wonder | Desert Cubs",
        description="Home Lands Port City is an iconic twin-tower destination and globally inspired resort lifestyle. The future address in South Asia overlooking the park, ocean and skyline.",
        keywords="Home Lands Port City, Indian Ocean next wonder, twin tower destination, resort lifestyle South Asia, Home Lands",
        canonical="https://www.desertcubs.com/homelands/portcity",
        og_image="https://www.desertcubs.com/static/img/homelands/portcity/hero.webp"
    )
    return render_template('portcity.html', meta=meta)


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
        ('/legends', '0.9', 'monthly', today),
        ('/legends/macneil-noronha', '0.9', 'monthly', today),
        ('/homelands', '0.8', 'monthly', today),
        ('/homelands/portcity', '0.8', 'monthly', today),
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
