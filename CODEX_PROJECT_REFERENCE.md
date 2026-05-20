# Codex Project Reference

Last updated: 2026-05-20

## Project At A Glance

Desert Cubs is a Flask/Jinja marketing website for a UAE cricket academy. It is intentionally simple: one Python app, Jinja templates, static CSS/JS/assets, file-based blog posts, and no database or frontend build step.

Primary goals: fast rendering, SEO, parent/student lead conversion, and easy VPS hosting.

## Stack

- App: `app.py`
- Templates: `templates/`, extending `templates/base.html`
- Static assets: `static/`
- Blog posts: `content/posts/`
- SEO defaults: `content/seo.json`
- Deployment helper: `scripts/server_auto_deploy.sh`
- Styling: prebuilt `static/css/tailwind.min.css`, custom `static/css/style.css`, and page-local template CSS
- JavaScript: vanilla `static/js/main.js` plus page-local scripts

Run locally:

```bash
python3 app.py
```

Useful checks:

```bash
python3 -m py_compile app.py
node --check static/js/main.js
python3 -m json.tool n8n_workflow.json >/tmp/n8n_check.json
```

## Important Routes

- `/`
- `/locations/<branch_id>`
- `/tours`
- `/blog`
- `/blog/<slug>`
- `/tournaments`
- `/events`
- `/about`
- `/girls-cricket`
- `/summer-camp`
- `/legends`
- `/legends/macneil-noronha`
- `/homelands`
- `/homelands/portcity`
- `/sitemap.xml`
- `/robots.txt`

## Core Design Rules

- Primary blue: `#003399`
- Dark blue: `#001f66` / `#001040` / `#001045`
- Gold: `#FFCC00`
- Headings: `Teko`
- Body/UI: `Nunito`
- Font Awesome is the icon system.
- Keep new pages visually consistent with the existing dark blue and gold premium sports brand.
- Many pages use inline CSS in templates; match the local pattern unless doing a deliberate cleanup.

## Home Lands And Port City

Home Lands is handled by:

- Route: `/homelands`
- Template: `templates/homelands.html`
- Data: `HOMELANDS_PROJECTS` in `app.py`
- Gallery helper: `get_homelands_gallery(project_id)`

Port City Colombo project announcement is handled by:

- Route: `/homelands/portcity`
- Template: `templates/portcity.html`
- Sitemap entry: added in `/sitemap.xml`
- Brochure: `static/docs/port-city-homelands-brochure.pdf`
- Images: `static/img/homelands/portcity/`

Current Port City image set:

```text
static/img/homelands/portcity/banner.webp  1920x1280
static/img/homelands/portcity/1.webp       1600x878
static/img/homelands/portcity/2.webp       1600x876
static/img/homelands/portcity/3.webp       1600x965
static/img/homelands/portcity/4.webp       1600x983
static/img/homelands/portcity/5.webp       1600x978
```

Recommended future image sizes:

- Homelands hero / Port City hero banner: `1920x1280` or `1800x1200` (`3:2`)
- Port City content/gallery images: `1920x1080` or `1600x900` (`16:9`)
- Keep important embedded text away from image edges.

Port City source/staging folder was temporary and has been removed. Do not recreate or deploy a root `Portcity/` folder.

## Production Cautions

- `base.html` owns global SEO, nav, footer, WhatsApp button, modals, and splash screen. Edits there affect the whole site.
- The UK Tour splash screen uses `sessionStorage` key `dcSplash` and auto-disables after July 2026.
- `verify_webhook()` allows webhook writes when `WEBHOOK_SECRET` is empty. Set `WEBHOOK_SECRET` in production.
- Blog content under `content/posts/` is automation-managed; avoid broad manual rewrites.
- `static/css/style.css` is minified into one line, so manual edits may be noisy.
- Trust the current code over older notes if documentation and code disagree.
