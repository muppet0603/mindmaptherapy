#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""네이버 블로그 RSS를 읽어 홈의 '교육 현장의 기록' 카드 3개를 갱신한다.

사용법:  python3 tools/update_blog.py [index.html 경로]
바뀐 내용이 없으면 아무것도 하지 않고 종료한다.
"""
import html
import pathlib
import re
import sys
import urllib.request

RSS = "https://rss.blog.naver.com/gloshim.xml"
START = "<!-- BLOG:START -->"
END = "<!-- BLOG:END -->"
COUNT = 3
MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def fetch_posts():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        xml = r.read().decode("utf-8", "replace")

    posts = []
    for item in re.findall(r"(?s)<item>(.*?)</item>", xml)[:COUNT]:
        def field(tag):
            m = re.search(r"(?s)<%s>(.*?)</%s>" % (tag, tag), item)
            if not m:
                return ""
            return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))).strip()

        link = field("link").split("?")[0]
        title = field("title")
        # 예: Thu, 20 Aug 2026 15:57:38 +0900
        m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", field("pubDate"))
        date = "%s.%02d.%02d" % (m.group(3), MONTHS[m.group(2)], int(m.group(1))) if m else ""
        if link and title and date:
            posts.append((date, title, link))
    return posts


def build_block(posts):
    cards = "\n".join(
        '      <a class="post" href="%s" target="_blank" rel="noopener">\n'
        '        <span class="date">%s</span>\n'
        '        <span class="title">%s</span>\n'
        '        <span class="more">블로그에서 읽기 →</span>\n'
        '      </a>' % (link, date, html.escape(title, quote=False))
        for date, title, link in posts)
    return '%s\n    <div class="posts">\n%s\n    </div>\n    %s' % (START, cards, END)


def main():
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    doc = path.read_text(encoding="utf-8")
    if START not in doc or END not in doc:
        print("마커를 찾지 못했습니다. 갱신하지 않습니다.")
        return 0

    try:
        posts = fetch_posts()
    except Exception as e:                     # 네트워크 실패 시 기존 내용 유지
        print("RSS를 읽지 못했습니다: %s" % e)
        return 0
    if len(posts) < COUNT:
        print("글이 %d개뿐이라 갱신하지 않습니다." % len(posts))
        return 0

    old = doc[doc.index(START):doc.index(END) + len(END)]
    new = build_block(posts)
    if old == new:
        print("최신 글이 그대로입니다. 변경 없음.")
        return 0

    path.write_text(doc.replace(old, new, 1), encoding="utf-8")
    print("블로그 카드를 갱신했습니다:")
    for date, title, _ in posts:
        print("  %s  %s" % (date, title[:50]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
