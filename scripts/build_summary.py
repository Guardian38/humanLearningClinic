"""과목 요약본(요약.md)을 공부용 HTML 페이지로 만든다.

요약.md가 원본이다. 이 페이지는 훑어보기용으로 md에서 만들기만 하고 손으로 고치지 않는다.

    python build_summary.py 요약.md 요약.html

쓸 수 있는 md 문법 (이 밖의 문법은 글자 그대로 나온다)
- `# 제목` 한 번(페이지 이름), 바로 다음 문단은 머리말
- `## 큰 절`(주차 등, 목차에 나옴), `### 항목`(검색·필터의 단위, 목차에서 큰 절 아래에 나옴)
- 문단, `- ` 목록과 `1. ` 번호 목록(2칸 들여쓰기로 한 단계 중첩), `> ` 인용(슬라이드 원문 정의), `| 표 |`
- 코드 블록: ```로 시작하고 ```로 닫는다. 안의 줄은 들여쓰기까지 그대로 나온다.
  여는 줄에 언어 이름(```python)을 붙이면 클리닉과 같은 색(VS Code Light+/Dark+)으로 칠한다. 언어가 없으면 칠하지 않는다(가상코드 등).
- 글 안: `**굵게**`, `*기울임*`, `` `코드` ``, `[p33]`·`[p10, p39]`·`[4주차 p33]`·`[2-2 p7~14]`(쪽수 근거), `★`(시험 강조)

코드 색 규칙(색 변수, 토큰 CSS, 이름 색 보정 JS)은 클리닉 템플릿의 @@shared 구간을 읽어 넣는다. 원본은 템플릿 하나다.
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "clinic_template.html")
REF = re.compile(r"\[((?:\d+-\d+ |\d+주차 )?p\d+(?:[~–-]\d+)?(?:, ?(?:\d+주차 )?p\d+(?:[~–-]\d+)?)*)\]")


def shared_parts():
    """클리닉 템플릿에서 코드 색 규칙(@@shared 구간)을 읽는다."""
    tpl = open(TEMPLATE, encoding="utf-8").read()
    parts = {}
    for m in re.finditer(r"(?:/\*|//) @@shared:([\w-]+)[^\n]*\n(.*?)\n[ \t]*(?:/\* @@end \*/|// @@end)", tpl, re.S):
        parts[m.group(1)] = m.group(2)
    need = {"code-vars-light", "code-vars-dark", "code-css", "code-js"}
    if need - parts.keys():
        sys.exit(f"오류: 클리닉 템플릿에서 코드 색 구간을 찾지 못했습니다: {sorted(need - parts.keys())}")
    return parts


def inline(s):
    s = html.escape(s, quote=False)
    # 코드 조각은 빼 두었다가 마지막에 넣는다(안의 `*`, `[p1]`을 서식으로 읽지 않게)
    codes = []
    s = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\0{len(codes) - 1}\0", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", s)
    s = REF.sub(r'<span class="ref">\1</span>', s)
    s = re.sub(r"\0(\d+)\0", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s.replace("★", '<span class="star" title="시험에 꼭 나온다고 공지되었거나 교수님이 강조한 것">★</span>')


def plain(s):
    return re.sub(r"<[^>]+>", "", inline(s))


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md):
    lines = md.replace("\r\n", "\n").split("\n")
    title, lede, out, toc = "", "", [], []  # toc: [(절 id, 제목, [(항목 id, 제목)])]
    sec = item = 0
    open_sec = open_item = False
    para, quote, table, lists = [], [], [], []  # lists: [(태그, 들여쓰기)]
    code, code_lang = None, ""  # 코드 블록 안이면 줄 목록
    langs = set()

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_quote():
        if quote:
            out.append('<blockquote class="def">' + "<br>".join(inline(q) for q in quote) + "</blockquote>")
            quote.clear()

    def flush_table():
        if table:
            rows = [cells(r) for r in table if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
            head, body = rows[0], rows[1:]
            h = "".join(f"<th>{inline(c)}</th>" for c in head)
            b = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            table.clear()

    def close_lists(to=-1):
        while lists and lists[-1][1] > to:
            out.append(f"</li></{lists.pop()[0]}>")

    def flush_all():
        flush_para(); flush_quote(); flush_table(); close_lists()

    def close_item():
        nonlocal open_item
        if open_item:
            out.append("</div>")
            open_item = False

    def open_new_item(extra=""):
        nonlocal open_item
        out.append(f'<div class="item{extra}">')
        open_item = True

    for raw in lines:
        line = raw.rstrip()
        if code is not None:
            if line.strip().startswith("```"):
                cls = f' class="language-{code_lang}"' if code_lang else ""
                out.append(f'<pre class="code"><code{cls}>' + html.escape("\n".join(code), quote=False) + "</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        if line.lstrip().startswith("```"):
            flush_all(); code = []
            code_lang = re.sub(r"[^\w+#.-]", "", line.strip()[3:].strip().lower())
            if code_lang:
                langs.add(code_lang)
            continue
        m_list = re.match(r"^( *)([-*]|\d+\.) (.*)$", line)
        if line.startswith("# ") and not title:
            flush_all(); title = line[2:].strip(); continue
        if line.startswith("## "):
            flush_all(); close_item()
            if open_sec:
                out.append("</section>")
            sec += 1; item = 0
            text = line[3:].strip()
            toc.append((f"s{sec}", text, []))
            out.append(f'<section class="sec" id="s{sec}"><h2>{inline(text)}</h2>')
            open_sec = True
            open_new_item(" intro")
            continue
        if line.startswith("### "):
            flush_all(); close_item()
            item += 1
            open_new_item()
            text = line[4:].strip()
            if toc:
                toc[-1][2].append((f"s{sec}-{item}", text))
            out.append(f'<h3 id="s{sec}-{item}">{inline(text)}</h3>')
            continue
        if line.startswith(">"):
            flush_para(); flush_table(); close_lists()
            quote.append(line[1:].strip()); continue
        if line.startswith("|"):
            flush_para(); flush_quote(); close_lists()
            table.append(line); continue
        if m_list:
            flush_para(); flush_quote(); flush_table()
            ind, mark, text = len(m_list.group(1)), m_list.group(2), m_list.group(3)
            tag = "ol" if mark[0].isdigit() else "ul"
            if lists and ind > lists[-1][1]:
                out.append(f"<{tag}><li>")
                lists.append((tag, ind))
            else:
                close_lists(ind)
                if lists and lists[-1][1] == ind and lists[-1][0] == tag:
                    out.append("</li><li>")
                else:
                    close_lists(ind - 1)
                    out.append(f"<{tag}><li>")
                    lists.append((tag, ind))
            out.append(inline(text))
            continue
        if not line.strip():
            flush_all(); continue
        if lists and raw.startswith("  "):  # 목록 항목이 다음 줄로 이어짐
            out.append(" " + inline(line.strip())); continue
        flush_quote(); flush_table(); close_lists()
        if title and not lede and not open_sec and not para:
            lede = line.strip(); continue
        para.append(line.strip())
    if code is not None:
        sys.exit("오류: 닫히지 않은 코드 블록(```)이 있습니다")
    flush_all(); close_item()
    if open_sec:
        out.append("</section>")
    # 내용이 없는 intro 칸은 지운다
    body = re.sub(r'<div class="item intro"></div>', "", "\n".join(out))
    return title, lede, toc, body, sorted(langs)


def toc_html(toc):
    out = []
    for sid, text, items in toc:
        sub = "".join(f'<li><a href="#{iid}" data-id="{iid}">{plain(t)}</a></li>' for iid, t in items)
        out.append(f'<li class="tsec" data-sec="{sid}"><a href="#{sid}" data-id="{sid}">{plain(text)}</a>'
                   + (f"<ol>{sub}</ol>" if sub else "") + "</li>")
    return "".join(out)


PAGE = r"""<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 레이아웃: 넓은 화면은 왼쪽에 목차를 고정하고(지금 읽는 큰 절의 항목만 펼침) 오른쪽에 본문 한 단(약 68자),
   좁은 화면은 오른쪽 아래 '목차' 버튼으로 여닫는 서랍에 모든 항목을 보여 준다 */
