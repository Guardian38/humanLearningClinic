"""과목 요약본(요약.md)을 공부용 HTML 페이지로 만든다.

요약.md가 원본이다. 이 페이지는 훑어보기용으로 md에서 만들기만 하고 손으로 고치지 않는다.

    python build_summary.py 요약.md 요약.html

쓸 수 있는 md 문법 (이 밖의 문법은 글자 그대로 나온다)
- `# 제목` 한 번(페이지 이름), 바로 다음 문단은 머리말
- `## 큰 절`(주차 등, 목차에 나옴), `### 항목`(검색·필터의 단위)
- 문단, `- ` 목록과 `1. ` 번호 목록(2칸 들여쓰기로 한 단계 중첩), `> ` 인용(슬라이드 원문 정의), `| 표 |`
- 글 안: `**굵게**`, `*기울임*`, `` `코드` ``, `[p33]`·`[p10, p39]`·`[4주차 p33]`·`[2-2 p7~14]`(쪽수 근거), `★`(시험 강조)
"""
import html
import re
import sys

REF = re.compile(r"\[((?:\d+-\d+ |\d+주차 )?p\d+(?:[~–-]\d+)?(?:, ?(?:\d+주차 )?p\d+(?:[~–-]\d+)?)*)\]")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", s)
    s = REF.sub(r'<span class="ref">\1</span>', s)
    return s.replace("★", '<span class="star" title="시험에 꼭 나온다고 공지되었거나 교수님이 강조한 것">★</span>')


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md):
    lines = md.replace("\r\n", "\n").split("\n")
    title, lede, out, toc = "", "", [], []
    sec = item = 0
    open_sec = open_item = False
    para, quote, table, lists = [], [], [], []  # lists: [(태그, 들여쓰기)]

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
        m_list = re.match(r"^( *)([-*]|\d+\.) (.*)$", line)
        if line.startswith("# ") and not title:
            flush_all(); title = line[2:].strip(); continue
        if line.startswith("## "):
            flush_all(); close_item()
            if open_sec:
                out.append("</section>")
            sec += 1; item = 0
            text = line[3:].strip()
            toc.append((f"s{sec}", text))
            out.append(f'<section class="sec" id="s{sec}"><h2>{inline(text)}</h2>')
            open_sec = True
            open_new_item(" intro")
            continue
        if line.startswith("### "):
            flush_all(); close_item()
            item += 1
            open_new_item()
            out.append(f'<h3 id="s{sec}-{item}">{inline(line[4:].strip())}</h3>')
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
    flush_all(); close_item()
    if open_sec:
        out.append("</section>")
    # 내용이 없는 intro 칸은 지운다
    body = re.sub(r'<div class="item intro"></div>', "", "\n".join(out))
    return title, lede, toc, body


