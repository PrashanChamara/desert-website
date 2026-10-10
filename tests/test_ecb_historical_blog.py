import json
import re
import unittest
from pathlib import Path
from html import unescape

import app as site

SLUG = '2026-10-10_desert-cubs-17-teams-ecb-national-academy-league-2026-27'
URL = '/blog/' + SLUG


class EcbHistoricalBlogTests(unittest.TestCase):
    def setUp(self):
        self.client = site.app.test_client()

    def test_article_in_normal_blog_search_and_sitemap(self):
        posts = site.get_blog_posts()
        self.assertEqual(posts[0]['slug'], SLUG)
        self.assertEqual(sum(p['slug'] == SLUG for p in posts), 1)
        for path in ('/blog', '/blog?q=ECB', '/blog?q=220', '/sitemap.xml'):
            self.assertIn(URL, self.client.get(path).text, path)
        self.assertEqual(self.client.get('/blog?page=2').status_code, 200)

    def test_article_metadata_and_schema(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        markup = response.text
        self.assertEqual(len(re.findall(r'<h1\b', markup)), 1)
        self.assertEqual(re.findall(r'<title>(.*?)</title>', markup), ['Desert Cubs Makes History: 17 Teams in ECB National Academy League 2026/27'])
        self.assertEqual(re.findall(r'<link rel="canonical"\s+href="([^"]+)"', markup), ['https://www.desertcubs.com' + URL])
        self.assertRegex(markup, r'<meta property="og:type"\s+content="article">')
        self.assertRegex(markup, r'<meta name="twitter:card"\s+content="summary_large_image">')
        self.assertRegex(markup, r'<meta property="og:image"\s+content="https://www.desertcubs.com/static/img/ecb-2026-27/ecb-17-teams-og.jpg">')
        schemas = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', markup, re.S)]
        article = next(item for schema in schemas for item in schema.get('@graph', [schema]) if item.get('@type') == 'BlogPosting')
        self.assertEqual(article['datePublished'], '2026-10-10T09:00:00+04:00')
        self.assertEqual(article['inLanguage'], 'en')
        self.assertTrue(article['image'].endswith('.jpg'))
        breadcrumb = next(item for schema in schemas for item in schema.get('@graph', [schema]) if item.get('@type') == 'BreadcrumbList')
        self.assertEqual(breadcrumb['itemListElement'][-1]['item'], 'https://www.desertcubs.com' + URL)
        self.assertEqual([item['position'] for item in breadcrumb['itemListElement']], [1, 2, 3])
        self.assertNotIn('ECB Blog/', markup)

    def test_all_source_paragraphs_retained_and_assets_resolve(self):
        source = Path('content/sources/ecb-2026-27.md')
        self.assertTrue(source.is_file(), 'Canonical editorial archive is missing')
        text = self.client.get(URL).text
        visible = unescape(re.sub('<[^>]+>', '', text))
        visible = ' '.join(visible.split())
        for block in source.read_text().split('\n\n'):
            if block.startswith(('#', '**Published:', '---', '- ')):
                continue
            plain = re.sub(r'\*+', '', block).strip()
            if plain:
                self.assertIn(' '.join(plain.split()), visible, plain[:100])
        manifest = json.loads(Path('static/img/ecb-2026-27/manifest.json').read_text())
        self.assertEqual(len(manifest['gallery']), 21)
        self.assertEqual(len(manifest['rosters']), 17)
        for asset in manifest['assets']:
            with self.client.get('/' + asset['path']) as response:
                self.assertEqual(response.status_code, 200, asset['path'])
        self.assertNotIn('DSC_7538.jpg', [i['source'] for i in manifest['gallery']])
        robots = self.client.get('/robots.txt').text
        self.assertIn('Allow: /static/img/ecb-2026-27/', robots)
