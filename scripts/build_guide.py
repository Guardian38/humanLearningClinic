"""이해 가이드(단원별 본문 조각 + guide.json)를 한 장짜리 HTML로 만든다.

    python build_guide.py guide.json 가이드.html [--subject subject.json]

- 본문 조각(units[].file)이 원본이다. 만든 페이지는 손으로 고치지 않는다(로컬과 게시본이 같은 파일).
- --subject를 주면 개념 id(data-c)와 단원 키가 클리닉 과목 데이터와 맞는지 검사한다.
- 개념 절 지도를 guide.json 옆의 guide_map.json으로 쓴다. 클리닉의 make_subject.py가 이것을 subject.json의 "guide"로 넣으면
  클리닉이 답을 확인한 뒤 그 개념의 가이드 절로 가는 링크를 보여 준다.

guide.json
{
  "title": "선형대수 이해 가이드",
  "kicker": "2026-2 선형대수 · 중간고사 범위",       (선택) 첫 화면 제목 위 한 줄
  "lede": "첫 화면 머리말 (HTML)",
  "key": "la-guide",                                   브라우저 저장 접두사. 과목마다 다르게
  "unitFormat": "Ch.{u}",                              단원 이름표. 클리닉의 unitFormat과 같게
  "url": "https://claude.ai/artifact/…",               (게시 후) 이 가이드의 주소. 클리닉 링크에 쓴다
  "clinic": "https://claude.ai/artifact/…",            (선택) 약점 클리닉 주소. 상단 바에 링크
  "home": "home.html",                                 (선택) 첫 화면 카드 아래에 붙일 조각(개념 연결 지도 등)
  "units": [{"key": "1", "title": "단원 이름", "file": "units/1.html",
             "kicker": "(선택) 교재 장·절", "heading": "(선택) 단원 큰 제목", "intro": "(선택) 단원 머리말 HTML",
             "summary": "(선택) 카드 설명", "labs": "(선택) 카드에 적을 실습 이름들"}]
}

본문 조각 규칙(자세한 것은 references/guide-rules.md)
- 머리(hero)와 목차는 빌드가 붙인다. 조각은 첫 <h2>부터 쓴다.
- 절은 <h2 id="…">. 개념 절에는 data-c="개념id"(여러 개면 공백으로)를 붙인다. h3에도 붙일 수 있다.
- id는 페이지 전체(모든 단원)에서 하나여야 한다. 실습 스크립트는 조각 끝에 인라인 <script>로 쓰고 외부 파일을 불러오지 않는다.
- 코드 블록은 <pre class="code"><code class="language-python">…</code></pre>. 클리닉·요약과 같은 색으로 칠한다.
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "guide_template.html")
sys.path.insert(0, HERE)
from build_summary import shared_parts  # noqa: E402  코드 색 규칙의 원본은 클리닉 템플릿 하나

KEY_OK = re.compile(r"^[\w.-]+$")


class Scan(HTMLParser):
    """조각에서 검사에 필요한 것을 모은다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.heads, self.qs, self.langs, self.ext = [], [], [], set(), []
        self.head = None  # 읽는 중인 h2/h3
        self.q = None     # 읽는 중인 .q
        self.depth = 0    # .q 안의 div 깊이

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        cls = (a.get("class") or "").split()
        if tag in ("h2", "h3"):
            self.head = {"tag": tag, "id": a.get("id"), "c": (a.get("data-c") or "").split(), "text": "", "line": self.getpos()[0]}
        if tag == "script" and a.get("src") or tag == "link" or tag in ("iframe", "img") and re.match(r"https?:", a.get("src") or ""):
            self.ext.append(f"<{tag}> {a.get('src') or a.get('href') or ''}")
        if tag == "code" and any(c.startswith("language-") for c in cls):
            self.langs.add(next(c for c in cls if c.startswith("language-"))[9:].lower())
        if tag == "div":
            if self.q is not None:
                self.depth += 1
                if "a" in cls:
                    self.q["a"] = True
                if "explain" in cls:
                    self.q["explain"] = True
            elif "q" in cls:
                self.q = {"mcq": "mcq" in cls, "id": a.get("data-id"), "answer": a.get("data-answer"), "li": 0, "a": False,
                          "explain": False, "line": self.getpos()[0]}
                self.depth = 1
        if tag == "li" and self.q is not None:
            self.q["li"] += 1

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.head:
            self.heads.append(self.head)
            self.head = None
        if tag == "div" and self.q is not None:
            self.depth -= 1
            if self.depth == 0:
                self.qs.append(self.q)
                self.q = None

    def handle_data(self, data):
        if self.head is not None:
            self.head["text"] += data


