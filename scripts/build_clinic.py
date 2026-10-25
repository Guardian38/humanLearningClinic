"""과목 데이터(JSON)를 클리닉 템플릿에 넣어 아티팩트용 HTML을 만든다.

사용법: python build_clinic.py <subject.json> <out.html> [--pylib <esprima가 설치된 폴더>] [--no-run]

- 데이터를 검사해 오류가 있으면 멈추고, 경고는 출력만 한다.
- 코드 문제의 모범 코드(run.sol)를 실제로 실행해 의도한 출력(run.out)을 확인한다. out이 없으면 실행 결과로 채운다.
  --no-run이면 건너뛴다.
- esprima를 불러올 수 있으면 페이지 안의 스크립트 문법도 검사한다.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "clinic_template.html")
KNOWN_TOOLS = {"matrix"}
# 페이지의 RUNNERS 키. 여기 없는 언어는 페이지에서 실행하지 않는다(run 없이 code만)
KNOWN_RUNNERS = {"js", "pyodide"}
# 페이지의 parseAns가 읽는 꼴: 수, 분수, 소수, [1 2; 3 4], (1, 2, 3), "x = 3"
ANS_OK = re.compile(r"^(?:[^=]*=\s*)?[\[(]?\s*-?\d+(?:[./]-?\d+)?(?:[\s,;]+-?\d+(?:[./]-?\d+)?)*\s*[\])]?$")
DEPENDENT = re.compile(r"위 문제|앞 문제|앞의 (예제|문제|실험)|같은 조건|같은 행렬|이전 문제")


def validate(d):
    errs, warns = [], []
    for k in ("title", "role", "units", "concepts", "questions"):
        if k not in d:
            errs.append(f"'{k}' 항목이 없습니다")
    if errs:
        return errs, warns
    units, concepts = d["units"], d["concepts"]
    for cid, v in concepts.items():
        if "." not in cid or cid.split(".", 1)[0] not in units:
            errs.append(f"개념 id '{cid}'는 '<단원 키>.<이름>' 꼴이고 단원 키가 units에 있어야 합니다")
        if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) and x for x in v)):
            errs.append(f"개념 '{cid}'는 [이름, 노트 요약] 꼴이어야 합니다")
    seen, used = set(), set()
    for i, q in enumerate(d["questions"]):
        tag = q.get("id", f"#{i}")
        if not q.get("id"):
            errs.append(f"{tag}: id가 없습니다 (기록이 id에 묶이므로 한번 정한 id는 바꾸지 않습니다)")
        elif q["id"] in seen:
            errs.append(f"{tag}: id가 중복됩니다")
        seen.add(q.get("id"))
        if q.get("c") not in concepts:
            errs.append(f"{tag}: 개념 '{q.get('c')}'가 concepts에 없습니다")
        used.add(q.get("c"))
        if not q.get("q"):
            errs.append(f"{tag}: 문제 글(q)이 없습니다")
        t = q.get("t")
        if t == "mc":
            o, a = q.get("o"), q.get("a")
            if not (isinstance(o, list) and 2 <= len(o) <= 5 and all(o)):
                errs.append(f"{tag}: 보기(o)는 2~5개여야 합니다")
            elif len(set(o)) != len(o):
                errs.append(f"{tag}: 같은 보기가 있습니다")
            if not (isinstance(a, int) and isinstance(o, list) and 0 <= a < len(o)):
                errs.append(f"{tag}: 정답(a)은 보기 인덱스(0부터)여야 합니다")
            if not q.get("e"):
                warns.append(f"{tag}: 해설(e)이 없습니다")
        elif t == "open":
            if not isinstance(q.get("a"), str) or not q["a"]:
                errs.append(f"{tag}: 서술형 모범 답안(a)이 없습니다")
            alts = q.get("alts")
            if alts is not None and not (isinstance(alts, list) and all(isinstance(x, str) and x for x in alts)):
                errs.append(f"{tag}: alts(다른 인정 답안)는 문자열 목록이어야 합니다")
            elif re.search(r"다른 (방법|예|풀이)|해도 (됩니다|된다)|넣어도|구해도", q.get("a", "")) and not alts:
                warns.append(f"{tag}: 모범 답안에 다른 갈래의 답이 섞여 있는지 확인하세요. 같은 점수를 받는 다른 근거는 alts로 뺍니다")
        elif t == "short":
            ans = q.get("ans")
            keys = ans if isinstance(ans, list) else [ans]
            if not keys or not all(isinstance(k, str) and k.strip() for k in keys):
                errs.append(f"{tag}: 단답형 정답(ans)은 문자열이나 문자열 목록이어야 합니다")
            elif not all(ANS_OK.match(k.strip()) for k in keys):
                warns.append(f"{tag}: 정답 {keys}가 수·행렬 꼴이 아니라 글자 그대로 비교합니다")
            if not q.get("e"):
                warns.append(f"{tag}: 풀이·해설(e)이 없습니다")
        else:
            errs.append(f"{tag}: t는 'mc', 'short', 'open' 중 하나여야 합니다")
        hints = q.get("hints")
        if hints is not None and not (isinstance(hints, list) and all(isinstance(h, str) and h for h in hints)):
            errs.append(f"{tag}: hints는 문자열 목록이어야 합니다")
        if q.get("work") not in (None, "photo", "text"):
            errs.append(f"{tag}: work는 'photo' 또는 'text'여야 합니다")
        texts = [q.get("q", "")] + (q.get("o") or []) + (hints or []) + [q.get("e", "") if t in ("mc", "short") else q.get("a", "")] + (q.get("alts") or [])
        for s in texts:
            if not isinstance(s, str):
                continue
            # 코드 안의 '$'는 수식이 아니다(MathJax는 <pre>, <code> 안을 건너뛴다)
            for code in re.findall(r"<pre[^>]*>([\s\S]*?)</pre>", s, re.I):
                if "<" in re.sub(r"</?code[^>]*>", "", code, flags=re.I):
                    warns.append(f"{tag}: <pre> 안의 '<'는 HTML 태그로 읽힙니다. 코드의 <, >, &는 &lt; &gt; &amp;로 쓰세요: {code[:50]}")
            if len(re.findall(r"(?<!\\)\$", re.sub(r"<(pre|code)[^>]*>[\s\S]*?</\1>", "", s, flags=re.I))) % 2:
                warns.append(f"{tag}: '$' 개수가 홀수라 수식이 깨질 수 있습니다: {s[:50]}")
                break
        f = q.get("fig")
        if f is not None:
            if not isinstance(f, dict) or not (f.get("svg") or f.get("src")):
                errs.append(f"{tag}: fig에는 svg나 src가 있어야 합니다")
            elif not f.get("alt"):
                errs.append(f"{tag}: fig.alt(그림 설명)가 없습니다. Claude는 채점·검토 때 이 설명으로만 그림을 압니다")
        if DEPENDENT.search(q.get("q", "")):
            warns.append(f"{tag}: 다른 문제에 기대는 표현이 있는지 확인하세요: {q['q'][:60]}")
        run = q.get("run")
        if q.get("code") or run is not None:
            if not (d.get("profile") or {}).get("code"):
                errs.append(f"{tag}: code/run 문제는 profile.code(언어)가 있어야 합니다")
            if t not in ("open", "short"):
                errs.append(f"{tag}: code/run은 서술형(open, 코드 작성)이나 단답형(short, 출력 맞히기)에만 씁니다")
        if run is not None:
            if not (isinstance(run, dict) and (isinstance(run.get("sol"), str) or isinstance(run.get("out"), str))):
                errs.append(f"{tag}: run은 {{\"sol\": 모범 코드, \"out\": 의도한 출력, \"stdin\": 입력}} 꼴이고 sol이나 out이 있어야 합니다")
            elif t == "open" and not ((d.get("profile") or {}).get("code") or {}).get("run"):
                warns.append(f"{tag}: 이 과목은 실행기(profile.code.run)가 없어 학생 코드의 출력을 비교하지 못합니다. 의도한 출력만 보여 줍니다")
    for cid in concepts:
        if cid not in used:
            warns.append(f"개념 '{cid}'에 문제가 없습니다 (기억 되살리기 카드로만 나옵니다)")
    prof = d.get("profile") or {}
    pl = prof.get("photoLimit")
    if pl is not None and not (isinstance(pl, dict) and isinstance(pl.get("n"), int) and isinstance(pl.get("of"), int) and 0 <= pl["n"] < pl["of"]):
        errs.append("profile.photoLimit는 {\"n\": 2, \"of\": 5}처럼 n < of인 정수여야 합니다")
    if set(prof.get("genTypes") or []) - {"mc", "short", "open"}:
        errs.append("profile.genTypes에는 'mc', 'short', 'open'만 쓸 수 있습니다")
    tools = set(prof.get("tools") or [])
    if tools - KNOWN_TOOLS:
        errs.append(f"알 수 없는 도구: {sorted(tools - KNOWN_TOOLS)} (쓸 수 있는 것: {sorted(KNOWN_TOOLS)})")
    code = prof.get("code")
    if code is not None:
        if not (isinstance(code, dict) and isinstance(code.get("lang"), str) and code["lang"]):
            errs.append("profile.code는 {\"lang\": \"python\", \"run\": \"pyodide\"}처럼 lang(highlight.js 언어 이름)이 있어야 합니다")
        elif code.get("run") not in (None, *KNOWN_RUNNERS):
            errs.append(f"profile.code.run은 {sorted(KNOWN_RUNNERS)} 중 하나이거나 없어야 합니다(없으면 실행하지 않음)")
    return errs, warns


# 페이지의 jsWorker와 같은 출력 형식(console.log 인자는 공백으로 잇고, 객체는 JSON)
JS_PRELUDE = r"""const __f=x=>typeof x==='string'?x:x===undefined?'undefined':['function','symbol','bigint'].includes(typeof x)?String(x):(()=>{try{return JSON.stringify(x)}catch(e){return String(x)}})();
console.log=console.info=(...a)=>process.stdout.write(a.map(__f).join(' ')+'\n');
console.warn=console.error=(...a)=>process.stderr.write(a.map(__f).join(' ')+'\n');
const __in=require('fs').readFileSync(0,'utf8').split('\n');let __k=0;globalThis.prompt=()=>__k<__in.length?__in[__k++]:null;
"""


def out_lines(s):
    """페이지의 outLines와 같다: 줄 끝 공백과 마지막 빈 줄은 무시한다."""
    lines = [l.rstrip() for l in s.replace("\r", "").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def run_sol(runner, sol, stdin):
    """모범 코드를 이 컴퓨터에서 실행한다. 실행할 수 없으면 None."""
    if runner == "pyodide":
        # -I는 PYTHON* 환경 변수를 무시하므로 UTF-8 출력은 -X utf8로 맞춘다
        cmd = [sys.executable, "-I", "-X", "utf8", "-c", sol]
    elif runner == "js" and shutil.which("node"):
        fd, path = tempfile.mkstemp(suffix=".js")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(JS_PRELUDE + sol)
        cmd = [shutil.which("node"), path]
    else:
        return None
    p = subprocess.run(cmd, input=stdin or "", capture_output=True, text=True, encoding="utf-8", timeout=20, cwd=tempfile.gettempdir())
    if cmd[-1].endswith(".js"):
        os.remove(cmd[-1])
    return p


def check_runs(d):
    """run.sol을 실행해 run.out을 확인하거나 채운다. 단답형은 정답(ans)과 출력이 같은지도 본다."""
    code = (d.get("profile") or {}).get("code") or {}
    runner = code.get("run")
    errs, n = [], 0
    for q in d["questions"]:
        run = q.get("run")
        if not run:
            continue
        tag, sol = q["id"], run.get("sol")
        if isinstance(sol, str) and sol.strip():
            try:
                p = run_sol(runner, sol, run.get("stdin", ""))
            except subprocess.TimeoutExpired:
                errs.append(f"{tag}: 모범 코드가 20초 안에 끝나지 않습니다")
                continue
            if p is None:
                if "out" not in run:
                    errs.append(f"{tag}: 모범 코드를 이 컴퓨터에서 실행할 수 없어(실행기 {runner}) run.out을 직접 적어야 합니다")
                else:
                    print(f"경고: {tag}: 모범 코드를 실행하지 못해 run.out을 확인하지 않았습니다")
                continue
            if p.returncode != 0:
                errs.append(f"{tag}: 모범 코드가 오류로 끝났습니다:\n{p.stderr.strip()[-600:]}")
                continue
            if "out" not in run:
                run["out"] = p.stdout
            elif out_lines(run["out"]) != out_lines(p.stdout):
                errs.append(f"{tag}: run.out이 모범 코드의 실제 출력과 다릅니다.\n  적은 것: {run['out']!r}\n  실제: {p.stdout!r}")
                continue
            n += 1
        if q.get("t") == "short" and "out" in run:
            keys = q["ans"] if isinstance(q.get("ans"), list) else [q.get("ans", "")]
            if not any(out_lines(k) == out_lines(run["out"]) for k in keys):
                errs.append(f"{tag}: 단답형 정답 {keys}가 코드의 실제 출력 {run['out']!r}과 다릅니다")
        if "out" not in run:
            errs.append(f"{tag}: run.out(의도한 출력)이 없습니다")
    return errs, n


MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}


def embed_figs(d, base):
    """fig.src가 로컬 파일이면 data URI로 바꿔 페이지 안에 넣는다 (외부 링크는 끊기거나 막힐 수 있음)."""
    import base64
    total = 0
    for q in d["questions"]:
        f = q.get("fig")
        if not f or not f.get("src") or f["src"].startswith("data:"):
            continue
        if re.match(r"https?://", f["src"]):
            sys.exit(f"{q['id']}: 외부 이미지 주소는 쓰지 않습니다. 파일로 받아 두고 로컬 경로를 적으세요")
        path = os.path.join(base, f["src"])
        ext = os.path.splitext(path)[1].lower()
        if ext not in MIME:
            sys.exit(f"{q['id']}: 지원하지 않는 이미지 형식 {ext}")
        raw = open(path, "rb").read()
        total += len(raw)
        if len(raw) > 400_000:
            print(f"경고: {q['id']} 그림이 {len(raw) // 1000}KB입니다. 줄이면 페이지가 가벼워집니다")
        f["src"] = f"data:{MIME[ext]};base64," + base64.b64encode(raw).decode()
    if total > 8_000_000:
        sys.exit(f"그림이 모두 {total // 1_000_000}MB라 페이지 한도(16MB)에 가깝습니다. 그림을 줄이세요")


def check_js(page, pylib):
    if pylib:
        sys.path.insert(0, pylib)
    try:
        import esprima
    except ImportError:
        print("문법 검사 건너뜀: esprima가 없습니다 (pip install --target <폴더> esprima 후 --pylib로 지정)")
        return True
    ok = True
    for i, js in enumerate(re.findall(r"<script>(.*?)</script>", page, re.S)):
        try:
            esprima.parseScript(js, {"tolerant": False})
        except Exception as e:
            print(f"스크립트 {i} 문법 오류: {e}")
            ok = False
    if ok:
        print("스크립트 문법 OK")
    return ok


def main():
    args = sys.argv[1:]
    pylib = None
    if "--pylib" in args:
        k = args.index("--pylib")
        pylib = args[k + 1]
        del args[k:k + 2]
    no_run = "--no-run" in args
    args = [a for a in args if a != "--no-run"]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    src, out = args
    d = json.load(open(src, encoding="utf-8"))
    errs, warns = validate(d)
    for w in warns:
        print("경고:", w)
    if errs:
        for e in errs:
            print("오류:", e)
        sys.exit(1)
    if any(q.get("run") for q in d["questions"]):
        if no_run:
            print("경고: --no-run이라 코드 문제의 출력을 확인하지 않았습니다")
            missing = [q["id"] for q in d["questions"] if q.get("run") and "out" not in q["run"]]
            if missing:
                sys.exit(f"오류: run.out이 없는 문제가 있습니다(--no-run이면 직접 적어야 함): {missing}")
        else:
            run_errs, n = check_runs(d)
            for e in run_errs:
                print("오류:", e)
            if run_errs:
                sys.exit(1)
            print(f"코드 출력 확인: 모범 코드 {n}개 실행")
    embed_figs(d, os.path.dirname(os.path.abspath(src)))
    tpl = open(TEMPLATE, encoding="utf-8").read()
    data = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = tpl.replace("@@TITLE@@", html.escape(d["title"])).replace("/*@@DATA@@*/null", data)
    if d.get("lede"):
        page = re.sub(r'<p class="lede">.*?</p>', lambda m: f'<p class="lede">{d["lede"]}</p>', page, count=1, flags=re.S)
    ok = check_js(page, pylib)
    open(out, "w", encoding="utf-8").write(page)
    n = len(d["questions"])
    print(f"작성: {out} ({len(page):,}자) · 단원 {len(d['units'])} · 개념 {len(d['concepts'])} · 문제 {n} "
          f"(객관식 {sum(q['t'] == 'mc' for q in d['questions'])}, 단답형 {sum(q['t'] == 'short' for q in d['questions'])}, "
          f"서술형 {sum(q['t'] == 'open' for q in d['questions'])}, 종이 풀이 {sum(q.get('work') == 'photo' for q in d['questions'])})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
