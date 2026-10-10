"""One-time migration of the supplied ECB editorial and images (Pillow + PyMuPDF).

Run from the project root before removing ECB Blog/. Generated assets and HTML
are committed production files; this script is not run by the website.
"""
import hashlib
import html
import io
import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ECB Blog'
DEST = ROOT / 'static/img/ecb-2026-27'
SLUG = '2026-10-10_desert-cubs-17-teams-ecb-national-academy-league-2026-27'
manifest = {'assets': [], 'gallery': [], 'rosters': [], 'sources': {}}


def load(path):
    im = ImageOps.exif_transpose(Image.open(path))
    if im.info.get('icc_profile'):
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])), ImageCms.createProfile('sRGB'), outputMode='RGB')
    return im


def save(im, name, width=None, lossless=False):
    im = im.copy()
    if width:
        im.thumbnail((width, width * 4), Image.Resampling.LANCZOS)
    path = DEST / name
    im.save(path, quality=83, method=6, lossless=lossless)
    manifest['assets'].append({'path': str(path.relative_to(ROOT)), 'width': im.width, 'height': im.height, 'bytes': path.stat().st_size})
    return im.size


def picture(stem, alt, cls='', eager=False):
    item = next(a for a in manifest['assets'] if a['path'].endswith(stem + '-960.webp'))
    sizes = '(max-width: 700px) 90vw, 400px' if stem.startswith('roster-') else '(max-width: 700px) 50vw, 400px'
    return (f'<img class="{cls}" src="/static/img/ecb-2026-27/{stem}-960.webp" '
            f'srcset="/static/img/ecb-2026-27/{stem}-480.webp 480w, /static/img/ecb-2026-27/{stem}-960.webp 960w, /static/img/ecb-2026-27/{stem}-1600.webp 1600w" '
            f'sizes="{sizes}" width="{item["width"]}" height="{item["height"]}" '
            f'alt="{html.escape(alt)}" loading="{"eager" if eager else "lazy"}" decoding="async">')


def gallery(items, group):
    result = '<div class="ecb-gallery">'
    for item in items:
        stem, alt = item['stem'], item['alt']
        result += (f'<a class="ecb-gallery__item" data-ecb-gallery="{group}" href="/static/img/ecb-2026-27/{stem}-1600.webp" '
                   f'data-caption="{html.escape(alt)}" aria-label="Enlarge: {html.escape(alt)}">'
                   + picture(stem, alt) + '<span aria-hidden="true">View photograph ↗</span></a>')
    return result + '</div>'


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return re.sub(r'https://[^\s<]+', lambda m: f'<a href="{m[0]}">{m[0]}</a>', text)


