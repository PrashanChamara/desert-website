# Codex Project Reference

Last reviewed: 2026-05-16

## Project Summary

Desert Cubs is an SEO-first Flask/Jinja marketing site for a UAE cricket academy. The site is intentionally simple: one Python app, hardcoded page data, Jinja templates, static CSS/JS, file-based blog posts, and an n8n/GitHub automation path for weekly SEO content.

Primary goals are local SEO, parent/student lead conversion, fast rendering, and easy VPS deployment.

## Current Stack

- Backend: Flask in `app.py`
- Compression: `Flask-Compress`
- Templates: Jinja2 in `templates/`, all extending `templates/base.html`
- Styling: prebuilt `static/css/tailwind.min.css` plus custom `static/css/style.css`
- JavaScript: vanilla JS in `static/js/main.js` plus page-local scripts in templates
- Content: static HTML blog files in `content/posts/`
- SEO config: `content/seo.json`
- Automation: `n8n_workflow.json`
- Deployment helper: `scripts/server_auto_deploy.sh`

There is no Node app, no frontend build pipeline in this repo, no database, and no test framework.

## Top-Level Structure

```text
app.py
requirements.txt
CLAUDE.md
CODEX_PROJECT_REFERENCE.md
n8n_workflow.json
scripts/server_auto_deploy.sh
content/
  seo.json
  posts/
templates/
  base.html
  index.html
  blog.html
  post.html
  location_detail.html
  tours.html
  tournaments.html
  events.html
  about.html
  girls_cricket.html
  summer_camp.html
  legends.html
  homelands.html
  404.html
static/
  css/
  js/
  img/
  docs/
  video/
```

## Backend Shape

`app.py` is a single-file Flask app. Keep additions consistent with that unless the user explicitly asks for a larger refactor.

Main sections:

- Performance/security response headers in `add_performance_headers()`
- Hardcoded data constants:
  - `BRANCHES`
  - `TOURS`
  - `TOURNAMENTS`
  - `MASTER_CLASSES`
  - `EVENTS`
  - `SPONSORS`
  - `HOMELANDS_PROJECTS`
- Helpers:
  - `get_homelands_gallery(project_id)`
  - `extract_post_meta(content)`
  - `get_blog_posts()`
  - `get_active_tournament()`
  - `get_global_seo()`
  - `verify_webhook(req)`
  - `seo(...)`
- Public routes:
  - `/`
  - `/tours`
  - `/blog`
  - `/blog/<slug>`
  - `/locations/<branch_id>`
  - `/tournaments`
  - `/events`
  - `/about`
  - `/girls-cricket`
  - `/summer-camp`
  - `/legends`
  - `/legends/macneil-noronha`
  - `/homelands`
  - `/sitemap.xml`
  - `/robots.txt`
- Webhooks:
  - `POST /webhook/update-seo`
  - `POST /webhook/create-blog`
- Legacy redirects:
  - `/privacypolicy`, `/services`, `/contactus`, and several old `/services-*` URLs

## Frontend And Design

`base.html` owns the global SEO tags, schema JSON-LD, top contact bar, fixed nav, mobile menu, sponsors section, footer, WhatsApp floating button, reusable gallery/photo/schedule modals, and shared scripts.

Brand rules currently used across the site:

- Primary blue: `#003399`
- Dark blue: `#001f66` and `#001045`
- Gold: `#FFCC00`
- Gold hover/darker: `#e6b800`
- Light background: `#f8fafc`
- Body text: `#0f172a`, `#374151`, `#475569`
- Headings use `Teko`
- Body/UI text uses `Nunito`

Common UI patterns:

- Dark blue sections use white/gold text.
- White or grey sections use dark blue headings and dark grey body text.
- Gold CTAs use dark blue text.
- Buttons are usually pill-shaped and uppercase.
- Most major pages include large inline CSS blocks for page-specific responsive layouts and animations.
- Font Awesome is the icon source.

Important global behavior:

- UK Tour 2026 splash screen in `base.html`, using `sessionStorage` and auto-disabling after July 2026.
- Mobile menu toggled by inline script in `base.html`.
- Reusable gallery modal uses global `openGallery(folder, prefix, count)`.
- Coach/photo modal uses `openModal(src, caption)`.
- Schedule modal uses `openSchedule(src, name)`.
- `static/js/main.js` handles counters, fade-in animation, anchor scrolling, active nav links, lazy `data-src` images, clipboard helper, and image fallbacks.

