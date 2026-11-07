#!/usr/bin/env python3
"""Dependency-free Markdown subset → GitHub Pages. Never emits raw HTML from posts."""
from pathlib import Path
from html import escape
from urllib.parse import urlparse
import datetime, json, re, shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
CFG = json.loads((ROOT / 'site.json').read_text())

def e(text):
    return escape(str(text), quote=True)

def safe_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ('https', 'http', 'mailto') or (url.startswith('/') and not url.startswith('//'))

def inline(text):
    pattern = r'`([^`]+)`|\[([^\]]+)\]\(([^\s)]+)\)'
    result, pos = [], 0
    for m in re.finditer(pattern, text):
        result.append(e(text[pos:m.start()]))
        if m[1] is not None:
            result.append('<code>' + e(m[1]) + '</code>')
        elif safe_url(m[3]):
            result.append(f'<a href="{e(m[3])}">{e(m[2])}</a>')
        else:
            result.append(e(m[0]))
        pos = m.end()
    result.append(e(text[pos:]))
    return ''.join(result)

def markdown(text):
    result, paragraph, code = [], [], []
    in_code, listing = False, None
    def flush():
        if paragraph:
            result.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()
    def close_list():
        nonlocal listing
        if listing:
            result.append(f'</{listing}>')
            listing = None
    for line in text.splitlines():
        if line.startswith('```'):
            flush(); close_list()
            if in_code:
                result.append('<pre><code>' + e('\n'.join(code)) + '</code></pre>'); code=[]
            in_code = not in_code
            continue
        if in_code:
            code.append(line); continue
        if not line.strip():
            flush(); close_list(); continue
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        item = re.match(r'^(?:- |\d+\. )(.+)$', line)
        if heading:
            flush(); close_list()
            level = len(heading[1])
            result.append(f'<h{level}>{inline(heading[2])}</h{level}>')
        elif item:
            flush()
            kind = 'ul' if line.startswith('- ') else 'ol'
            if listing != kind:
                close_list(); listing=kind; result.append(f'<{kind}>')
            result.append('<li>' + inline(item[1]) + '</li>')
        else:
            close_list(); paragraph.append(line.strip())
    flush(); close_list()
    if in_code: raise ValueError('Unclosed code fence')
    return '\n'.join(result)

def page(path, title, desc, body, active=''):
    nav = ''.join(f'<a href="{url}"'+(' aria-current="page"' if active==key else '')+f'>{label}</a>' for key,url,label in [('home','/','首页'),('posts','/posts/','文章'),('projects','/projects/','项目'),('about','/about/','关于')])
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · {e(CFG['title'])}</title><meta name="description" content="{e(desc)}"><meta name="color-scheme" content="dark"><link rel="canonical" href="{e(CFG['url']+path)}"><link rel="stylesheet" href="/assets/style.css"><link rel="icon" href="/favicon.svg" type="image/svg+xml"></head><body><a class="skip" href="#main">跳至正文</a><header><a class="brand" href="/">litterburger<small>开发笔记</small></a><nav aria-label="主导航">{nav}</nav></header><main id="main">{body}</main><footer><span>© 2026 litterburger · 慢慢构建，认真记录。</span><span><a href="{e(CFG['github'])}">GitHub</a> · <a href="/about/">关于这个空间</a></span></footer></body></html>'''
    target = OUT / path.lstrip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT/'assets',OUT/'assets')
    (OUT/'.nojekyll').touch()
    (OUT/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#2f6450"/><text x="32" y="43" text-anchor="middle" fill="#fffef9" font-size="34" font-family="monospace">lb</text></svg>')
    posts=[]
    for source in sorted((ROOT/'content/posts').glob('*.md'),reverse=True):
        text=source.read_text()
        match=re.match(r'^---\n(.*?)\n---\n(.*)',text,re.S)
        if not match: raise ValueError(f'Missing front matter: {source.name}')
        meta=dict(line.split(': ',1) for line in match[1].splitlines())
        for field in ('title','date','summary'):
            if not meta.get(field): raise ValueError(f'Missing {field}: {source.name}')
        datetime.date.fromisoformat(meta['date'])
        if not re.fullmatch(r'[a-z0-9-]+',source.stem): raise ValueError('Use ASCII lowercase slugs')
        meta['url']='/posts/'+source.stem+'/'
        # Title is provided by article header; omit only the initial Markdown H1.
        body=re.sub(r'^\s*# [^\n]+\n','',match[2],count=1)
        page(meta['url'],meta['title'],meta['summary'],f'<article class="prose"><div class="article-head"><a href="/posts/">← 所有文章</a><h1>{e(meta["title"])}</h1><p class="summary">{e(meta["summary"])}</p><div class="meta"><time datetime="{e(meta["date"])}">{e(meta["date"])}</time> · litterburger</div></div>{markdown(body)}</article>','posts')
        posts.append(meta)
    def cards():
        return '<div class="cards">'+''.join(f'<article class="card"><div class="meta"><time datetime="{e(p["date"])}">{e(p["date"])}</time> / 开发笔记</div><h3><a href="{p["url"]}">{e(p["title"])}</a></h3><p>{e(p["summary"])}</p><a class="more" href="{p["url"]}" aria-label="阅读：{e(p["title"])}">阅读笔记 →</a></article>' for p in posts)+'</div>'
    page('/','首页','开发过程、项目说明与值得留下的思考。','''<section class="hero"><div><div class="eyebrow">Independent notes / 开发与项目</div><h1>把想法写下来，<br>把项目做下去。</h1><p class="lead">这里是 litterburger 的开发笔记。记录具体的问题、尝试和选择，也为仍在生长的项目留一份清晰的说明。</p><div class="actions"><a class="button" href="/posts/">翻开开发笔记 ↗</a><a href="/projects/">看看项目</a></div></div><div class="hero-art" aria-hidden="true"><span>{ }</span></div></section><section><div class="section-head"><h2>最近的笔记</h2><a href="/posts/">全部文章 →</a></div>'''+cards()+'''</section><section class="project"><div class="section-head"><h2>正在记录的项目</h2><span class="meta">01 / PROJECT</span></div><div class="card"><span class="tag">安全预览</span><h3>寻源 · 信息收集台</h3><p>从用途、状态到许可边界，先把项目说清楚。</p><a href="/projects/">查看项目说明 →</a></div></section>''','home')
    page('/posts/','文章','开发笔记与项目维护记录。','<div class="page-intro"><div class="eyebrow">Notebook / 文章</div><h1>留下一点上下文。</h1><p class="lead">开发、项目与维护中的小记录。由 Markdown 编写，随实际进展逐步补充。</p></div>'+cards(),'posts')
    project='''# 项目