def main():
    if not SOURCE.is_dir():
        raise SystemExit('Source folder already migrated; production files require no rebuild.')
    DEST.mkdir(parents=True, exist_ok=True)
    for path in SOURCE.iterdir():
        manifest['sources'][path.name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}

    # Full event frames, including their existing official branding, remain intact.
    for path in sorted(SOURCE.glob('DSC_*.jpg')):
        number = int(path.stem.split('_')[1])
        if not 6943 <= number <= 7514:
            continue
        im = load(path)
        stem = path.stem.lower().replace('_', '-')
        if number in (6943, 6953, 6972):
            alt = f'Speaker on stage at the Desert Cubs ECB capping ceremony — photograph {number}'
        elif number in (7039, 7272, 7514):
            alt = f'Players and attendees in the auditorium at the Desert Cubs capping ceremony — photograph {number}'
        else:
            alt = f'Desert Cubs players and coaches together on stage at the ECB capping ceremony — photograph {number}'
        for width in (480, 960, 1600):
            save(im, f'{stem}-{width}.webp', width)
        manifest['gallery'].append({'source': path.name, 'stem': stem, 'alt': alt})

    cover = load(SOURCE / 'DSC_7538.jpg')
    for width in (480, 960, 1600):
        save(cover, f'ecb-17-teams-cover-{width}.webp', width)
    # Wide crops remove empty stage/foreground, retaining the assembled players.
    thumb = ImageOps.fit(cover, (800, 450), Image.Resampling.LANCZOS, centering=(.5, .56))
    save(thumb, 'ecb-17-teams-cover-800.webp')
    social = ImageOps.fit(cover, (1200, 630), Image.Resampling.LANCZOS, centering=(.5, .56))
    save(social, 'ecb-17-teams-og.webp')
    save(social.convert('RGB'), 'ecb-17-teams-og.jpg')
    save(load(SOURCE / 'player.png'), 'player.webp', 900)
    for source, name in [('Desert_cubs_logo.png', 'desert-cubs'), ('SIRAJ Logo.jpg', 'siraj-finance'), ('ECB.jpg', 'ecb'), ('SLAY Bar+kitchen-001.png', 'slay')]:
        save(load(SOURCE / source), f'logo-{name}.webp', 600, lossless=True)

    # Page identities were read visually from the supplied PDF, not OCR.
    names = [('Girls', 'Roses')] + [(age, name) for age in ('Under 12 Boys', 'Under 15 Boys', 'Under 18 Boys') for name in ('Eagles', 'Lions', 'Ninjas', 'Sharks', 'Warriors')]
    names.append(('Under 18 Boys', 'Wizards'))
    pdf = fitz.open(SOURCE / 'DC ROSES-001.pdf')
    assert len(pdf) == len(names) == 17
    for i, (page, (category, team)) in enumerate(zip(pdf, names), 1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1600 / page.rect.width, 1600 / page.rect.width), alpha=False)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        stem = f'roster-{i:02d}'
        for width in (480, 960, 1600):
            save(im, f'{stem}-{width}.webp', width)
        manifest['rosters'].append({'source': 'DC ROSES-001.pdf', 'page': i, 'category': category, 'team': team, 'stem': stem, 'alt': f'{category} — Desert Cubs {team}: official 2026/27 roster graphic'})

    source = (SOURCE / 'ECB BLOG.txt').read_text(encoding='utf-8')
    archive = ROOT / 'content/sources/ecb-2026-27.md'
    archive.parent.mkdir(exist_ok=True)
    archive.write_text(source, encoding='utf-8')
    metadata = {
        'blog_title': '17 Teams. 220+ Dreams. One Desert Cubs Legacy.',
        'seo_title': 'Desert Cubs Makes History: 17 Teams in ECB National Academy League 2026/27',
        'seo_description': 'Discover how Desert Cubs Cricket Academy is fielding 17 teams and 220+ young cricketers in the ECB National Academy League 2026/27, a milestone in UAE cricket.',
        'category': 'ECB National Academy League', 'author': 'Desert Cubs Cricket Academy',
        'date': '2026-10-10',
        'excerpt': 'From just 11 young cricketers in 2007 to 17 teams and over 220 players in the ECB National Academy League 2026/27. Discover the remarkable Desert Cubs journey.',
        'image': 'ecb-17-teams-cover-800.webp',
        'image_path': 'img/ecb-2026-27/ecb-17-teams-cover-800.webp',
    }
    parts = ['<!-- DC_META: ' + json.dumps(metadata) + ' -->']
    blocks = re.split(r'\n\s*\n', source.strip())
    section = 0
    for block in blocks:
        if block.startswith('# ') or block.startswith('**Published:') or block == '---':
            continue
        if block == '**Explore Desert Cubs:** https://www.desertcubs.com':
            continue
        if block.startswith('## ') or block.startswith('### '):
            if section:
                parts.append('</section>')
            section += 1
            title = block.lstrip('# ')
            parts.append(f'<section class="ecb-prose" id="chapter-{section}"><p class="ecb-eyebrow">Chapter {section:02d}</p><h2>{html.escape(title)}</h2>')
        elif block.startswith('- '):
            parts.append('<ul class="ecb-breakdown">' + ''.join('<li>' + inline(line[2:]) + '</li>' for line in block.splitlines()) + '</ul><p class="ecb-total">Total: 17 official teams</p>')
        else:
            parts.append('<p>' + inline(block) + '</p>')

        if block == '**This milestone was not built overnight. It has been 19 years in the making.**':
            parts.append('<nav class="ecb-inline-links" aria-label="Explore our academy"><a href="/about">Our academy story ↗</a><a href="/#branches">Our five training centres ↗</a></nav>')
        if block == 'And every season provides another chance to improve.':
            milestones = [('2007', 'Desert Cubs established with 11 young cricketers'), ('2017', "ECB Women’s League champions"), ('2017/18', 'ECB Under 17 National Academy League success'), ('2018/19', 'Under 14 National Academy League title'), ('2019/20', 'Under 19 National Academy League title'), ('2026', '17 teams in the national academy league')]
            parts.append('<ol class="ecb-timeline" aria-label="Milestones from the Desert Cubs story">' + ''.join(f'<li><strong>{year}</strong><span>{label}</span></li>' for year, label in milestones) + '</ol>')
        if block == 'It was the beginning of a new one.':
            parts.append('</section><section class="ecb-wide ecb-photo-section" aria-labelledby="ecb-gallery-heading"><p class="ecb-eyebrow">27 September 2026 · Sharjah English School</p><h2 id="ecb-gallery-heading">History in Frames — Our ECB National League Journey</h2><p>Players, coaches and families together for the official capping ceremony. Select a photograph to explore the gallery.</p>' + gallery(manifest['gallery'], 'event') + '</section><section class="ecb-prose">')
        if block == 'And every young cricketer deserves the opportunity to pursue their ambitions.':
            parts.append('<p class="ecb-inline-links"><a href="/girls-cricket">Explore girls’ cricket at Desert Cubs ↗</a></p>')
        if block == '**ONE ACADEMY. ONE BADGE. ONE DESERT CUBS FAMILY.**':
            parts.append('<details class="ecb-rosters"><summary>Meet our 17 teams — official roster graphics</summary><p>Explore the official squad graphics by competition category. Select a graphic to enlarge.</p>')
            for category in ('Under 12 Boys', 'Under 15 Boys', 'Under 18 Boys', 'Girls'):
                parts.append(f'<h3>{category}</h3>' + gallery([r for r in manifest['rosters'] if r['category'] == category], 'roster'))
            parts.append('</details>')
        if block == 'And every season provides another chance to improve.':
            parts.append('<nav class="ecb-inline-links" aria-label="Related cricket stories"><a href="/tournaments">Our tournament calendar ↗</a><a href="/blog/2026-05-12_uk-tour-2026-desert-cubs-home-of-cricket">Our UK tour story ↗</a></nav>')
    parts.append('</section>')
    (ROOT / 'content/posts' / (SLUG + '.html')).write_text('\n'.join(parts) + '\n', encoding='utf-8')
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Generated {len(manifest["gallery"])} gallery photographs, {len(manifest["rosters"])} rosters and {len(manifest["assets"])} image assets.')
    print(f'Total production images: {sum(a["bytes"] for a in manifest["assets"])/1024/1024:.2f} MiB')


if __name__ == '__main__':
    main()
