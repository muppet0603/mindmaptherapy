#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""강의 후기 사이트(review-mindmaptherapy)에서 '홈페이지에 올리기'한 후기를 읽어
홈의 '참여자들이 남긴 말' 맨 앞에 최대 3개를 넣는다. 기존에 손으로 고른 후기는 그대로 둔다.

사용법:  python3 tools/update_reviews.py [index.html 경로]
  - 후기 사이트를 읽지 못하면 아무것도 바꾸지 않는다.
  - 올린 후기가 0개면 자리를 비운다(강사가 내린 후기는 홈페이지에서도 내려간다).
"""
import html
import json
import os
import pathlib
import sys
import urllib.request

API = os.environ.get("REVIEWS_API", "https://review-mindmaptherapy.vercel.app/api/public-reviews")
START = "<!-- REVIEWS:START -->"
END = "<!-- REVIEWS:END -->"
COUNT = 3


def fetch_reviews():
    req = urllib.request.Request(API, headers={"User-Agent": "mindmaptherapy-homepage"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out = []
    for item in data.get("reviews", []):
        text, label = str(item.get("text", "")).strip(), str(item.get("label", "")).strip()
        if text and label:
            out.append((text, label))
    return out[:COUNT]


def build_block(reviews):
    cards = "".join(
        '\n        <div class="voice">\n'
        '          <blockquote>“%s”</blockquote>\n'
        '          <cite>%s</cite>\n'
        '        </div>' % (html.escape(text, quote=False), html.escape(label, quote=False))
        for text, label in reviews)
    return "%s%s\n        %s" % (START, cards, END)


def main():
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    doc = path.read_text(encoding="utf-8")
    if START not in doc or END not in doc:
        print("후기 마커를 찾지 못했습니다. 갱신하지 않습니다.")
        return 0
    try:
        reviews = fetch_reviews()
    except Exception as e:                      # 네트워크 실패 시 기존 내용 유지
        print("후기 사이트를 읽지 못했습니다: %s" % e)
        return 0

    old = doc[doc.index(START):doc.index(END) + len(END)]
    new = build_block(reviews)
    if old == new:
        print("올린 후기가 그대로입니다. 변경 없음.")
        return 0
    path.write_text(doc.replace(old, new, 1), encoding="utf-8")
    print("후기 %d개를 반영했습니다." % len(reviews))
    return 0


if __name__ == "__main__":
    sys.exit(main())
