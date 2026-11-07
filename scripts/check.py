#!/usr/bin/env python3
"""Check rendered pages, internal links, Markdown escaping, and mobile CSS rules."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import build
root=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.urls=[]; self.viewport=False; self.lang=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang')=='zh-CN'
        if tag=='meta' and a.get('name')=='viewport': self.viewport='width=device-width' in a.get('content','')
        for key in ('href','src'):
            if key in a: self.urls.append(a[key])
count=0
for path in (root/'docs').rglob('*.html'):
    parser=Links(); parser.feed(path.read_text())
    assert parser.viewport and parser.lang, path
    for url in parser.urls:
        parsed=urlparse(url)
        if parsed.scheme or parsed.netloc or not parsed.path: continue
        assert parsed.path.startswith('/'), (path,url)
        target=root/'docs'/unquote(parsed.path).lstrip('/')
        if parsed.path.endswith('/'): target=target/'index.html'
        assert target.is_file(), (path,url)
    count+=1
css=(root/'assets/style.css').read_text()
assert '@media(max-width:700px)' in css and 'grid-template-columns:1fr' in css
assert 'prefers-reduced-motion' in css and ':focus-visible' in css
assert '<script>' not in build.markdown('<script>alert(1)</script>')
assert 'href="javascript:' not in build.markdown('[x](javascript:alert)')
assert '<code>&lt;x&gt;</code>' in build.markdown('`<x>`')
assert not list((root/'docs').rglob('*.map'))
print(f'PASS: {count} HTML pages; all internal links/assets; lang + mobile viewport; responsive CSS; safe Markdown escaping')
