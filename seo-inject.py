#!/usr/bin/env python3
"""tools.dayue.tech 全站 SEO 批处理注入"""
import os, re, json
from pathlib import Path

BASE_DIR = Path(__file__).parent
SITE_URL = "https://tools.dayue.tech"
# Google Analytics ID - 留空则只加注释占位
GA_ID = ""

def get_pages():
    """返回所有页面列表"""
    pages = []
    # 首页
    pages.append({
        "file": "index.html",
        "url": SITE_URL + "/",
        "type": "home"
    })
    # 文章页 (子目录/index.html)
    for d in sorted(os.listdir(BASE_DIR)):
        idx = BASE_DIR / d / "index.html"
        if idx.exists() and d not in ("css", "images", "node_modules"):
            with open(idx, encoding="utf-8") as f:
                content = f.read()
            m = re.search(r"<title>([^<]+)</title>", content)
            title = m.group(1) if m else d
            pages.append({
                "file": f"{d}/index.html",
                "url": f"{SITE_URL}/{d}/",
                "type": "article",
                "title": title,
                "dir": d
            })
    return pages


def build_jsonld(page):
    """构建 JSON-LD 结构化数据"""
    is_home = page["type"] == "home"
    schemas = []

    # Organization (所有页面)
    schemas.append({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Tool Picks",
        "url": SITE_URL,
        "description": "Honest power tool reviews. Cordless drills, saws, grinders, impact drivers — tested thoroughly, ranked honestly."
    })

    # WebSite (所有页面)
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Tool Picks",
        "url": SITE_URL,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{SITE_URL}/?s={{search_term_string}}",
            "query-input": "required name=search_term_string"
        }
    }
    schemas.append(website)

    # Article (文章页)
    if not is_home:
        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": page.get("title", ""),
            "url": page["url"],
            "mainEntityOfPage": page["url"],
            "publisher": {
                "@type": "Organization",
                "name": "Tool Picks",
                "url": SITE_URL
            }
        }
        schemas.append(article)

    return json.dumps(schemas if len(schemas) > 1 else schemas[0], ensure_ascii=False, indent=2)


def process_page(page):
    """处理单个页面"""
    fpath = BASE_DIR / page["file"]
    if not fpath.exists():
        return f"⚠️  不存在: {page['file']}"

    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = []

    # 1. canonical
    if 'rel="canonical"' not in content:
        canonical = f'<link rel="canonical" href="{page["url"]}">'
        content = content.replace("</title>", f"</title>\n  {canonical}")
        changes.append("canonical")

    # 2. og:image (用现有产品图或通用图)
    if 'property="og:image"' not in content:
        # 优先用页面里的第一张产品图
        img_match = re.search(r'src="([^"]*images/[^"]+\.(?:jpg|png|webp))"', content)
        if img_match:
            img_path = img_match.group(1).lstrip("./")
            if not img_path.startswith("http"):
                img_path = f"{SITE_URL}/{img_path.replace('../', '')}"
        else:
            img_path = f"{SITE_URL}/images/dewalt-dcd805.jpg"
        og_img = f'<meta property="og:image" content="{img_path}">'
        content = content.replace('<meta property="og:type"', f'{og_img}\n<meta property="og:type"')
        if '<meta property="og:type"' not in content:
            content = content.replace("</title>", f'</title>\n  {og_img}')
        changes.append("og:image")

    # 3. JSON-LD
    if 'application/ld+json' not in content:
        ld = build_jsonld(page)
        ld_html = f'<script type="application/ld+json">\n{ld}\n  </script>'
        content = content.replace("</head>", f"  {ld_html}\n</head>")
        changes.append("JSON-LD")

    # 4. 图片 alt 属性补全
    img_pattern = re.compile(r'<img(?![^>]*\salt=)([^>]*?)src="([^"]+)"([^>]*?)>')
    def add_alt(m):
        prefix, src, suffix = m.group(1), m.group(2), m.group(3)
        # 从文件名生成 alt
        fname = os.path.basename(src).replace(".jpg", "").replace(".png", "").replace(".webp", "")
        alt_text = fname.replace("-", " ").replace("_", " ").title()
        return f'<img{prefix}src="{src}"{suffix} alt="{alt_text}">'
    new_content = img_pattern.sub(add_alt, content)
    if new_content != content:
        content = new_content
        changes.append("img-alt")

    # 5. Google Analytics
    if GA_ID and f'gtag/js?id={GA_ID}' not in content:
        ga_code = f"""  <!-- Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_ID}');
  </script>"""
        content = content.replace("</head>", f"{ga_code}\n</head>")
        changes.append("GA")
    elif not GA_ID and "GOOGLE ANALYTICS ID" not in content:
        placeholder = "  <!-- GOOGLE ANALYTICS ID: 填入 GA ID 后启用 -->\n"
        content = content.replace("</head>", f"{placeholder}</head>")

    if content != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ {page['file']}: {' + '.join(changes)}"

    return f"   {page['file']}: 无改动"


def main():
    pages = get_pages()
    print(f"处理 {len(pages)} 个页面...\n")
    for p in pages:
        print(process_page(p))
    print(f"\n=== 完成 ===")


if __name__ == "__main__":
    main()