## Page Features

- Homepage (`index.html`): hero, registration CTAs, IPL prediction modal, trust stats, locations, features, tours, testimonials, FAQ, sponsors.
- Blog listing (`blog.html`): search by query, pagination, article cards, topic links.
- Blog post (`post.html`): article schema, hero banner, rendered HTML body, share buttons, CTA cards.
- Location detail (`location_detail.html`): branch data, schedule modal, coach cards/photo modal.
- Tours (`tours.html`): upcoming UK 2026 registration/PDF and historical tour galleries.
- Tournaments (`tournaments.html`): season calendar with client-side internal/external filters.
- Events (`events.html`): master classes and event galleries.
- Girls cricket, summer camp, legends, about: SEO landing pages with extra JSON-LD.
- Macneil Noronha (`macneil_noronha.html`): dedicated SEO profile for Macneil Hadley Noronha, Desert Cubs alumnus selected by Chennai Super Kings for IPL 2026.
- Homelands (`homelands.html`): property investment landing page with project data and auto-scanned galleries.

## Blog And SEO System

Blog file naming:

```text
content/posts/YYYY-MM-DD_slug-title.html
```

Blog metadata is expected as a first-line HTML comment:

```html
<!-- DC_META: {"seo_title":"...","seo_description":"...","blog_title":"...","category":"..."} -->
```

`get_blog_posts()` reads the first 512 bytes of each post to extract this metadata. If metadata is missing, titles fall back to the slug.

`seo()` builds the `meta` dict used by `base.html`. It falls back to `content/seo.json` for defaults.

`/sitemap.xml` is generated dynamically from static routes, branch routes, and blog posts.

Do not remove the JSON-LD in `base.html` or page-specific `extra_head` blocks without replacing it intentionally.

## Automation And Deployment

`n8n_workflow.json` describes a weekly Monday 06:00 workflow:

1. Build SEO/blog prompt.
2. Call Gemini 2.5 Flash.
3. Parse JSON response.
4. Generate a blog image through Pollinations.
5. Commit blog HTML, image, and `content/seo.json` updates to GitHub.

The workflow file currently has `"active": false` in the exported JSON.

`scripts/server_auto_deploy.sh` is designed for the server, not local development. It:

1. Fetches `origin/main`.
2. Pulls if remote changed.
3. Converts new blog JPG images to WebP and deletes the JPG.
4. Installs Python requirements.
5. Restarts `gunicorn-desertcubs` with systemd.

## Local Development

Install dependencies if needed:

```bash
python3 -m pip install -r requirements.txt
```

Run locally:

```bash
python3 app.py
```

The Flask dev server runs on port `5000` by default.

For production-like serving:

```bash
gunicorn app:app
```

Useful checks before larger edits:

```bash
python3 -m py_compile app.py
node --check static/js/main.js
python3 -m json.tool n8n_workflow.json >/tmp/n8n_check.json
```

## Development Cautions

- The current code and `CLAUDE.md` are not perfectly aligned. Trust the code first.
- Current active venue data in `app.py` is 5 visible centres plus `apple-international-school` marked inactive. Some copy still says 6 centres.
- Many templates use inline styles/scripts. Match local style unless doing a specific cleanup.
- `static/css/style.css` is minified into one line and has no trailing newline, so small CSS changes may be noisy if manually edited.
- `base.html` contains very large global responsibilities. Edits there have site-wide impact.
- `post.html` uses a `.jpg` background for article heroes, while listing cards prefer `.webp` through `<picture>`. The deploy script can delete blog JPGs after WebP conversion, so blog image handling needs care before changing automation.
- Macneil Noronha source images live in optimized WebP form under `static/img/macneil-noronha/`. The original root `MACNEIL NORONHA/` staging folder was removed after copying and conversion.
- `verify_webhook()` allows webhook writes when `WEBHOOK_SECRET` is empty. This is convenient locally but should be configured in production.
- Blog content under `content/posts/` is automation-managed. Avoid manual content rewrites unless fixing a clear issue.
- If adding new Tailwind utility classes that are not already in `tailwind.min.css`, verify the class exists or regenerate the static Tailwind file outside this repo's normal flow.
