"""Optional browser regression: run local Flask on :5017, then execute this file.
Requires Playwright and Chrome; no submissions or production writes are performed.
ECB_QA_BASE_URL and ECB_QA_CHROME can override the local defaults.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('ECB_QA_BASE_URL', 'http://127.0.0.1:5017')
SLUG = '2026-10-10_desert-cubs-17-teams-ecb-national-academy-league-2026-27'
OUT = Path('/tmp/ecb-browser-qa')
OUT.mkdir(exist_ok=True)
errors, failed, checks = [], [], []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=os.environ.get('ECB_QA_CHROME', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(device_scale_factor=1)
    context.route('**/*google-analytics.com/**', lambda route: route.abort())
    context.route('**/*googletagmanager.com/**', lambda route: route.abort())
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: failed.append([response.status, response.url]) if response.status >= 400 and response.url.startswith(BASE) else None)
    for width in (360,390,768,1024,1440,1920):
        page.set_viewport_size({'width':width,'height':1000})
        page.goto(BASE+'/blog/'+SLUG, wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        assert page.locator('h1').count() == 1
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow {width}'
        assert page.locator('.ecb-logos img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth > 0)')
        page.screenshot(path=str(OUT/f'hero-{width}.png'))
        checks.append(f'article width {width}: no overflow; logos loaded')
    for width in (1440,390):
        page.set_viewport_size({'width':width,'height':1000})
        page.goto(BASE+'/blog',wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Blog overflow {width}'
        card=page.locator(f'a[href="/blog/{SLUG}"]').first
        card.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/f'blog-{width}.png'))
        card.locator('xpath=..').screenshot(path=str(OUT/f'card-{width}.png'))
        assert card.locator('img').evaluate('(i)=>i.complete && i.naturalWidth > 0')
        card.click()
        page.wait_for_url('**/blog/'+SLUG)
        checks.append(f'blog width {width}: card loads and opens correct article')
    page.set_viewport_size({'width':1440,'height':1000})
    page.goto(BASE+'/blog/'+SLUG,wait_until='networkidle')
    for selector, label in [('.ecb-cover','cover'),('#chapter-2','reading'),('#chapter-3','teams'),('.ecb-photo-section','gallery'),('.ecb-ending','cta')]:
        page.locator(selector).scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT/f'{label}.png'))
    page.locator('.ecb-rosters summary').click()
    for photo in page.locator('[data-ecb-gallery] img').all():
        photo.scroll_into_view_if_needed()
        photo.evaluate('(i)=>i.decode()')
        assert photo.evaluate('(i)=>i.complete && i.naturalWidth>0')
    checks.append('all 21 event thumbnails and all 17 roster graphics decode successfully')
    roster = page.locator('[data-ecb-gallery="roster"]').first
    roster.click()
    assert page.locator('dialog').evaluate('(d)=>d.open')
    assert page.locator('#ecb-lightbox-count').inner_text() == '1 / 17'
    page.keyboard.press('Escape')
    assert roster.evaluate('(a)=>document.activeElement===a')
    event=page.locator('[data-ecb-gallery="event"]').first
    event.click()
    assert page.locator('#ecb-lightbox-count').inner_text() == '1 / 21'
    page.keyboard.press('ArrowRight')
    assert page.locator('#ecb-lightbox-count').inner_text() == '2 / 21'
    page.keyboard.press('ArrowLeft')
    assert page.locator('#ecb-lightbox-count').inner_text() == '1 / 21'
    page.locator('[data-ecb-prev]').click()
    assert page.locator('#ecb-lightbox-count').inner_text() == '21 / 21'
    page.screenshot(path=str(OUT/'lightbox.png'))
    page.keyboard.press('Escape')
    assert not page.locator('dialog').evaluate('(d)=>d.open')
    assert event.evaluate('(a)=>document.activeElement===a')
    checks.append('event and roster gallery: open, arrows, wrap, Escape, return focus pass')
    page.set_viewport_size({'width':390,'height':844})
    event.click()
    page.locator('.ecb-lightbox__stage').dispatch_event('touchstart',{'changedTouches':[{'identifier':0,'clientX':300,'clientY':200}]})
    page.locator('.ecb-lightbox__stage').dispatch_event('touchend',{'changedTouches':[{'identifier':0,'clientX':100,'clientY':210}]})
    assert page.locator('#ecb-lightbox-count').inner_text() == '2 / 21'
    page.locator('.ecb-lightbox__stage').dispatch_event('touchstart',{'changedTouches':[{'identifier':0,'clientX':300,'clientY':200}]})
    page.locator('.ecb-lightbox__stage').dispatch_event('touchend',{'changedTouches':[{'identifier':0,'clientX':220,'clientY':400}]})
    assert page.locator('#ecb-lightbox-count').inner_text() == '2 / 21'
    page.screenshot(path=str(OUT/'lightbox-mobile.png'))
    page.locator('[data-ecb-close]').click()
    checks.append('mobile swipe changes photograph; close button works')
    page.locator('#mobileMenuBtn').click()
    assert page.locator('#mobileMenu').is_visible()
    page.locator('#mobileMenuBtn').click()
    assert not page.locator('#mobileMenu').is_visible()
    checks.append('mobile navigation opens and closes')
    for selector,label in [('.ecb-photo-section','gallery-mobile'),('.ecb-ending','cta-mobile')]:
        page.locator(selector).scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT/f'{label}.png'))
    page.goto(BASE+'/blog?q=ECB',wait_until='networkidle')
    assert page.locator(f'article:has(a[href="/blog/{SLUG}"])').count() == 1
    page.goto(BASE+'/blog?page=2',wait_until='networkidle')
    assert page.locator('h1').count() == 1
    checks.append('search and pagination pass')
    for route in ('/', '/tours', '/tournaments', '/girls-cricket', '/blog/2026-05-12_uk-tour-2026-desert-cubs-home-of-cricket'):
        response = page.goto(BASE+route,wait_until='domcontentloaded')
        assert response.status == 200, route
    checks.append('homepage, tours, tournaments, girls coaching and older blog route return 200')
    print(json.dumps({'checks':checks,'page_errors':errors,'local_http_errors':failed,'screenshots':str(OUT)},indent=2))
    assert not errors and not failed
    browser.close()