## 寻源 · 信息收集台

寻源是一个信息收集台项目。目前的加固版处于安全预览阶段，部分浏览器功能禁用，真实外网兼容性仍待验证。

这是一份项目入口说明，不代表功能完整性、性能或生产可用性的承诺。

## 使用与许可边界

- 源码可见，采用自定义许可；不是 MIT 许可，也不是 OSI 认可的开源许可。
- 个人及企业在普通工作中使用免费。
- 售卖原软件、修改版，或提供收费托管、API、软件访问等付费服务，需要事先取得书面付费授权。
- 具体权利义务以软件正式发布时附带的许可文本为准。

## 当前状态

安全预览；浏览器功能与外网兼容性尚需进一步验证。此处暂不提供未经确认的下载地址。
'''
    page('/projects/','项目','寻源信息收集台：当前状态与自定义许可边界。','<article class="prose">'+markdown(project)+'</article>','projects')
    about='''# 关于

这里是 litterburger 的开发笔记，一个记录开发过程和项目的个人空间。

## 这个空间

记录问题与选择，整理项目入口，将已确认的结果和仍待验证的计划区分开。不急着给每个想法下结论，先把值得保留的上下文写下来。

## 站点如何维护

使用静态页面与 Markdown，托管在 GitHub Pages。没有登录、评论系统或第三方统计脚本，也不使用第三方字体与追踪组件。访问仍适用 GitHub 平台自身的隐私政策。

博客站点代码采用 MIT 许可；文章内容和项目软件的许可另行适用，不因站点代码许可而改变。

## 找到我

[GitHub 个人主页](https://github.com/czj44223-cloud)
'''
    contacts=[]
    contact_config=CFG.get('contacts',{})
    emails=contact_config.get('emails',[])
    if contact_config.get('email'):
        emails=[contact_config['email']]+emails
    for email in emails:
        if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',email):
            raise ValueError('Invalid public email')
        contacts.append(f'<li><a href="mailto:{e(email)}">{e(email)}</a></li>')
    youtube=contact_config.get('youtube')
    if youtube:
        if not youtube.startswith('https://www.youtube.com/'):
            raise ValueError('Invalid YouTube URL')
        contacts.append(f'<li><a href="{e(youtube)}">YouTube：{e(urlparse(youtube).path.lstrip("/"))}</a></li>')
    page('/about/','关于','关于 litterburger 的开发笔记与站点维护。','<article class="prose">'+markdown(about)+('<ul class="contact-list">'+''.join(contacts)+'</ul>' if contacts else '')+'</article>','about')
    page('/404/','页面未找到','这个地址暂时没有内容。','<div class="page-intro"><div class="eyebrow">404 / NOT FOUND</div><h1>这一页还没有写下。</h1><p>也许链接已经变更，先回到笔记首页看看。</p><a class="button" href="/">返回首页</a></div>')
    shutil.copyfile(OUT/'404/index.html',OUT/'404.html')
    urls=['/','/posts/','/projects/','/about/']+[p['url'] for p in posts]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(CFG['url']+u)+'</loc></url>' for u in urls)+'</urlset>')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+CFG['url']+'/sitemap.xml\n')
    print(f'Built {len(posts)} posts and 4 main pages → docs/')

if __name__=='__main__': build()