def strip_nonmath(s):
    return re.sub(r"<(script|style|pre|code)\b[^>]*>[\s\S]*?</\1>", "", s, flags=re.I)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    subject = None
    if "--subject" in args:
        i = args.index("--subject")
        subject = json.load(open(args[i + 1], encoding="utf-8"))
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    src, out = args
    base = os.path.dirname(os.path.abspath(src))
    g = json.load(open(src, encoding="utf-8"))
    errs, warns = [], []

    for k in ("title", "key", "units"):
        if not g.get(k):
            errs.append(f"guide.json에 {k}가 없습니다")
    if g.get("key") and not KEY_OK.match(g["key"]):
        errs.append("key는 영문·숫자·._-만 씁니다(브라우저 저장 이름)")
    units = g.get("units") or []
    keys = [u.get("key") for u in units]
    if len(set(keys)) != len(keys) or not all(isinstance(k, str) and KEY_OK.match(k) for k in keys):
        errs.append(f"units의 key는 서로 다른 영문·숫자 문자열이어야 합니다: {keys}")
    concepts = (subject or {}).get("concepts") or {}
    if subject is not None:
        sk = set((subject.get("units") or {}).keys())
        if set(keys) - sk:
            warns.append(f"클리닉에 없는 단원 키: {sorted(set(keys) - sk)} (클리닉의 units 키와 같게 쓰면 개념이 같은 단원에 묶입니다)")
        if g.get("unitFormat", "{u}") != subject.get("unitFormat", "{u}"):
            warns.append(f"unitFormat이 클리닉과 다릅니다: 가이드 {g.get('unitFormat')!r}, 클리닉 {subject.get('unitFormat')!r}")
    if errs:
        for e in errs:
            print("오류:", e)
        sys.exit(1)

    fmt = g.get("unitFormat", "{u}")
    all_ids, sections, langs, cmap = {}, [], set(), {}
    for u in units:
        tag = fmt.replace("{u}", u["key"])
        path = os.path.join(base, u.get("file") or "")
        if not u.get("file") or not os.path.isfile(path):
            errs.append(f"{tag}: 본문 조각 파일이 없습니다: {u.get('file')}")
            continue
        if not u.get("title"):
            errs.append(f"{tag}: title이 없습니다")
        body = open(path, encoding="utf-8").read()
        sc = Scan()
        sc.feed(body)
        langs |= sc.langs
        for i in sc.ids:
            if i in all_ids or i in ("home", "cards") or i.startswith("u-"):
                errs.append(f"{tag}: id '{i}'가 겹칩니다({all_ids.get(i, '예약된 이름')}). id는 모든 단원을 통틀어 하나여야 합니다")
            all_ids[i] = tag
        for e in sc.ext:
            errs.append(f"{tag}: 외부 파일을 불러옵니다: {e}. 스크립트는 인라인으로 쓰고, 그림은 SVG나 data URI로 넣습니다")
        if re.search(r"<h1\b", body, re.I):
            warns.append(f"{tag}: <h1>은 빌드가 붙이므로 조각에서는 <h2>부터 씁니다")
        h2 = [h for h in sc.heads if h["tag"] == "h2"]
        if not h2:
            warns.append(f"{tag}: <h2> 절이 없어 목차가 비어 있습니다")
        for h in h2:
            if not h["id"]:
                warns.append(f"{tag}: id 없는 <h2>는 목차에 나오지 않습니다: {h['text'].strip()[:40]}")
        for h in sc.heads:
            for cid in h["c"]:
                if concepts and cid not in concepts:
                    errs.append(f"{tag}: data-c '{cid}'는 클리닉에 없는 개념 id입니다 ({h['text'].strip()[:40]})")
                if not cid.startswith(u["key"] + "."):
                    warns.append(f"{tag}: 개념 '{cid}'가 다른 단원 키로 시작합니다. 개념 id는 <단원 키>.<이름>입니다")
                if cid in cmap:
                    continue  # 처음 나온 절이 그 개념의 본 절
                text = re.sub(r"\s+", " ", h["text"]).strip()
                cmap[cid] = {"label": f"{tag} · {text}", "anchor": f"c-{cid}"}
        qids = [q["id"] for q in sc.qs if q["id"]]
        if len(set(qids)) != len(qids):
            errs.append(f"{tag}: 자가 점검 data-id가 겹칩니다: {sorted({x for x in qids if qids.count(x) > 1})}")
        for q in sc.qs:
            qt = f"{tag} {q['line']}행 문항"
            if not q["id"]:
                warns.append(f"{qt}: data-id가 없으면 순서가 id가 되어, 문항을 끼워 넣을 때 저장된 표시가 어긋납니다")
            if q["mcq"]:
                if not (q["answer"] or "").isdigit() or not 0 <= int(q["answer"]) < q["li"]:
                    errs.append(f"{qt}: data-answer는 보기 인덱스(0부터, 보기 {q['li']}개)여야 합니다")
                if not q["explain"]:
                    warns.append(f"{qt}: 해설(.explain)이 없습니다")
            elif not q["a"]:
                errs.append(f"{qt}: 서술형 문항에 답(.a)이 없습니다")
        if len(re.findall(r"(?<!\\)\$", strip_nonmath(body))) % 2:
            warns.append(f"{tag}: '$' 개수가 홀수라 수식이 깨질 수 있습니다")
        for ref in re.findall(r"G\.\$\(\s*[\"'`]#([\w-]+)", body):
            if ref not in sc.ids:
                warns.append(f"{tag}: 스크립트가 찾는 #{ref}가 이 단원에 없습니다")
        hero = (f'<header class="hero"><div class="kicker">{html.escape(tag)}{(" · " + u["kicker"]) if u.get("kicker") else ""}</div>'
                f'<h1>{u.get("heading") or html.escape(u["title"])}</h1>{("<p>" + u["intro"] + "</p>") if u.get("intro") else ""}</header>')
        sections.append(f'<section class="unit" id="u-{u["key"]}" data-unit="{u["key"]}">\n{hero}\n<nav class="toc"></nav>\n{body.strip()}\n</section>')

    if concepts:
        miss = [c for c in concepts if c not in cmap]
        if miss:
            warns.append(f"가이드에 절이 없는 클리닉 개념 {len(miss)}개(클리닉에서 링크가 나오지 않음): {', '.join(miss)}")
    home = ""
    if g.get("home"):
        hp = os.path.join(base, g["home"])
        if os.path.isfile(hp):
            home = open(hp, encoding="utf-8").read().strip()
        else:
            errs.append(f"home 조각 파일이 없습니다: {g['home']}")
    for w in warns:
        print("경고:", w)
    if errs:
        for e in errs:
            print("오류:", e)
        sys.exit(1)

    sh = shared_parts()
    cfg = {"title": html.escape(g["title"]), "key": g["key"], "unitFormat": fmt, "clinic": g.get("clinic") or "",
           "units": [{"key": u["key"], "title": html.escape(u["title"]), "summary": u.get("summary", ""), "labs": u.get("labs", "")}
                     for u in units]}
    code_js = ""
    if langs:
        code_js = ("<script>\n// 코드 색칠: 클리닉과 같은 규칙(highlight.js + VS Code 색). 불러오지 못하면 색 없이 그대로 둔다\n(() => {\n"
                   + sh["code-js"] + f"\n  const LANGS = {json.dumps(sorted(langs))};\n" + r"""  function paint(c, lang) {
    if (!window.hljs.getLanguage(lang)) return;
    c.innerHTML = window.hljs.highlight(c.textContent, { language: lang, ignoreIllegals: true }).value;
    c.querySelectorAll('.hljs-keyword').forEach(k => { if (CTL_KW.has(k.textContent)) k.classList.add('ctl'); });
    const name = (window.hljs.getLanguage(lang).name || lang).toLowerCase();
    if (!NO_IDENT.has(lang) && !NO_IDENT.has(name)) markIdents(c);
  }
  const load = src => new Promise(res => { const s = document.createElement('script'); s.src = src; s.onload = s.onerror = res; document.head.appendChild(s); });
  load(HLJS + 'highlight.min.js').then(() => {
    if (!window.hljs) return;
    const more = LANGS.filter(l => !window.hljs.getLanguage(l));
    return Promise.all(more.map(l => load(`${HLJS}languages/${l}.min.js`))).then(() => {
      document.querySelectorAll('pre.code code[class*="language-"]').forEach(c => paint(c, c.className.match(/language-([\w+#.-]+)/)[1]));
    });
  });
})();
</script>""")
    page = open(TEMPLATE, encoding="utf-8").read()
    for k, v in {"/*@@CODE_VARS_LIGHT@@*/": sh["code-vars-light"], "/*@@CODE_VARS_DARK@@*/": sh["code-vars-dark"],
                 "/*@@CODE_CSS@@*/": sh["code-css"], "<!--@@CODE_JS@@-->": code_js,
                 "/*@@CONFIG@@*/null": json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"),
                 "@@TITLE@@": html.escape(g["title"]), "@@KICKER@@": html.escape(g.get("kicker", "")), "@@LEDE@@": g.get("lede", ""),
                 "<!--@@HOME@@-->": home, "<!--@@UNITS@@-->": "\n\n".join(sections)}.items():
        page = page.replace(k, v)
    open(out, "w", encoding="utf-8").write(page)

    gmap = {"url": g.get("url") or None, "map": cmap}
    mp = os.path.join(base, "guide_map.json")
    json.dump(gmap, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    labs = len(re.findall(r'class="lab\b', page))
    quiz = len(re.findall(r'class="q\b', page))
    print(f"작성: {out} ({len(page):,}자) · 단원 {len(sections)} · 개념 절 {len(cmap)} · 실습 {labs} · 자가 점검 {quiz}"
          + (f" (색칠 언어: {', '.join(sorted(langs))})" if langs else ""))
    print(f"개념 지도: {mp}" + ("" if g.get("url") else " (url 없음: 게시한 뒤 guide.json에 url을 적고 다시 빌드하면 클리닉 링크가 생깁니다)"))
    if len(page) > 3_000_000:
        print("경고: 페이지가 3MB를 넘습니다. 그림을 줄이세요")


if __name__ == "__main__":
    main()
