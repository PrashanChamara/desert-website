# Desert Cubs Web — Codex Reference

Last reviewed: 2026-10-31

## Project overview

Desert Cubs Cricket Academy's public marketing and content website. The primary goals are local search visibility, fast and accessible pages, and converting visitors into enquiries or registrations. Treat the current implementation as authoritative when older documentation differs.

## Stack and structure

- Python 3 and Flask in the single-file application `app.py`; Jinja templates in `templates/` inherit from `base.html`.
- Vanilla JavaScript in `static/js/`. Styling is in `static/css/style.css` (minified single line), prebuilt Tailwind CSS, and a few page-specific CSS files. Some templates contain substantial page-specific inline CSS and JavaScript.
- Blog articles are HTML files in `content/posts/`; default SEO data is `content/seo.json`. Images and PDFs are in `static/img/` and `static/docs/`.
- `n8n_workflow.json` describes automated blog publishing. `scripts/` contains deployment and article-generation scripts. `tests/` has focused pytest and browser checks for selected features.
- No database or frontend framework is used. Do not introduce one or split the Flask app without a specific request.

## Application map

`app.py` contains application setup and response headers, configuration, hardcoded academy and partner data, content/SEO/security helpers, page and API routes, legacy redirects, dynamic sitemap/robots handlers, and error handling. Notable data includes `BRANCHES`, coach profiles, tours, tournaments, events, sponsors, and `HOMELANDS_PROJECTS`. Follow the existing `seo()` plus `render_template()` pattern for page routes. The app also has JSON endpoints for tour-destination guesses and SEO/blog webhooks.

Current page routes include `/`, `/locations/<branch_id>`, `/tours`, `/blog`, `/blog/<slug>`, `/tournaments`, `/events`, `/about`, `/girls-cricket`, `/summer-camp`, `/legends`, `/legends/macneil-noronha`, `/homelands`, and `/homelands/portcity`. Additional endpoints include `/api/next-tour-guess`, webhooks, `/sitemap.xml`, and `/robots.txt`. Check the route decorators in `app.py` for current details and flags; visibility and dates may be controlled dynamically.

Templates include the shared shell (`base.html`), home, blog, branch, events and campaign pages, plus dedicated ECB article and Port City pages. `templates/partials/ses_location.html` and `static/{css,js}/ses-location.*` implement the SES-specific experience. The ECB historical article uses `post_ecb_history.html` with its own stylesheet, script, source content, image manifest/assets, implementation notes, and targeted tests. Inspect these linked files together before modifying either feature.

## Conventions and safeguards

- Python functions and route handlers use `snake_case`; shared/static configuration and data constants use `UPPER_SNAKE_CASE`. Prefer the established structures and minimal, localized edits.
- Templates use Jinja inheritance and blocks. Shared navigation, metadata, schema markup, footer, modals, and global scripts are in `base.html`; changes there can affect every page.
- Preserve SEO metadata, canonical/social tags, JSON-LD, sitemap and robots behavior when changing pages. New page routes should supply route-specific `seo()` metadata and be included in sitemap generation when appropriate.
- Blog files in `content/posts/` are part of the n8n publishing flow. Avoid broad manual edits. Follow the post metadata format and existing helper logic in `app.py` if a specific post change is requested.
- Verify coach, centre, season, tournament, and registration details against current source/code before publishing. Current reference: five active centres (Karama is closed); do not revive expired campaigns or present past tours as open registration.
- Brand palette: blue `#003399`, dark blue `#001f66` (also darker variants), and gold `#FFCC00`; headings use Teko and body/UI use Nunito. Maintain sufficient contrast, especially dark text on gold and white/gold text on dark blue.
- Preserve the established responsive/mobile behavior, accessible labels and image alternatives, image dimensions, and loading priorities. Use optimized local image assets and follow the surrounding page's asset conventions.
- Webhook handlers use `verify_webhook()`. Note: current implementation permits webhook writes when `WEBHOOK_SECRET` is empty; never expose or hardcode secrets, and consider this behavior when changing webhook handling.
- Do not edit deployment settings, production services, or automation-managed data unless the request requires it.

## Local development and verification

Dependencies are listed in `requirements.txt`. The app can be started with `python3 app.py` (inspect the bottom of `app.py` and environment before choosing a production-like run command). Existing focused tests live in `tests/`; inspect their fixtures and scope before running relevant checks. There is no need to add tests unless requested. For code changes, use targeted verification appropriate to the touched area and report exactly what was run.

Deployment is pull-based: `scripts/server_auto_deploy.sh` checks for repository updates and restarts the Gunicorn service on the VPS. Do not deploy or commit/push unless explicitly requested.

## Project instructions

Read `tasks/lessons.md` at the start of each session and apply its rules. After any user correction, append `[YYYY-MM-DD] | what went wrong | rule to follow next time` to that file. Also consult `CLAUDE.md` and `CODEX_PROJECT_REFERENCE.md`; these contain further project and content-specific constraints. Where documentation conflicts, check the current source and ask before publishing facts that cannot be verified.
