#!/usr/bin/env python3
"""tools.dayue.tech: related区 + GA注入"""
import re
from pathlib import Path

BASE = Path(__file__).parent
GA_ID = ""  # 填入GA ID后启用

# 所有文章页的标题和URL
PAGES = []
for d in sorted(BASE.iterdir()):
    if d.is_dir() and not d.name.startswith('.') and d.name not in ('css','images'):
        idx = d / 'index.html'
        if idx.exists():
            t = re.search(r'<title>(.*?)</title>', idx.read_text(encoding='utf-8'))
            title = t.group(1).split('—')[0].strip() if t else d.name
            PAGES.append({'dir':d.name, 'title':title, 'url':f'/{d.name}/'})

# 首页
PAGES.insert(0, {'dir':'/', 'title':'Home', 'url':'/'})

# 按相似分类分组（简单启发式）
def get_cat(dirname):
    if dirname == '/': return 'home'
    cats = {'drill':'Drills','saw':'Saws','grind':'Grinders','impact':'Impact',
            'brushless':'Guides','vs':'Comparison','guide':'Guides','bit':'Bits',
            'battery':'Guides','cordless':'Drills','combo':'Combo Kits','oscillating':'Oscillating',
            'rotary':'Rotary','sander':'Sanders','hammer':'Hammer','screwdriver':'Bits',
            '12v':'Guides','18v':'Guides','20v':'Guides'}
    for k,v in cats.items():
        if k in dirname: return v
    return 'Other'

for p in PAGES:
    if p['dir'] != '/':
        p['cat'] = get_cat(p['dir'])

count = 0
for p in PAGES:
    if p['dir'] == '/': continue
    fpath = BASE / p['dir'] / 'index.html'
    content = fpath.read_text(encoding='utf-8')
    orig = content
    changes = []

    # 1. related区（如果还没有）
    if 'class="related"' not in content and 'class="more-articles"' not in content:
        same_cat = [x for x in PAGES if x.get('cat') == p.get('cat') and x['dir'] != p['dir']]
        # 不够4个就从所有页面补
        others = [x for x in PAGES if x['dir'] != p['dir'] and x not in same_cat]
        related = (same_cat + others)[:4]
        if related:
            rel_html = '\n<div class="related" style="max-width:750px;margin:0 auto;padding:24px;border-top:1px solid #e8e8ea;">\n<p style="font-size:14px;color:#86868b;margin-bottom:12px;">Related articles:</p>\n'
            for r in related:
                rel_html += f'<a href="{r["url"]}" style="display:block;font-size:14px;color:#06c;margin-bottom:6px;text-decoration:none;">→ {r["title"]}</a>\n'
            rel_html += '</div>\n'
            content = content.replace('</article>', rel_html + '</article>')
            changes.append('related')

    # 2. GA
    if GA_ID and f'gtag/js?id={GA_ID}' not in content:
        ga = f"""  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>"""
        content = content.replace('</head>', f'{ga}\n</head>')
        changes.append('GA')
    elif not GA_ID and 'GOOGLE ANALYTICS' not in content:
        if '<!-- GA -->' not in content:
            content = content.replace('</head>', '  <!-- GA: 填入GA ID后启用 -->\n</head>')
            changes.append('GA placeholder')

    if content != orig:
        fpath.write_text(content, encoding='utf-8')
        count += 1
        print(f'  {p["dir"]}: {" + ".join(changes)}')

print(f'\n✅ {count} 篇文章页已更新')
