# ECB Historical Article Implementation Plan

Goal: Integrate the complete supplied historical article into the existing Flask blog, with a cinematic article presentation and verified permanent assets.

Architecture: Keep the dated content/posts HTML convention and /blog/<slug> route. Select an isolated ECB template for the single known article. Preserve the common header/footer, blog sorting, pagination and older posts. Generate semantic article HTML from an archived canonical Markdown source; keep an asset manifest with source hashes and dimensions.

Tech stack: Flask, Jinja, scoped CSS, vanilla JavaScript; offline Pillow/PyMuPDF asset conversion. No new runtime dependencies.

- Inspect repository, complete editorial source, 28 image files and all 17 PDF pages; compare production blog. Complete.
- Add regression tests for metadata, discovery/search/pagination, full source retention, assets, sitemap and schema.
- Build 480/960/1600 WebP event images, full cover and thumbnail, JPEG social crop, transparent player, lossless logos and separate roster images. Preserve canonical text and source mappings.
- Extend metadata reading; add optional card excerpt/image/author fields with existing defaults. Enable custom article via exact slug only.
- Build hero, logo strip, authentic cover, statistics, complete narrative, team breakdown, supported timeline, ceremony photography, distinct event/roster galleries and registration CTA.
- Use native dialog with focus restoration, keyboard navigation, touch swipe and full-size download links; avoid loading full images until requested.
- Verify all content, routes, assets, structured data, six viewport widths, gallery interaction and browser errors. Review diff.
- Delete only the explicitly authorised ECB Blog directory after migration and checks pass. Report local completion and deployment status accurately.

Decisions: Use dated slug 2026-10-10_desert-cubs-17-teams-ecb-national-academy-league-2026-27. Keep JPEG social preview under static/img/ecb-2026-27 to avoid deployment conversion. Preserve pre-existing branding printed into photos. Use 220+ throughout authored additions; preserve equivalent “more than 220” wording in canonical narrative. No UAE-wide record assertion.