:root {{
  --paper: #f4f6f8; --sheet: #ffffff; --ink: #1c2330; --muted: #5b6676; --rule: #d6dce4;
  --accent: #2b5a87; --mark: #fde89a; --star: #b24f1d; --scrim: rgba(16, 22, 30, .45);
  --f-display: "Gowun Batang", "Noto Serif KR", "Batang", serif;
  --f-body: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
{code_vars_light}
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #13171d; --sheet: #1a2028; --ink: #e3e7ed; --muted: #9ba5b3; --rule: #2b333e;
  --accent: #8fb8e2; --mark: #5c4b12; --star: #f2a46c; --scrim: rgba(0, 0, 0, .6); color-scheme: dark;
{code_vars_dark}
}} }}
:root[data-theme="dark"] {{
  --paper: #13171d; --sheet: #1a2028; --ink: #e3e7ed; --muted: #9ba5b3; --rule: #2b333e;
  --accent: #8fb8e2; --mark: #5c4b12; --star: #f2a46c; --scrim: rgba(0, 0, 0, .6); color-scheme: dark;
{code_vars_dark}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font: 16px/1.75 var(--f-body); }}
.wrap {{ max-width: 1120px; margin: 0 auto; display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 48px;
  padding-block: 40px 96px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
nav {{ position: sticky; top: calc(env(safe-area-inset-top, 0px) + 24px); align-self: start; max-height: calc(100vh - 48px); overflow: auto; overscroll-behavior: contain; }}
nav .lbl {{ font: 500 11px/1 var(--f-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 0 0 12px; }}
nav ol {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }}
nav a {{ display: block; padding: 6px 10px; border-radius: 4px; color: var(--ink); text-decoration: none; font-size: 14px; line-height: 1.4; }}
nav a:hover {{ background: var(--sheet); }}
nav .tsec > a.on {{ background: var(--sheet); color: var(--accent); font-weight: 600; }}
nav .tsec > ol {{ display: none; margin: 2px 0 6px 10px; padding-left: 8px; border-left: 1px solid var(--rule); }}
nav .tsec.open > ol {{ display: grid; }}
nav .tsec > ol a {{ font-size: 13px; padding: 4px 8px; color: var(--muted); }}
nav .tsec > ol a.on {{ color: var(--accent); font-weight: 600; background: var(--sheet); }}
nav a.off {{ opacity: .4; }}
nav .close {{ display: none; }}
.toc-btn, .scrim {{ display: none; }}
a:focus-visible, button:focus-visible, input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
main {{ min-width: 0; max-width: 46rem; }}
header h1 {{ font: 700 clamp(28px, 4vw, 40px)/1.25 var(--f-display); margin: 0 0 12px; text-wrap: balance; }}
header .lede {{ color: var(--muted); margin: 0 0 24px; }}
.tools {{ display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; padding-block: 12px; border-block: 1px solid var(--rule); margin-bottom: 8px; }}
.tools input[type=search] {{ flex: 1 1 220px; min-width: 0; font: inherit; font-size: 15px; padding: 8px 12px; border: 1px solid var(--rule); border-radius: 6px; background: var(--sheet); color: var(--ink); }}
.tools label {{ display: flex; gap: 6px; align-items: center; font-size: 14px; color: var(--muted); cursor: pointer; }}
.tools .count {{ font: 12px var(--f-mono); color: var(--muted); font-variant-numeric: tabular-nums; }}
.sec h2 {{ font: 700 26px/1.3 var(--f-display); margin: 56px 0 4px; padding-top: 8px; text-wrap: balance; scroll-margin-top: 16px; }}
.item h3 {{ font: 600 18px/1.45 var(--f-body); margin: 32px 0 8px; text-wrap: balance; scroll-margin-top: 16px; }}
.item p, .item ul, .item ol {{ margin: 0 0 12px; }}
.item ul, .item ol {{ padding-left: 1.3em; }}
.item li {{ margin: 3px 0; }}
.item li > ul, .item li > ol {{ margin: 4px 0; }}
strong {{ font-weight: 600; background: linear-gradient(transparent 62%, var(--mark) 62%); }}
blockquote.def {{ margin: 12px 0 16px; padding: 14px 18px; background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; font-family: var(--f-display); font-size: 17px; line-height: 1.8; }}
blockquote.def::before {{ content: "원문"; display: block; font: 500 10px/1 var(--f-mono); letter-spacing: .14em; color: var(--muted); margin-bottom: 8px; }}
.ref {{ font: 500 11px/1 var(--f-mono); color: var(--muted); border: 1px solid var(--rule); border-radius: 3px; padding: 2px 5px; margin-left: 4px; white-space: nowrap; vertical-align: 2px; }}
.star {{ color: var(--star); font-weight: 700; }}
code {{ font: 14px var(--f-mono); background: var(--sheet); border: 1px solid var(--rule); border-radius: 3px; padding: 0 4px; }}
/* 코드 블록은 클리닉과 같은 배경·글자색 (VS Code처럼 합자를 끔) */
pre.code {{ margin: 12px 0 16px; padding: 12px 16px; overflow-x: auto; background: var(--code-bg); color: var(--code-fg); border: 1px solid var(--rule); border-radius: 6px; tab-size: 4; }}
pre.code code {{ font-size: 13.5px; line-height: 1.6; background: none; border: 0; padding: 0; white-space: pre; color: inherit; }}
pre.code, pre.code code {{ font-variant-ligatures: none; font-feature-settings: "liga" 0, "calt" 0; }}
{code_css}
.tbl {{ overflow-x: auto; margin: 12px 0 16px; border: 1px solid var(--rule); border-radius: 6px; background: var(--sheet); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14.5px; line-height: 1.6; }}
th, td {{ text-align: left; vertical-align: top; padding: 9px 12px; border-bottom: 1px solid var(--rule); }}
th {{ font-weight: 600; color: var(--muted); font-size: 13px; background: var(--paper); }}
tr:last-child td {{ border-bottom: 0; }}
.empty {{ color: var(--muted); padding: 32px 0; }}
@media (max-width: 860px) {{
  .wrap {{ grid-template-columns: minmax(0, 1fr); gap: 0; padding-block: 24px 96px; }}
  /* 목차 서랍: 왼쪽에서 열리고, 모든 항목을 펼쳐 보여 준다 */
  /* nav는 .wrap 그리드의 자식이라 align-self: start가 남아 있으면 top/bottom으로 늘어나지 않는다 */
  nav {{ position: fixed; z-index: 20; top: 0; bottom: 0; left: 0; width: min(86vw, 340px); max-height: none; align-self: stretch;
    padding: calc(env(safe-area-inset-top, 0px) + 16px) 12px calc(env(safe-area-inset-bottom, 0px) + 24px) max(12px, env(safe-area-inset-left, 0px));
    background: var(--sheet); border-right: 1px solid var(--rule); box-shadow: 0 0 32px rgba(0, 0, 0, .18);
    transform: translateX(-102%); visibility: hidden; }}
  nav.open {{ transform: none; visibility: visible; }}
  nav .head {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }}
  nav .head .lbl {{ margin: 0; }}
  nav .close {{ display: block; font: inherit; font-size: 14px; color: var(--muted); background: none; border: 1px solid var(--rule); border-radius: 6px; padding: 4px 10px; cursor: pointer; }}
  nav a {{ padding: 9px 10px; font-size: 15px; }}
  nav .tsec > a {{ font-weight: 600; }}
  nav .tsec > ol, nav .tsec.open > ol {{ display: grid; }}
  nav .tsec > ol a {{ font-size: 14px; padding: 7px 8px; }}
  nav a:hover {{ background: var(--paper); }}
  nav .tsec > a.on, nav .tsec > ol a.on {{ background: var(--paper); }}
  .scrim {{ display: block; position: fixed; inset: 0; z-index: 15; background: var(--scrim); opacity: 0; visibility: hidden; }}
  .scrim.open {{ opacity: 1; visibility: visible; }}
  .toc-btn {{ display: flex; align-items: center; gap: 8px; position: fixed; z-index: 10;
    right: max(16px, env(safe-area-inset-right, 0px)); bottom: calc(env(safe-area-inset-bottom, 0px) + 16px);
    font: 600 14px/1 var(--f-body); color: var(--sheet); background: var(--accent); border: 0; border-radius: 999px;
    padding: 12px 18px; box-shadow: 0 4px 16px rgba(0, 0, 0, .22); cursor: pointer; }}
  .toc-btn .where {{ font-weight: 400; opacity: .85; max-width: 40vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  main {{ max-width: none; }}
}}
@media (prefers-reduced-motion: no-preference) {{
  html {{ scroll-behavior: smooth; }}
  /* 열 때는 바로 보이게(그래야 열자마자 포커스·스크롤이 된다), 닫을 때는 미끄러진 뒤에 숨긴다 */
  nav, .scrim {{ transition: transform .22s ease, opacity .22s ease, visibility 0s linear .22s; }}
  nav.open, .scrim.open {{ transition: transform .22s ease, opacity .22s ease, visibility 0s; }}
}}
</style>
<div class="wrap">
<nav id="toc" aria-label="목차"><div class="head"><p class="lbl">목차</p><button type="button" class="close" id="tocClose">닫기</button></div><ol>{toc}</ol></nav>
<div class="scrim" id="scrim"></div>
<main>
<header><h1>{title_html}</h1><p class="lede">{lede}</p>
<div class="tools">
<input type="search" id="q" placeholder="용어로 찾기" aria-label="요약에서 찾기">
<label><input type="checkbox" id="starOnly"> ★ 항목만</label>
<span class="count" id="count"></span>
</div></header>
{body}
<p class="empty" id="empty" hidden>찾는 말이 들어간 항목이 없습니다. 다른 용어로 찾아 보세요.</p>
</main>
</div>
<button type="button" class="toc-btn" id="tocBtn" aria-controls="toc" aria-expanded="false">목차<span class="where" id="where"></span></button>
<script>
(() => {{
  const q = document.getElementById('q'), star = document.getElementById('starOnly');
  const items = [...document.querySelectorAll('.item')], secs = [...document.querySelectorAll('.sec')];
  const count = document.getElementById('count'), empty = document.getElementById('empty');
  const text = new Map(items.map(el => [el, el.textContent.toLowerCase()]));
  const nav = document.getElementById('toc'), btn = document.getElementById('tocBtn'), scrim = document.getElementById('scrim');
  const links = new Map([...nav.querySelectorAll('a[data-id]')].map(a => [a.dataset.id, a]));
  function apply() {{
    const k = q.value.trim().toLowerCase(), s = star.checked;
    let n = 0;
    for (const el of items) {{
      const show = (!k || text.get(el).includes(k)) && (!s || el.querySelector('.star') || el.closest('.sec').querySelector('h2 .star'));
      el.hidden = !show; if (show && !el.classList.contains('intro')) n++;
      const h = el.querySelector('h3'); if (h && links.has(h.id)) links.get(h.id).classList.toggle('off', !show);
    }}
    for (const sec of secs) {{
      sec.hidden = !sec.querySelector('.item:not([hidden])');
      if (links.has(sec.id)) links.get(sec.id).classList.toggle('off', sec.hidden);
    }}
    const filtered = k || s;
    count.textContent = filtered ? n + '개 항목' : '';
    empty.hidden = !filtered || n > 0 || items.some(el => !el.hidden);
    track();
  }}
  q.addEventListener('input', apply); star.addEventListener('change', apply);

  // 지금 읽는 큰 절·항목: 화면 위쪽 30% 선을 지난 마지막 제목
  const heads = [...document.querySelectorAll('.sec h2, .item h3')];
  let cur = '';
  function track() {{
    const line = innerHeight * 0.3;
    let h = null;
    for (const el of heads) {{
      if (el.closest('[hidden]')) continue;
      if (el.getBoundingClientRect().top <= line) h = el; else break;
    }}
    const id = h ? (h.tagName === 'H2' ? h.closest('.sec').id : h.id) : '';
    if (id === cur) return;
    cur = id;
    const sid = h ? h.closest('.sec').id : '';
    for (const [k, a] of links) a.classList.toggle('on', k === id || k === sid);
    for (const li of nav.querySelectorAll('.tsec')) li.classList.toggle('open', li.dataset.sec === sid);
    document.getElementById('where').textContent = h ? ' · ' + h.textContent.replace('★', '').trim() : '';
  }}
  let ticking = false;
  addEventListener('scroll', () => {{ if (!ticking) {{ ticking = true; requestAnimationFrame(() => {{ ticking = false; track(); }}); }} }}, {{ passive: true }});
  addEventListener('resize', track);

  // 좁은 화면의 목차 서랍
  const narrow = matchMedia('(max-width: 860px)');
  function setOpen(open) {{
    nav.classList.toggle('open', open); scrim.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
    document.documentElement.style.overflow = open ? 'hidden' : '';
    if (open) {{
      const a = nav.querySelector('.tsec > ol a.on') || nav.querySelector('a.on') || nav.querySelector('a');
      a.scrollIntoView({{ block: 'center' }}); a.focus({{ preventScroll: true }});
    }}
  }}
  btn.addEventListener('click', () => setOpen(!nav.classList.contains('open')));
  scrim.addEventListener('click', () => {{ setOpen(false); btn.focus(); }});
  document.getElementById('tocClose').addEventListener('click', () => {{ setOpen(false); btn.focus(); }});
  nav.addEventListener('click', e => {{ if (e.target.closest('a') && narrow.matches) setOpen(false); }});
  addEventListener('keydown', e => {{ if (e.key === 'Escape' && nav.classList.contains('open')) {{ setOpen(false); btn.focus(); }} }});
  narrow.addEventListener('change', () => setOpen(false));

  apply();
}})();
</script>
<script>
// 코드 색칠: 클리닉과 같은 규칙(highlight.js + VS Code 색). 불러오지 못하면 색 없이 그대로 둔다
(() => {{
{code_js}
  const LANGS = {langs};
  if (!LANGS.length) return;
  function paint(c, lang) {{
    if (!window.hljs.getLanguage(lang)) return;
    c.innerHTML = window.hljs.highlight(c.textContent, {{ language: lang, ignoreIllegals: true }}).value;
    c.querySelectorAll('.hljs-keyword').forEach(k => {{ if (CTL_KW.has(k.textContent)) k.classList.add('ctl'); }});
    const name = (window.hljs.getLanguage(lang).name || lang).toLowerCase();
    if (!NO_IDENT.has(lang) && !NO_IDENT.has(name)) markIdents(c);
  }}
  const load = src => new Promise(res => {{ const s = document.createElement('script'); s.src = src; s.onload = s.onerror = res; document.head.appendChild(s); }});
  load(HLJS + 'highlight.min.js').then(() => {{
    if (!window.hljs) return;
    const more = LANGS.filter(l => !window.hljs.getLanguage(l));
    return Promise.all(more.map(l => load(`${{HLJS}}languages/${{l}}.min.js`))).then(() => {{
      document.querySelectorAll('pre.code code[class*="language-"]').forEach(c => paint(c, c.className.match(/language-([\w+#.-]+)/)[1]));
    }});
  }});
}})();
</script>
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        sys.exit("사용법: python build_summary.py 요약.md 요약.html")
    md = open(sys.argv[1], encoding="utf-8").read()
    title, lede, toc, body, langs = convert(md)
    if not title:
        sys.exit("오류: '# 제목' 줄이 없습니다")
    sh = shared_parts()
    page = PAGE.format(title=html.escape(title), title_html=inline(title), lede=inline(lede), toc=toc_html(toc), body=body,
                       code_vars_light=sh["code-vars-light"], code_vars_dark=sh["code-vars-dark"],
                       code_css=sh["code-css"], code_js=sh["code-js"], langs=str(langs).replace("'", '"'))
    open(sys.argv[2], "w", encoding="utf-8").write(page)
    n_items = body.count('<div class="item"')
    n_code = body.count('<pre class="code">')
    print(f"작성: {sys.argv[2]} ({len(page):,}자) · 큰 절 {len(toc)} · 항목 {n_items} · 코드 블록 {n_code}"
          + (f" (색칠 언어: {', '.join(langs)})" if langs else ""))


if __name__ == "__main__":
    main()
