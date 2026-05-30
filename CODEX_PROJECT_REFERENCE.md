# Codex Project Reference

Last updated: 2026-05-30

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

## Current Academy Facts

- Public headline count: 15,000+ alumni.
- Active training centres: 5 across Dubai and Sharjah. AIS is closed/inactive and should not be shown as an active branch.
- The expired IPL Guess & Win competition must not be shown on the homepage.
- Robin Uthappa visited Desert Cubs on 23-24 May 2026. The feature lives on `/events#robin-uthappa`, using gallery assets in `static/img/robin-uthappa/`.
- Homepage alumni/hero slideshow includes Esha Oza, Macneil Noronha, and Robin Uthappa. Robin and Macneil slides are clickable.

## Home Lands And Port City

Home Lands is handled by:

- Route: `/homelands`
- Template: `templates/homelands.html`
- Data: `HOMELANDS_PROJECTS` in `app.py`
- Gallery helper: `get_homelands_gallery(project_id)`

Port City project announcement is handled by:

- Route: `/homelands/portcity`
- Template: `templates/portcity.html`
- Sitemap entry: added in `/sitemap.xml`
- Brochure: `static/docs/port-city-homelands-brochure.pdf`
- Images: `static/img/homelands/portcity/`

The Port City page must only use details present in the approved Port City PDF unless the user provides approved replacement copy. Current allowed public copy:

```text
THE INDIAN OCEAN'S NEXT WONDER
An iconic twin-tower destination. A globally inspired resort lifestyle.
The future address in South Asia overlooking the Park, Ocean & Skyline.
Be Among the First to Experience What's Next
A Project by HOME LANDS
TRUST | INNOVATION | EXCELLENCE
Call us +971 55 341 4555 | +971 58 827 4266
```

Do not add Port City unit details, prices, payment plans, dates, floor counts, ownership rules, or investment notes unless they are provided again by the user as approved source material.

Recommended future image sizes when the user supplies new artwork:

- Homelands hero link image: square `1080x1080`
- Port City content/gallery images: square `1080x1080`
- Keep important embedded text away from image edges.

Port City source/staging folder is temporary and should be removed after copying/compressing approved assets. Do not deploy a root `portcity/` or `Portcity/` folder.

## Production Cautions

- `base.html` owns global SEO, nav, footer, WhatsApp button, modals, and splash screen. Edits there affect the whole site.
- The UK Tour splash screen uses `sessionStorage` key `dcSplash` and auto-disables after July 2026.
- `verify_webhook()` allows webhook writes when `WEBHOOK_SECRET` is empty. Set `WEBHOOK_SECRET` in production.
- Blog content under `content/posts/` is automation-managed; avoid broad manual rewrites.
- `static/css/style.css` is minified into one line, so manual edits may be noisy.
- Trust the current code over older notes if documentation and code disagree.