PAGE = r"""<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=IBM+Plex+Sans+KR:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 레이아웃: 넓은 화면은 왼쪽에 큰 절 목차를 고정하고 오른쪽에 본문 한 단(약 68자), 좁은 화면은 목차가 위에서 가로로 흐른다 */
:root {{
  --paper: #f4f6f8; --sheet: #ffffff; --ink: #1c2330; --muted: #5b6676; --rule: #d6dce4;
  --accent: #2b5a87; --mark: #fde89a; --star: #b24f1d;
  --f-display: "Gowun Batang", "Noto Serif KR", "Batang", serif;
  --f-body: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #13171d; --sheet: #1a2028; --ink: #e3e7ed; --muted: #9ba5b3; --rule: #2b333e;
  --accent: #8fb8e2; --mark: #5c4b12; --star: #f2a46c; color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --paper: #13171d; --sheet: #1a2028; --ink: #e3e7ed; --muted: #9ba5b3; --rule: #2b333e;
  --accent: #8fb8e2; --mark: #5c4b12; --star: #f2a46c; color-scheme: dark;
}}
body {{ background: var(--paper); color: var(--ink); font: 16px/1.75 var(--f-body); }}
.wrap {{ max-width: 1120px; margin: 0 auto; display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 48px;
  padding-block: 40px 96px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
nav {{ position: sticky; top: calc(env(safe-area-inset-top, 0px) + 24px); align-self: start; max-height: calc(100vh - 48px); overflow: auto; }}
nav .lbl {{ font: 500 11px/1 var(--f-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 0 0 12px; }}
nav ol {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }}
nav a {{ display: block; padding: 6px 10px; border-radius: 4px; color: var(--ink); text-decoration: none; font-size: 14px; line-height: 1.4; }}
nav a:hover {{ background: var(--sheet); }}
nav a.on {{ background: var(--sheet); color: var(--accent); font-weight: 600; }}
nav a:focus-visible, button:focus-visible, input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
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
.tbl {{ overflow-x: auto; margin: 12px 0 16px; border: 1px solid var(--rule); border-radius: 6px; background: var(--sheet); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14.5px; line-height: 1.6; }}
th, td {{ text-align: left; vertical-align: top; padding: 9px 12px; border-bottom: 1px solid var(--rule); }}
th {{ font-weight: 600; color: var(--muted); font-size: 13px; background: var(--paper); }}
tr:last-child td {{ border-bottom: 0; }}
.empty {{ color: var(--muted); padding: 32px 0; }}
@media (max-width: 860px) {{
  .wrap {{ grid-template-columns: minmax(0, 1fr); gap: 16px; padding-block: 24px 72px; }}
  nav {{ position: static; max-height: none; overflow: visible; }}
  nav ol {{ display: flex; gap: 6px; overflow-x: auto; padding-bottom: 6px; }}
  nav a {{ white-space: nowrap; border: 1px solid var(--rule); background: var(--sheet); }}
  main {{ max-width: none; }}
}}
@media (prefers-reduced-motion: no-preference) {{ html {{ scroll-behavior: smooth; }} }}
</style>
<div class="wrap">
<nav aria-label="목차"><p class="lbl">목차</p><ol>{toc}</ol></nav>
<main>
<header><h1>{title_html}</h1><p class="lede">{lede}</p>
<div class="tools">
<input type="search" id="q" placeholder="용어로 찾기 (예: 양화사, 반례)" aria-label="요약에서 찾기">
<label><input type="checkbox" id="starOnly"> ★ 항목만</label>
<span class="count" id="count"></span>
</div></header>
{body}
<p class="empty" id="empty" hidden>찾는 말이 들어간 항목이 없습니다. 다른 용어로 찾아 보세요.</p>
</main>
</div>
<script>
(() => {{
  const q = document.getElementById('q'), star = document.getElementById('starOnly');
  const items = [...document.querySelectorAll('.item')], secs = [...document.querySelectorAll('.sec')];
  const count = document.getElementById('count'), empty = document.getElementById('empty');
  const text = new Map(items.map(el => [el, el.textContent.toLowerCase()]));
  function apply() {{
    const k = q.value.trim().toLowerCase(), s = star.checked;
    let n = 0;
    for (const el of items) {{
      const show = (!k || text.get(el).includes(k)) && (!s || el.querySelector('.star') || el.closest('.sec').querySelector('h2 .star'));
      el.hidden = !show; if (show && !el.classList.contains('intro')) n++;
    }}
    for (const sec of secs) sec.hidden = !sec.querySelector('.item:not([hidden])');
    const filtered = k || s;
    count.textContent = filtered ? n + '개 항목' : '';
    empty.hidden = !filtered || n > 0 || items.some(el => !el.hidden);
  }}
  q.addEventListener('input', apply); star.addEventListener('change', apply);
  const links = [...document.querySelectorAll('nav a')];
  if ('IntersectionObserver' in window) {{
    const io = new IntersectionObserver(es => {{
      for (const e of es) if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
    }}, {{ rootMargin: '0px 0px -70% 0px' }});
    secs.forEach(s => io.observe(s));
  }}
  apply();
}})();
</script>
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        sys.exit("사용법: python build_summary.py 요약.md 요약.html")
    md = open(sys.argv[1], encoding="utf-8").read()
    title, lede, toc, body = convert(md)
    if not title:
        sys.exit("오류: '# 제목' 줄이 없습니다")
    plain = lambda s: re.sub(r"<[^>]+>", "", inline(s))
    toc_html = "".join(f'<li><a href="#{i}">{plain(t)}</a></li>' for i, t in toc)
    page = PAGE.format(title=html.escape(title), title_html=inline(title), lede=inline(lede), toc=toc_html, body=body)
    open(sys.argv[2], "w", encoding="utf-8").write(page)
    n_items = body.count('<div class="item"')
    print(f"작성: {sys.argv[2]} ({len(page):,}자) · 큰 절 {len(toc)} · 항목 {n_items}")


if __name__ == "__main__":
    main()
