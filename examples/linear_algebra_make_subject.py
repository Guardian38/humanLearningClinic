"""선형대수 약점 클리닉의 과목 데이터(subject.json)를 만든다.

계산이 들어간 정답은 아래 check()에서 sympy로 검증한다. 문제를 고치면 다시 실행한다.
문제 id는 풀이 기록과 묶여 있으므로 한번 정한 id는 바꾸지 않는다(문제를 빼려면 지우고, 새 문제는 새 id로).

    python make_subject.py            # 검증 후 subject.json 작성
    python ~/.claude/skills/study-clinic/scripts/build_clinic.py subject.json 선형대수클리닉.html

[study-clinic 예시] 실제로 쓰는 선형대수 클리닉의 원본을 복사한 것이다. 구조(문제 도우미 함수, sympy 검증,
보기 섞기, PROFILE)를 참고하고, PROFILE의 출제·채점 기준은 이 과목에서 정한 값이라 다른 과목에 옮기지 않는다.
"""
import json
import os
import sys

from sympy import Matrix, Rational, eye, symbols, solve

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))


def M(id, c, q, o, a, e, **kw):
    return {"id": id, "c": c, "t": "mc", "q": q, "o": o, "a": a, "e": e, **kw}


def O(id, c, q, a):
    return {"id": id, "c": c, "t": "open", "q": q, "a": a}


UNITS = {"1": "연립방정식과 행렬", "2": "행렬식"}

CONCEPTS = {
    "1.system": ["연립방정식과 해의 세 경우", "m×n system은 방정식 m개, 미지수 n개다. 2×2에서 두 직선이 한 점에서 만나면 유일해, 평행하면 해 없음(inconsistent), 겹치면 무수히 많다. 해가 같은 system을 equivalent라 하고, 순서 바꾸기·0이 아닌 수 곱하기·한 식의 상수배를 다른 식에 더하기를 해도 equivalent system을 얻는다."],
    "1.ge": ["가우스 소거와 가우스-요르당 소거", "가우스 소거는 pivot 아래를 0으로 만들어 triangular form으로 바꾼 뒤 back substitution한다. pivot이 0이면 행을 교환한다. 가우스-요르당 소거는 pivot 위도 0으로 만들고 각 행을 pivot으로 나눠 [A|b]→[I|x]로 해를 바로 읽는다."],
    "1.ref": ["row echelon form과 해의 판정", "각 행의 첫 0이 아닌 성분에 해당하는 변수가 lead variable, 나머지가 free variable이다. free variable이 있고 해가 있으면 해가 무수히 많다. (0 … 0 | c), c≠0인 행이 있으면 inconsistent다. m=n은 exact, m>n은 overdetermined, m<n은 underdetermined system이고, m<n이면 해가 있을 때 무수히 많다."],
    "1.alg": ["행렬 대수", "m×n과 n×r 행렬의 곱은 m×r이고 c_ij = Σ_k a_ik b_kj (A의 i행과 B의 j열의 곱)이다. AB≠BA(교환법칙 불성립). 결합법칙, 분배법칙, 스칼라 곱의 성질은 성립한다. O는 덧셈의 항등원, −A는 덧셈의 역원이다."],
    "1.trans": ["전치와 대칭행렬", "B=A^T는 b_ji=a_ij. (A^T)^T=A, (αA)^T=αA^T, (A+B)^T=A^T+B^T, (AB)^T=B^TA^T(순서가 바뀜). A^T=A이면 symmetric이다. K^T=−K인 행렬은 강의에서 따로 이름을 붙이지 않았다(문제에서는 식으로만 쓴다)."],
    "1.inv": ["역행렬과 singular", "n×n A에 대해 AB=BA=I이면 B=A^{-1}. 역행렬이 없으면 singular, 있으면 nonsingular(invertible). (AB)^{-1}=B^{-1}A^{-1}이며 증명은 두 순서로 곱해 I가 됨을 보인다. I는 곱셈의 항등원이다."],
    "1.elem": ["기본행렬", "I에 행연산을 한 번 한 행렬이다. 왼쪽에 곱하면 그 행연산을 한 것과 같다. type I(두 행 교환)의 역은 자기 자신, type II(한 행에 α≠0 곱함)의 역은 α→1/α, type III(한 행의 c배를 다른 행에 더함)의 역은 c→−c. E_k⋯E_1A=I이면 E_k⋯E_1=A^{-1}이므로 [A|I]→[I|A^{-1}]."],
    "1.part": ["분할행렬과 블록 곱", "AB=[Ab_1 ⋯ Ab_r]이므로 AB의 j열은 Ab_j, (i,j) 성분은 a(i,:)b_j다. 블록 크기가 맞으면 블록을 성분처럼 곱한다: [A_1 A_2][B_1; B_2]=A_1B_1+A_2B_2. block diagonal 행렬의 역행렬은 각 대각 블록의 역행렬을 대각에 놓은 것이다."],
    "2.cof": ["여인수 전개", "M_ij는 i행과 j열을 지운 행렬, |M_ij|는 minor, A_ij=(−1)^{i+j}|M_ij|는 cofactor다. |A|=a_i1A_i1+⋯+a_inA_in으로 아무 행이나 열로 전개해도 되므로 0이 많은 행이나 열을 고른다. n×n 하나에 (n−1)×(n−1) 행렬식 n개가 필요하다."],
    "2.prop": ["행렬식의 기본 성질", "행렬식은 스칼라이며 절댓값이 아니다. |A^T|=|A|. triangular이면 대각성분의 곱. 영행(영열), 같은 두 행(열), 상수배인 두 행(열)이 있으면 0. A가 nonsingular ⇔ |A|≠0."],
    "2.row": ["행연산과 행렬식", "|E_1|=−1(두 행 교환), |E_2|=α(한 행에 α배), |E_3|=1(한 행의 상수배를 다른 행에 더함), |EA|=|E||A|. |αA|=α^n|A|(n×n). 여인수 성질: a_i1A_j1+⋯+a_inA_jn은 i=j이면 |A|, i≠j이면 같은 행이 두 개인 행렬의 행렬식이라 0. 행 교환은 type III 세 번과 type II(α=−1) 한 번으로 만들 수 있어 부호가 바뀐다."],
    "2.mult": ["곱과 역행렬의 행렬식", "A가 singular ⇔ |A|=0. |AB|=|A||B|(행렬식은 스칼라라 순서 무관). |A^{-1}|=1/|A|는 |AA^{-1}|=|I|=1에서 나온다."],
    "2.adj": ["수반행렬", "adj A는 cofactor 행렬을 전치한 것으로 (i,j) 성분이 A_ji다. 여인수 성질에서 A(adj A)=|A|I, 따라서 A^{-1}=adj A/|A|. 2×2는 대각성분을 서로 바꾸고 나머지 두 성분의 부호를 바꾼 것을 |A|로 나눈다. (정리) A(adj A)=|A|I의 행렬식을 취하면 n×n에서 |adj A|=|A|^{n−1}(|A|≠0일 때), 그리고 adj A=|A|A^{-1}이다. A^{-1}의 (i,j) 성분은 A_ji/|A|(전치 주의)."],
    "2.cramer": ["크라메르 공식", "n×n Ax=b이고 |A|≠0이면 x_i=|A_i|/|A|, A_i는 A의 i번째 열을 b로 바꾼 행렬이다. x=adj A·b/|A|에서 나온다. 행렬식 n+1개가 필요해 전체 해는 가우스 소거가 낫고, 특정 미지수 하나만 필요할 때 유리하다."],
    "2.vol": ["부피로서의 행렬식", "|a_1 a_2|는 a_1, a_2가 만드는 평행사변형의 (부호 있는) 넓이, 3×3은 평행육면체의 부피다. 한 열에 다른 열의 상수배를 더하는 것(type III)은 도형을 밀기(shear)만 해서 밑변과 높이가 그대로라 넓이(부피)가 변하지 않는다."],
}

# 2-vol-2 그림: a1=(2,0), a2=(1,3)이 만드는 평행사변형 (1칸 = 20px, 원점 (20,80))
SHEAR_SVG = (
    '<svg viewBox="0 0 300 100" width="300" height="100" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">'
    '<g stroke="var(--muted)" stroke-width="0.5">'
    + "".join(f'<line x1="{20 + 20 * i}" y1="10" x2="{20 + 20 * i}" y2="90"/>' for i in range(14))
    + "".join(f'<line x1="10" y1="{20 + 20 * j}" x2="290" y2="{20 + 20 * j}"/>' for j in range(4))
    + '</g>'
    '<polygon points="20,80 60,80 80,20 40,20" fill="var(--accent)" fill-opacity="0.25" stroke="var(--accent)" stroke-width="2"/>'
    '<polygon points="20,80 60,80 280,20 240,20" fill="none" stroke="var(--claude)" stroke-width="2" stroke-dasharray="6 4"/>'
    '<text x="44" y="95" font-size="11" fill="currentColor">a₁</text>'
    '<text x="22" y="48" font-size="11" fill="currentColor">a₂</text>'
    '<text x="200" y="14" font-size="11" fill="var(--claude)">a₂ + 5a₁</text>'
    '</svg>'
)

def S(id, c, q, ans, e, hints=None, work=None, **kw):
    d = {"id": id, "c": c, "t": "short", "q": q, "ans": ans, "e": e, **kw}
    if hints:
        d["hints"] = hints
    if work:
        d["work"] = work
    return d


BR = "<br>"


def OH(id, c, q, a, hints=None, work=None, alts=None):
    """서술형. a는 근거 한 갈래로 쓰고, 같은 점수를 받는 다른 근거는 alts에 둔다(둘 다 요구하지 않게)."""
    d = O(id, c, q, a)
    if alts:
        d["alts"] = alts
    if hints:
        d["hints"] = hints
    if work:
        d["work"] = work
    return d


Q = [
    # 1.system
    S("1-sys-1", "1.system", r"연립방정식 $x+2y=3$, $2x+4y=k$의 해가 무수히 많아지는 $k$를 구하시오.", "6",
      r"두 번째 식의 계수 $(2,4)$는 첫 번째 식 $(1,2)$의 2배입니다. 상수도 2배인 $k=6$이면 두 식이 같은 직선이라 해가 무수히 많습니다. $k\neq6$이면 두 직선이 평행해 해가 없고(inconsistent), 유일해는 어떤 $k$로도 나오지 않습니다.",
      ["두 직선이 겹치려면 두 번째 식이 첫 번째 식의 몇 배여야 할까요?"]),
    # 1.ge
    OH("1-ge-4", "1.ge", "가우스 소거와 가우스-요르당 소거의 차이를 설명하시오.",
       "가우스 소거는 pivot <b>아래</b>만 0으로 만들어 triangular form(row echelon form)을 만든 뒤, 아래 식부터 대입하는 back substitution으로 해를 구합니다. 가우스-요르당 소거는 pivot 아래를 0으로 만든 뒤 pivot <b>위</b>도 0으로 만들고, 각 행을 pivot으로 나눠 $[A\\,|\\,b]\\to[I\\,|\\,x]$ 꼴로 만들어 해를 바로 읽습니다.",
       ["두 방법이 각각 어떤 꼴의 행렬에서 멈추는지 생각해 보세요."]),
    S("1-ge-5", "1.ge", r"가우스 소거로 연립방정식 $x_1+x_2+x_3=6$, $2x_1+3x_2+x_3=11$, $x_1+2x_2+3x_3=14$를 풀어 $(x_1,x_2,x_3)$을 쓰시오.", "(1, 2, 3)",
      r"첨가행렬에서 2행 −= 2×1행, 3행 −= 1행을 하면 $\begin{bmatrix}1&1&1&\vert&6\\0&1&-1&\vert&-1\\0&1&2&\vert&8\end{bmatrix}$, 3행 −= 2행을 하면 3행이 $[0\ 0\ 3\,|\,9]$가 됩니다. back substitution으로 $x_3=3$, $x_2=-1+3=2$, $x_1=6-2-3=1$입니다.",
      ["1행으로 2행과 3행의 $x_1$을 먼저 없앱니다.", "triangular form이 되면 맨 아래 식부터 대입합니다."], "photo"),
    # 1.ref
    S("1-ref-1", "1.ref", r"미지수가 $x_1,x_2,x_3$인 연립방정식의 첨가행렬을 소거해 $\begin{bmatrix}1&2&0&\vert&3\\0&0&1&\vert&4\\0&0&0&\vert&0\end{bmatrix}$을 얻었다. free variable을 쓰시오.", ["x2", "x_2"],
      r"각 행의 첫 0이 아닌 성분은 1열과 3열이므로 lead variable은 $x_1,x_3$이고 $x_2$가 free variable입니다. 마지막 행은 $0=0$이라 모순이 없고, free variable이 있어 해가 무수히 많습니다($x_3=4$, $x_1=3-2x_2$).",
      ["각 행에서 처음으로 0이 아닌 성분이 어느 열에 있는지 보세요."]),
    M("1-ref-3", "1.ref", "방정식 3개, 미지수 5개인 연립방정식(underdetermined system)에 대해 항상 옳은 것은?",
      ["해가 있다면 반드시 무수히 많다", "항상 유일해가 있다", "항상 해가 없다", "해가 있다면 유일하다"], 0,
      "lead variable은 행마다 최대 하나라 많아야 3개입니다. 미지수가 5개이므로 free variable이 적어도 2개 생깁니다. 그래서 해가 있으면 무수히 많습니다. 다만 (0 … 0 | c≠0) 행이 생기면 해가 없을 수도 있어 '항상 해가 있다'고는 할 수 없습니다."),
    M("1-ref-4", "1.ref", "4×4 연립방정식 $Ax=b$에서, 계수행렬 $A$의 row echelon form에 영행이 하나 생겼다. 가능한 해의 경우는?",
      ["해가 없거나 무수히 많다", "반드시 유일해다", "반드시 해가 없다", "반드시 무수히 많다"], 0,
      "계수 부분에 영행이 있으면 lead variable이 3개 이하라 free variable이 생깁니다. 그 행의 상수가 0이면 모순이 없어 해가 무수히 많고, 0이 아니면 $0=c$가 되어 해가 없습니다. 어느 쪽이든 유일해는 아닙니다."),
    S("1-ref-5", "1.ref", r"연립방정식 $x+y+z=1$, $x+2y+3z=2$, $2x+3y+4z=k$가 해를 가지도록 하는 $k$를 구하시오.", "3",
      r"세 번째 식의 계수 $(2,3,4)$는 첫째와 둘째 식의 계수를 더한 것입니다. 소거하면 3행이 $[0\ 0\ 0\,|\,k-3]$이 되므로, $k=3$이어야 $0=0$이 되어 해가 있습니다(이때 free variable이 있어 무수히 많음). $k\neq3$이면 inconsistent입니다.",
      ["세 번째 식의 계수가 다른 두 식의 계수와 어떤 관계인지 보세요.", "소거 후 마지막 행이 $(0\\ 0\\ 0\\,|\\,c)$ 꼴이 되면 $c$가 0이어야 합니다."]),
    # 1.alg
    S("1-alg-2", "1.alg", r"$A=\begin{bmatrix}1&2\\3&4\end{bmatrix}$, $B=\begin{bmatrix}2&0\\1&5\end{bmatrix}$일 때 $AB$의 (2,1) 성분을 구하시오.", "10",
      r"(2,1) 성분은 $A$의 2행과 $B$의 1열의 곱입니다: $3\cdot2+4\cdot1=10$. 곱 전체를 구할 필요가 없습니다. 순서를 바꾼 $BA$의 (2,1) 성분은 16이라 값이 다릅니다($AB\neq BA$).",
      ["$c_{ij}$는 $A$의 $i$행과 $B$의 $j$열의 곱입니다."]),
    M("1-alg-3", "1.alg", "$n\\times n$ 행렬 $A$, $B$에 대해 항상 성립하는 것은?",
      ["$(A+B)^2=A^2+AB+BA+B^2$", "$(A+B)^2=A^2+2AB+B^2$", "$AB=BA$", "$(AB)^2=A^2B^2$"], 0,
      "분배법칙으로 $(A+B)(A+B)=A^2+AB+BA+B^2$입니다. $AB\\neq BA$일 수 있어 $AB+BA$를 $2AB$로 합칠 수 없고, $(AB)^2=ABAB$도 $A^2B^2$와 같다고 할 수 없습니다."),
    OH("1-alg-4", "1.alg", "2×2 행렬의 곱셈에서 교환법칙 $AB=BA$가 일반적으로 성립하지 않음을 보이는 예를 들고, 계산으로 확인하시오.",
       r"예: $A=\begin{bmatrix}1&1\\0&0\end{bmatrix}$, $B=\begin{bmatrix}1&0\\1&0\end{bmatrix}$. $AB=\begin{bmatrix}2&0\\0&0\end{bmatrix}$, $BA=\begin{bmatrix}1&1\\1&1\end{bmatrix}$이므로 $AB\neq BA$입니다.",
       ["0과 1만 쓴 간단한 행렬로 시도해 보세요."],
       alts=["$AB\\neq BA$인 어떤 2×2 예라도, 두 곱을 직접 계산해 다름을 보이면 맞습니다."]),
    S("1-alg-5", "1.alg", r"$A=\begin{bmatrix}1&1\\0&1\end{bmatrix}$일 때 $A^3$을 구하시오.", "[1 3; 0 1]",
      r"$A^2=\begin{bmatrix}1&2\\0&1\end{bmatrix}$, $A^3=A^2A=\begin{bmatrix}1&3\\0&1\end{bmatrix}$입니다. 곱할 때마다 (1,2) 성분이 1씩 늘어납니다.",
      ["$A^2$부터 구해 보세요."]),
    # 1.trans
    OH("1-tr-1", "1.trans", "곱이 정의되는 행렬 $A$, $B$, $C$에 대해 $(ABC)^T$를 $A^T$, $B^T$, $C^T$로 나타내고, $(AB)^T=B^TA^T$를 이용해 이유를 보이시오.",
       "$(ABC)^T=((AB)C)^T=C^T(AB)^T=C^TB^TA^T$입니다. $(AB)^T=B^TA^T$를 $AB$와 $C$의 곱에 한 번, $A$와 $B$의 곱에 한 번 써서 곱의 순서가 완전히 뒤집힙니다.",
       ["$ABC$를 $(AB)$와 $C$의 곱으로 보세요."]),
    OH("1-tr-2", "1.trans", "임의의 $m\\times n$ 행렬 $A$에 대해 $A^TA$의 크기를 쓰고, $A^TA$가 대칭행렬임을 보이시오.",
       "$A^T$는 $n\\times m$이므로 $A^TA$는 $n\\times n$입니다. $(A^TA)^T=A^T(A^T)^T=A^TA$이므로 symmetric입니다($(AB)^T=B^TA^T$와 $(A^T)^T=A$를 씀).",
       ["대칭이라는 것은 전치해도 자기 자신이라는 뜻입니다."]),
    M("1-tr-3", "1.trans", "$A$, $B$가 $n\\times n$ 대칭행렬일 때 항상 대칭인 것은?",
      ["$A+B$", "$AB$", "$AB-BA$", "$A^TB$"], 0,
      "$(A+B)^T=A^T+B^T=A+B$입니다. $(AB)^T=B^TA^T=BA$라서 $AB=BA$일 때만 대칭입니다. $A^TB=AB$도 마찬가지이고, $(AB-BA)^T=BA-AB$는 부호가 반대가 됩니다."),
    # 1.inv
    M("1-inv-1", "1.inv", "$A$, $B$가 nonsingular $n\\times n$ 행렬일 때 $(A^{-1}B)^{-1}$은?",
      ["$B^{-1}A$", "$AB^{-1}$", "$A^{-1}B^{-1}$", "$B^{-1}A^{-1}$"], 0,
      "$(XY)^{-1}=Y^{-1}X^{-1}$에 $X=A^{-1}$, $Y=B$를 넣으면 $B^{-1}(A^{-1})^{-1}=B^{-1}A$입니다. 확인: $(A^{-1}B)(B^{-1}A)=A^{-1}A=I$."),
    OH("1-inv-2", "1.inv", "$n\\times n$ 행렬 $A$가 $A^2-3A+2I=O$를 만족한다. $A$가 nonsingular임을 보이고 $A^{-1}$을 $A$와 $I$로 나타내시오.",
       "식을 $A(3I-A)=2I$로 바꾸면 $A\\cdot\\frac12(3I-A)=I$이고, 같은 방법으로 $\\frac12(3I-A)A=I$도 성립합니다. 따라서 $A$는 nonsingular이고 $A^{-1}=\\frac12(3I-A)$입니다. 행렬의 나눗셈은 없으므로 이렇게 $I$를 만드는 꼴로 정리합니다.",
       ["$A$를 포함한 항을 한쪽으로 모아 $A(\\cdots)=cI$ 꼴을 만들어 보세요."]),
    M("1-inv-3", "1.inv", "$A$가 nonsingular $n\\times n$ 행렬이고 $AB=AC$일 때 옳은 것은?",
      ["$B=C$이다", "$B\\neq C$일 수 있다", "$BA=CA$만 알 수 있다", "$A=I$이다"], 0,
      "양변의 왼쪽에 $A^{-1}$을 곱하면 $A^{-1}AB=A^{-1}AC$, 즉 $B=C$입니다. $A$가 singular이면 이 소거가 안 되어 $B\\neq C$일 수 있습니다."),
    OH("1-inv-4", "1.inv", "$A$, $B$가 nonsingular $n\\times n$ 행렬일 때 $(AB)^{-1}=B^{-1}A^{-1}$임을 보이시오.",
       "$B^{-1}A^{-1}$을 $AB$에 양쪽 순서로 곱해 $I$가 됨을 보이면 됩니다. $(B^{-1}A^{-1})(AB)=B^{-1}(A^{-1}A)B=B^{-1}B=I$이고, $(AB)(B^{-1}A^{-1})=A(BB^{-1})A^{-1}=AA^{-1}=I$입니다. 따라서 역행렬의 정의에 따라 $(AB)^{-1}=B^{-1}A^{-1}$입니다. 결합법칙을 썼다는 점이 핵심입니다.",
       ["역행렬의 정의는 양쪽에서 곱해 모두 $I$가 되는 것입니다."]),
    # 1.elem
    M("1-el-1", "1.elem", r"3×3 행렬 $A$의 왼쪽에 $E=\begin{bmatrix}1&0&0\\0&1&0\\-2&0&1\end{bmatrix}$를 곱하면, $A$에 어떤 행연산을 한 것과 같은가?",
      ["3행에서 1행의 2배를 뺀다", "1행에서 3행의 2배를 뺀다", "3행에 $-2$를 곱한다", "1열에서 3열의 2배를 뺀다"], 0,
      r"$E$는 $I$의 3행에 1행의 $-2$배를 더한 type III 기본행렬입니다. 왼쪽에 곱하면 $A$에 같은 행연산을 합니다. 열 연산은 오른쪽에 곱할 때 일어납니다."),
    S("1-el-2", "1.elem", r"type III 기본행렬 $E=\begin{bmatrix}1&0&0\\4&1&0\\0&0&1\end{bmatrix}$의 역행렬을 구하시오.", "[1 0 0; -4 1 0; 0 0 1]",
      "$E$는 '2행에 1행의 4배를 더한다'이므로 되돌리려면 '2행에서 1행의 4배를 뺀다', 즉 $c\\to-c$입니다. $\\frac14$로 바꾸는 것은 type II의 역행렬 규칙입니다.",
      ["$E$가 한 행연산을 되돌리는 행연산은 무엇일까요?"]),
    S("1-el-3", "1.elem", r"$E_1=\begin{bmatrix}0&1&0\\1&0&0\\0&0&1\end{bmatrix}$(1행과 2행 교환), $E_2=\begin{bmatrix}5&0&0\\0&1&0\\0&0&1\end{bmatrix}$(1행에 5를 곱함)일 때 $(E_1E_2)^{-1}$을 구하시오.", "[0 1/5 0; 1 0 0; 0 0 1]",
      r"$(E_1E_2)^{-1}=E_2^{-1}E_1^{-1}=E_2^{-1}E_1$입니다($E_1^{-1}=E_1$). $E_2^{-1}$은 1행에 $\frac15$을 곱하므로, $E_1$의 1행 $[0\ 1\ 0]$에 $\frac15$을 곱해 $\begin{bmatrix}0&\frac15&0\\1&0&0\\0&0&1\end{bmatrix}$입니다. 순서를 바꾼 $E_1E_2^{-1}$은 $\begin{bmatrix}0&1&0\\\frac15&0&0\\0&0&1\end{bmatrix}$로 다릅니다.",
      ["$(AB)^{-1}=B^{-1}A^{-1}$로 순서를 먼저 정하세요.", "$E_2^{-1}$을 왼쪽에 곱하는 것은 1행에 $\\frac15$을 곱하는 행연산입니다."]),
    M("1-el-4", "1.elem", "기본행렬 $E_1$, $E_2$, $E_3$에 대해 $E_3E_2E_1A=I$일 때 $A$는?",
      ["$E_1^{-1}E_2^{-1}E_3^{-1}$", "$E_3^{-1}E_2^{-1}E_1^{-1}$", "$E_1E_2E_3$", "$E_3E_2E_1$"], 0,
      "$E_3E_2E_1=A^{-1}$이므로 $A=(E_3E_2E_1)^{-1}=E_1^{-1}E_2^{-1}E_3^{-1}$입니다. $E_3E_2E_1$은 $A$가 아니라 $A^{-1}$입니다."),
    OH("1-el-5", "1.elem", "$[A\\,|\\,I]$에 행연산을 해서 $[I\\,|\\,A^{-1}]$을 얻을 수 있는 이유를 기본행렬로 설명하시오.",
       "행연산은 기본행렬을 왼쪽에 곱하는 것입니다. $A$를 $I$로 만드는 행연산을 $E_1,\\dots,E_k$라 하면 $E_k\\cdots E_1A=I$이므로 $E_k\\cdots E_1=A^{-1}$입니다. 같은 연산을 $[A\\,|\\,I]$ 전체에 하면 $[E_k\\cdots E_1A\\ |\\ E_k\\cdots E_1I]=[I\\,|\\,A^{-1}]$이 됩니다.",
       ["행연산 하나하나를 기본행렬의 곱으로 바꿔 생각해 보세요."]),
    OH("1-el-8", "1.elem", "$AX=I$를 만족하는 $n\\times n$ 행렬 $X=[\\mathbf x_1\\ \\cdots\\ \\mathbf x_n]$를 열별로 보고, $[A\\,|\\,I]$에 가우스-요르당 소거를 해서 $[I\\,|\\,A^{-1}]$을 얻는 것이 연립방정식 $n$개를 한꺼번에 푸는 것임을 설명하시오. (기본행렬의 곱이 아니라 열별 연립방정식으로 설명한다)",
       "$AX=[A\\mathbf x_1\\ \\cdots\\ A\\mathbf x_n]$이고 $I=[\\mathbf e_1\\ \\cdots\\ \\mathbf e_n]$이므로 $AX=I$는 $A\\mathbf x_j=\\mathbf e_j$($j=1,\\dots,n$) 연립방정식 $n$개입니다. 각각은 $[A\\,|\\,\\mathbf e_j]\\to[I\\,|\\,\\mathbf x_j]$로 풀리는데, 계수행렬이 모두 $A$라 행연산이 같습니다. 그래서 오른쪽 열을 한데 모은 $[A\\,|\\,\\mathbf e_1\\cdots\\mathbf e_n]=[A\\,|\\,I]$에 한 번만 소거하면 $[I\\,|\\,\\mathbf x_1\\cdots\\mathbf x_n]=[I\\,|\\,X]$가 되고, $X=A^{-1}$입니다." + BR
       + "<b>채점 요소:</b> $AX$의 $j$열이 $A\\mathbf x_j$라는 분할, $A\\mathbf x_j=\\mathbf e_j$ $n$개, 계수행렬이 같아 행연산을 한 번에 할 수 있다는 점",
       ["$AX$의 $j$번째 열은 무엇일까요?", "$n$개의 연립방정식에서 계수행렬은 모두 같습니다."]),
    S("1-el-6", "1.elem", r"$[A\,|\,I]\to[I\,|\,A^{-1}]$ 방법으로 $A=\begin{bmatrix}1&1&0\\0&1&1\\0&0&1\end{bmatrix}$의 역행렬을 구하시오.", "[1 -1 1; 0 1 -1; 0 0 1]",
      r"이미 upper triangular라 후진 소거만 하면 됩니다. 2행 −= 3행으로 오른쪽이 $\begin{bmatrix}1&0&0\\0&1&-1\\0&0&1\end{bmatrix}$, 1행 −= 2행으로 1행이 $[1\ -1\ 1]$이 되어 $A^{-1}=\begin{bmatrix}1&-1&1\\0&1&-1\\0&0&1\end{bmatrix}$입니다.",
      ["pivot 아래는 이미 0입니다. 아래 행부터 위로 올라가며 pivot 위를 0으로 만드세요."], "photo"),
    # 1.part
    S("1-pt-1", "1.part", r"$A=\begin{bmatrix}1&2\\3&4\end{bmatrix}$, $B=[\mathbf b_1\ \mathbf b_2\ \mathbf b_3]=\begin{bmatrix}1&0&2\\0&1&1\end{bmatrix}$일 때 $AB$의 3번째 열을 구하시오.", "[4; 10]",
      r"$AB=[A\mathbf b_1\ A\mathbf b_2\ A\mathbf b_3]$이므로 3열은 $A\mathbf b_3=\begin{bmatrix}1\cdot2+2\cdot1\\3\cdot2+4\cdot1\end{bmatrix}=\begin{bmatrix}4\\10\end{bmatrix}$입니다. 곱 전체를 구할 필요가 없습니다.",
      ["$AB$의 $j$열은 $A\\mathbf b_j$입니다."]),
    S("1-pt-2", "1.part", r"$M=\begin{bmatrix}2&0&0\\0&1&2\\0&1&3\end{bmatrix}$을 block diagonal 행렬로 보고 $M^{-1}$을 구하시오.", "[1/2 0 0; 0 3 -2; 0 -1 1]",
      r"$M=\begin{bmatrix}A_{11}&O\\O&A_{22}\end{bmatrix}$, $A_{11}=[2]$, $A_{22}=\begin{bmatrix}1&2\\1&3\end{bmatrix}$입니다. 각 블록의 역행렬 $\frac12$과 $\begin{bmatrix}3&-2\\-1&1\end{bmatrix}$($|A_{22}|=1$)을 대각에 놓으면 됩니다.",
      ["대각 블록 두 개로 나눠 각각의 역행렬을 구하세요."]),
    # 2.cof
    S("2-cof-1", "2.cof", r"$A=\begin{bmatrix}1&2&3\\4&5&6\\7&8&10\end{bmatrix}$에서 $a_{12}$의 cofactor $A_{12}$를 구하시오.", "2",
      r"$M_{12}$는 1행과 2열을 지운 $\begin{bmatrix}4&6\\7&10\end{bmatrix}$이고 minor는 $40-42=-2$입니다. cofactor는 $(-1)^{1+2}\cdot(-2)=2$입니다. minor와 cofactor를 헷갈리면 $-2$가 나옵니다.",
      ["$A_{ij}=(-1)^{i+j}|M_{ij}|$입니다."]),
    S("2-cof-2", "2.cof", r"$\begin{vmatrix}1&0&0&2\\3&0&4&1\\0&0&0&5\\2&1&3&0\end{vmatrix}$의 값을 구하시오.", "20",
      r"0이 많은 2열로 전개하면 $1\cdot(-1)^{4+2}\begin{vmatrix}1&0&2\\3&4&1\\0&0&5\end{vmatrix}$이고, 이것을 3행으로 전개하면 $5\cdot(-1)^{3+3}\begin{vmatrix}1&0\\3&4\end{vmatrix}=5\cdot4=20$입니다.",
      ["0이 가장 많은 열을 찾아 전개하세요.", "남은 3×3도 0이 많은 행으로 한 번 더 전개합니다."], "photo"),
    S("2-cof-4", "2.cof", r"$\begin{vmatrix}2&1&3\\1&0&2\\4&1&1\end{vmatrix}$의 값을 여인수 전개로 구하시오.", "6",
      r"0이 있는 2행으로 전개하면 $1\cdot(-1)^{2+1}\begin{vmatrix}1&3\\1&1\end{vmatrix}+0+2\cdot(-1)^{2+3}\begin{vmatrix}2&1\\4&1\end{vmatrix}=-(1-3)-2(2-4)=2+4=6$입니다. 부호 $(-1)^{i+j}$를 빠뜨리면 $-2-4=-6$처럼 틀린 값이 나옵니다.",
      ["0이 있는 행이나 열을 고르세요.", "각 항의 부호 $(-1)^{i+j}$를 따로 적어 두면 실수가 줄어듭니다."], "photo"),
    # 2.prop
    M("2-pr-1", "2.prop", "다음 중 계산하지 않고도 행렬식이 0임을 알 수 있는 것은?",
      [r"$\begin{bmatrix}1&2&3\\2&4&6\\0&1&5\end{bmatrix}$", r"$\begin{bmatrix}1&2\\3&4\end{bmatrix}$", r"$\begin{bmatrix}2&1&7\\0&3&1\\0&0&5\end{bmatrix}$", r"$\begin{bmatrix}0&1\\1&0\end{bmatrix}$"], 0,
      "2행이 1행의 2배인 행렬은 계산하지 않아도 행렬식이 0입니다. 나머지는 각각 $-2$, triangular라 대각곱 $30$, 행 교환한 $I$라 $-1$입니다."),
    M("2-pr-3", "2.prop", "정사각행렬 $A$에 대한 설명으로 옳지 <b>않은</b> 것은?",
      ["$|A|=0$이면 $A$에는 반드시 영행이 있다", "성분이 모두 0인 열이 있으면 $|A|=0$이다", "같은 두 열이 있으면 $|A|=0$이다", "$A$가 triangular이면 $|A|$는 대각성분의 곱이다"], 0,
      r"영행이 있으면 0이지만, 거꾸로 $|A|=0$이라고 영행이 있는 것은 아닙니다. 예: $\begin{bmatrix}1&2\\2&4\end{bmatrix}$는 영행이 없지만 두 행이 상수배라 행렬식이 0입니다."),
    # 2.row
    S("2-row-1", "2.row", "$|A|=5$인 3×3 행렬 $A$의 1행과 3행을 바꾸고, 그다음 2행에 3을 곱한 행렬을 $B$라 하자. $|B|$를 구하시오.", "-15",
      "행 교환은 $|E_1|=-1$, 한 행에 3배는 $|E_2|=3$이므로 $|B|=3\\cdot(-1)\\cdot5=-15$입니다. 한 행에만 3을 곱했으므로 $3^3$이 아닙니다.",
      ["각 행연산이 행렬식에 무엇을 곱하는지 따로 생각하세요."]),
    S("2-row-2", "2.row", "$|A|=2$인 4×4 행렬 $A$에 대해 $|3A|$를 구하시오.", "162",
      "$3A$는 네 행 모두에 3이 곱해진 것이므로 $|3A|=3^4|A|=81\\cdot2=162$입니다($|\\alpha A|=\\alpha^n|A|$).",
      ["$3A$는 몇 개의 행에 3이 곱해진 것일까요?"]),
    S("2-row-3", "2.row", "$|A|=7$인 3×3 행렬 $A$의 2행에 1행의 4배를 더한 행렬의 행렬식을 구하시오.", "7",
      "type III 행연산은 $|E_3|=1$이라 행렬식을 바꾸지 않습니다. 새 행으로 전개하면 원래 행렬식과 '같은 행이 두 개인 행렬식(0)'의 4배의 합이 되기 때문입니다.",
      ["이 행연산은 어떤 type의 기본행렬일까요?"]),
    S("2-row-4", "2.row", "$|A|=6$인 3×3 행렬 $A=(a_{ij})$와 그 cofactor $A_{ij}$에 대해 $a_{11}A_{21}+a_{12}A_{22}+a_{13}A_{23}$의 값을 구하시오.", "0",
      "1행 성분에 2행의 cofactor를 곱한 합($i\\neq j$)입니다. 이것은 $A$의 2행을 1행으로 바꾼 행렬을 2행으로 전개한 값인데, 그 행렬은 같은 행이 두 개라 행렬식이 0입니다.",
      ["성분은 1행, cofactor는 2행입니다. 행 번호가 같을 때와 다를 때를 구분하세요."]),
    OH("2-row-5", "2.row", "두 행을 교환하면 행렬식의 부호가 바뀌는 이유를, 다른 두 가지 행연산의 성질을 이용해 설명하시오.",
       "행 교환은 type III 연산 세 번과 type II($\\alpha=-1$) 한 번으로 만들 수 있습니다: $\\begin{bmatrix}r_2\\\\r_3\\end{bmatrix}\\to\\begin{bmatrix}r_2-r_3\\\\r_3\\end{bmatrix}\\to\\begin{bmatrix}r_2-r_3\\\\r_2\\end{bmatrix}\\to\\begin{bmatrix}-r_3\\\\r_2\\end{bmatrix}\\to\\begin{bmatrix}r_3\\\\r_2\\end{bmatrix}$. type III는 행렬식을 바꾸지 않고($|E_3|=1$), 한 행에 $-1$을 곱하면 행렬식에 $-1$이 곱해지므로($|E_2|=\\alpha$) 전체적으로 $|E_1A|=-|A|$입니다.",
       ["행 교환을 '한 행에 다른 행을 더하거나 빼는' 연산 몇 번으로 만들 수 있을까요?", "마지막에 부호를 바꾸는 연산이 하나 필요합니다."]),
    S("2-row-6", "2.row", r"행연산으로 triangular form을 만들어 $\begin{vmatrix}1&2&3\\2&5&7\\3&7&11\end{vmatrix}$의 값을 구하시오.", "1",
      r"2행 −= 2×1행, 3행 −= 3×1행(type III라 값 그대로)으로 $\begin{vmatrix}1&2&3\\0&1&1\\0&1&2\end{vmatrix}$, 3행 −= 2행으로 $\begin{vmatrix}1&2&3\\0&1&1\\0&0&1\end{vmatrix}$가 됩니다. 대각곱은 $1\cdot1\cdot1=1$입니다.",
      ["type III 행연산만 쓰면 행렬식이 변하지 않습니다.", "triangular가 되면 대각성분만 곱합니다."], "photo"),
    # 2.mult
    S("2-mul-1", "2.mult", "$|A|=2$, $|B|=-3$인 3×3 행렬 $A$, $B$에 대해 $|A^{-1}B^T|$를 구하시오.", "-3/2",
      "$|A^{-1}B^T|=|A^{-1}||B^T|=\\frac{1}{|A|}\\cdot|B|=\\frac12\\cdot(-3)=-\\frac32$입니다.",
      ["$|AB|=|A||B|$로 나눠서 각각 구하세요."]),
    M("2-mul-2", "2.mult", "$n\\times n$ 행렬 $A$, $B$에 대해 $|AB|=0$이면?",
      ["$A$와 $B$ 중 적어도 하나는 singular다", "$A$와 $B$ 둘 다 singular다", "$A=O$이거나 $B=O$다", "$AB=O$다"], 0,
      "$|AB|=|A||B|=0$이므로 $|A|=0$ 또는 $|B|=0$, 즉 적어도 하나가 singular입니다. 행렬식이 0이라고 행렬이 영행렬인 것은 아닙니다."),
    S("2-mul-3", "2.mult", "nonsingular $n\\times n$ 행렬 $A$가 $A^2=A$를 만족할 때 $|A|$를 구하시오.", "1",
      "$|A|^2=|A|$이므로 $|A|=0$ 또는 $1$인데, nonsingular이면 $|A|\\neq0$이라 $|A|=1$입니다. (실제로 양변에 $A^{-1}$을 곱하면 $A=I$입니다.)",
      ["양변에 행렬식을 취해 보세요."]),
    OH("2-mul-5", "2.mult", "$A$가 nonsingular일 때 $|A^{-1}|=\\dfrac{1}{|A|}$임을 보이시오.",
       "$AA^{-1}=I$의 양변에 행렬식을 취하고 $|AB|=|A||B|$를 쓰면 $|A||A^{-1}|=|I|=1$입니다. $A$가 nonsingular라 $|A|\\neq0$이므로 $|A^{-1}|=\\frac{1}{|A|}$입니다.",
       ["$AA^{-1}=I$에서 출발하세요."]),
    # 2.adj
    S("2-adj-1", "2.adj", r"$A=\begin{bmatrix}3&5\\1&2\end{bmatrix}$의 역행렬을 구하시오.", "[2 -5; -1 3]",
      r"$|A|=6-5=1$입니다. 2×2는 대각성분을 서로 바꾸고 나머지 두 성분의 부호를 바꾼 adj A를 $|A|$로 나누므로 $A^{-1}=\begin{bmatrix}2&-5\\-1&3\end{bmatrix}$입니다.",
      ["$|A|$부터 구하세요."]),
    S("2-adj-2", "2.adj", "$|A|=2$인 3×3 행렬 $A$에 대해 $|\\operatorname{adj}A|$를 구하시오.", "4",
      "$A(\\operatorname{adj}A)=|A|I=2I$의 행렬식을 취하면 $|A||\\operatorname{adj}A|=|2I|=2^3=8$이므로 $|\\operatorname{adj}A|=8/2=4$입니다.",
      ["$A(\\operatorname{adj}A)=|A|I$의 양변에 행렬식을 취해 보세요.", "$|2I|$는 3×3에서 $2^3$입니다."]),
    S("2-adj-3", "2.adj", r"$A=\begin{bmatrix}1&2&3\\0&1&4\\5&6&0\end{bmatrix}$의 수반행렬 $\operatorname{adj}A$의 (1,2) 성분을 구하시오.", "18",
      r"adj A는 cofactor 행렬의 전치이므로 (1,2) 성분은 $A_{21}=(-1)^{2+1}\begin{vmatrix}2&3\\6&0\end{vmatrix}=-(0-18)=18$입니다. 전치하지 않은 $A_{12}$는 20입니다.",
      ["adj A는 cofactor 행렬을 전치한 것입니다. (1,2) 성분은 어느 cofactor일까요?"]),
    OH("2-adj-4", "2.adj", "$A(\\operatorname{adj}A)=|A|I$가 성립하는 이유를 여인수 성질로 설명하시오.",
       "$A(\\operatorname{adj}A)$의 $(i,j)$ 성분은 $A$의 $i$행과 adj A의 $j$열(= $A$의 $j$행 cofactor)의 곱 $a_{i1}A_{j1}+\\cdots+a_{in}A_{jn}$입니다. 여인수 성질에 따라 이 값은 $i=j$이면 $|A|$($i$행 전개), $i\\neq j$이면 같은 행이 두 개인 행렬의 행렬식이라 0입니다. 따라서 대각성분만 $|A|$인 $|A|I$가 됩니다.",
       ["곱의 $(i,j)$ 성분을 성분과 cofactor로 써 보세요."]),
    S("2-adj-5", "2.adj", r"$A=\begin{bmatrix}1&2&3\\0&1&4\\5&6&0\end{bmatrix}$의 행렬식은 1이다. $A^{-1}=\frac{1}{|A|}\operatorname{adj}A$로 $A^{-1}$을 구하시오.", "[-24 18 5; 20 -15 -4; -5 4 1]",
      r"cofactor를 모두 구해 전치합니다. 예: $A_{11}=\begin{vmatrix}1&4\\6&0\end{vmatrix}=-24$, $A_{21}=-\begin{vmatrix}2&3\\6&0\end{vmatrix}=18$, $A_{31}=\begin{vmatrix}2&3\\1&4\end{vmatrix}=5$가 adj A의 1행입니다. $|A|=1$이라 $A^{-1}=\operatorname{adj}A=\begin{bmatrix}-24&18&5\\20&-15&-4\\-5&4&1\end{bmatrix}$입니다.",
      ["cofactor 9개를 구한 뒤 전치하는 것을 잊지 마세요.", "adj A의 1행은 $A_{11}, A_{21}, A_{31}$입니다."], "photo"),
    # 2.cramer
    S("2-cr-1", "2.cramer", "크라메르 공식으로 연립방정식 $2x_1+x_2=5$, $x_1+3x_2=5$의 $x_2$를 구하시오.", "1",
      r"$|A|=\begin{vmatrix}2&1\\1&3\end{vmatrix}=5$, $|A_2|=\begin{vmatrix}2&5\\1&5\end{vmatrix}=5$이므로 $x_2=5/5=1$입니다. ($x_1=2$)",
      ["$A_2$는 $A$의 몇 번째 열을 $b$로 바꾼 것일까요?"]),
    S("2-cr-4", "2.cramer", r"크라메르 공식으로 연립방정식 $x_1+x_2+x_3=6$, $x_1+2x_2+x_3=8$, $x_1+x_2+2x_3=9$의 $x_3$을 구하시오.", "3",
      r"$|A|=\begin{vmatrix}1&1&1\\1&2&1\\1&1&2\end{vmatrix}=1$, $|A_3|=\begin{vmatrix}1&1&6\\1&2&8\\1&1&9\end{vmatrix}=3$이므로 $x_3=3$입니다. 두 행렬식 모두 1행을 2행·3행에서 빼면(type III) triangular에 가까워져 빨리 계산됩니다.",
      ["$|A|$와 $|A_3|$ 두 개만 구하면 됩니다.", "1행을 다른 행에서 빼면(type III) 행렬식이 변하지 않으면서 0이 생깁니다."], "photo"),
    OH("2-cr-5", "2.cramer", "$|A|\\neq0$인 $n\\times n$ 연립방정식 $Ax=b$에서 크라메르 공식 $x_i=\\dfrac{|A_i|}{|A|}$가 성립하는 이유를 설명하시오.",
       "$x=A^{-1}b=\\frac{1}{|A|}(\\operatorname{adj}A)b$입니다. adj A의 $i$행은 $A_{1i},\\dots,A_{ni}$이므로 $x_i=\\frac{1}{|A|}(b_1A_{1i}+b_2A_{2i}+\\cdots+b_nA_{ni})$입니다. 괄호 안은 $A$의 $i$번째 열을 $b$로 바꾼 행렬 $A_i$를 $i$열로 전개한 값 $|A_i|$입니다.",
       ["$A^{-1}=\\frac{1}{|A|}\\operatorname{adj}A$에서 출발하세요.", "adj A의 $i$행에는 어떤 cofactor들이 있을까요?"]),
    # 2.vol
    S("2-vol-2", "2.vol", "$\\mathbf a_1=(2,0)$과 $\\mathbf a_2+5\\mathbf a_1$이 만드는 평행사변형의 넓이를 구하시오. 단 $\\mathbf a_2=(1,3)$이다.", "6",
      r"$\mathbf a_1$, $\mathbf a_2$가 만드는 넓이는 $\begin{vmatrix}2&1\\0&3\end{vmatrix}=6$입니다. 한 열에 다른 열의 상수배를 더하는 것(type III)은 도형을 밀기만 해서 밑변(2)과 높이(3)가 그대로이므로 넓이도 6입니다. $\mathbf a_2+5\mathbf a_1=(11,3)$을 직접 넣어도 $\begin{vmatrix}2&11\\0&3\end{vmatrix}=6$입니다.",
      ["그림에서 두 평행사변형의 밑변과 높이를 비교해 보세요."],
      fig={"svg": SHEAR_SVG, "alt": "모눈 위에 원점에서 시작하는 두 평행사변형. 색칠된 것은 a1=(2,0), a2=(1,3)이 만드는 평행사변형이고, 점선은 a1과 a2+5a1=(11,3)이 만드는 평행사변형이다. 두 도형 모두 밑변은 x축 위의 길이 2, 높이는 3이다.",
           "caption": "색칠: a₁, a₂ · 점선: a₁, a₂ + 5a₁"}),
    S("2-vol-3", "2.vol", "3×3 행렬 $A$의 행렬식이 $-4$이다. $2A$의 열벡터 세 개가 만드는 평행육면체의 부피를 구하시오.", "32",
      "$|2A|=2^3\\cdot(-4)=-32$이고, 부피는 부호 있는 부피의 절댓값이므로 32입니다. $A$ 자체의 부피는 4입니다.",
      ["$|\\alpha A|=\\alpha^n|A|$를 쓰고, 부피는 음수가 될 수 없다는 점을 생각하세요."]),
]

# 시험형 서술형 (2026-10-21 교수 공지: 1시간에 서술형 7문제 → 문제당 8분 안팎).
# 소문항 2~3개로, 법칙을 보이거나 끌어낸 뒤 그 법칙으로 계산이 짧게 끝나게 만든다. 수치는 check_exam()에서 검증한다.
EXAM = [
    OH("1-sys-3", "1.system",
       "$n\\times n$ 행렬 $A$와 연립방정식 $Ax=b$에 대해 답하시오." + BR
       + "(a) $Ax=\\mathbf 0$은 항상 해를 가짐을 보이시오." + BR
       + "(b) $|A|\\neq0$이면 $Ax=\\mathbf 0$의 해는 $x=\\mathbf 0$뿐임을 보이시오." + BR
       + "(c) $Ax=b$가 서로 다른 두 해 $x_1$, $x_2$를 가지면, 모든 실수 $t$에 대해 $x_1+t(x_2-x_1)$도 해임을 보이고, 이로부터 연립방정식의 해가 정확히 2개일 수 없는 이유를 설명하시오.",
       "(a) $x=\\mathbf 0$을 넣으면 $A\\mathbf 0=\\mathbf 0$이므로 항상 해가 있습니다(inconsistent일 수 없음)." + BR
       + "(b) $|A|\\neq0$이면 $A$는 nonsingular라 $A^{-1}$이 있습니다. $Ax=\\mathbf 0$의 양변 왼쪽에 $A^{-1}$을 곱하면 $x=A^{-1}\\mathbf 0=\\mathbf 0$입니다." + BR
       + "(c) $A(x_1+t(x_2-x_1))=Ax_1+t(Ax_2-Ax_1)=b+t(b-b)=b$입니다(분배법칙, 스칼라 곱의 성질). $x_2-x_1\\neq\\mathbf 0$이라 $t$마다 다른 해가 나오므로 해가 무수히 많습니다. 따라서 해가 2개 이상이면 무수히 많고, 해의 개수는 0개, 1개, 무수히 많음 중 하나입니다." + BR
       + "<b>채점 요소:</b> (a) 영벡터 대입 (b) 역행렬을 곱하는 근거로 $|A|\\neq0\\Leftrightarrow$ nonsingular (c) 대입 계산과 '$t$마다 다른 해'라는 결론",
       ["(b)는 $|A|\\neq0$이 무엇을 보장하는지부터 떠올리세요.", "(c)는 $Ax_1=Ax_2=b$를 써서 직접 대입해 보세요."]),
    OH("1-ref-6", "1.ref",
       "연립방정식 $x+y+z=1$, $x+2y+3z=2$, $x+3y+az=b$에 대해 답하시오." + BR
       + "(a) 첨가행렬을 row echelon form으로 바꾸고, 해가 유일한 경우, 해가 없는 경우, 해가 무수히 많은 경우의 $a$, $b$ 조건을 각각 쓰시오." + BR
       + "(b) 계수행렬의 행렬식을 $a$로 나타내고, 해가 유일한 조건과 어떤 관계인지 설명하시오." + BR
       + "(c) 해가 무수히 많은 경우의 해를 $z=t$로 놓고 나타내시오.",
       r"(a) 2행 −= 1행, 3행 −= 1행, 3행 −= 2×2행으로 $\begin{bmatrix}1&1&1&\vert&1\\0&1&2&\vert&1\\0&0&a-5&\vert&b-3\end{bmatrix}$입니다. $a\neq5$이면 lead variable이 3개라 유일해, $a=5$이고 $b\neq3$이면 마지막 행이 $(0\ 0\ 0\,|\,c\neq0)$이라 해 없음, $a=5$이고 $b=3$이면 $z$가 free variable이라 해가 무수히 많습니다."
       + BR + r"(b) 쓴 연산이 모두 type III라 행렬식이 변하지 않으므로 $|A|=1\cdot1\cdot(a-5)=a-5$(triangular의 대각곱)입니다. 해가 유일한 조건 $a\neq5$는 $|A|\neq0$, 즉 $A$가 nonsingular인 것과 같습니다. 이때 $x=A^{-1}b$로 하나로 정해집니다."
       + BR + r"(c) $a=5$, $b=3$이면 $y+2z=1$에서 $y=1-2t$, $x=1-y-z=t$이므로 $(x,y,z)=(t,\,1-2t,\,t)$입니다."
       + BR + "<b>채점 요소:</b> (a) 소거 결과와 세 경우의 조건 (b) $|A|=a-5$(type III 불변과 대각곱 또는 여인수 전개), 유일해 ⇔ $|A|\\neq0$ (c) 해의 표현",
       ["세 번째 식의 계수 $(1,3,a)$가 앞의 두 식 계수로 얼마나 만들어지는지 보세요.", "(b)는 (a)에서 쓴 행연산의 type을 보면 계산 없이 끝납니다."], "photo",
       alts=[r"(b)의 행렬식은 계수행렬을 여인수 전개로 직접 계산해 $a-5$를 얻어도 됩니다."]),
    OH("1-alg-6", "1.alg",
       "$n\\times n$ 행렬 $A$가 $A^2=A$를 만족한다." + BR
       + "(a) $(I-A)^2=I-A$이고 $A(I-A)=O$임을 보이시오." + BR
       + "(b) $I+A$가 nonsingular임을 보이고 $(I+A)^{-1}$을 $A$와 $I$로 나타내시오." + BR
       + "(c) $A$가 nonsingular이면 $A=I$임을 보이시오. 이로부터 $A\\neq I$이면 $|A|$의 값은 무엇인지 쓰시오.",
       "(a) $(I-A)^2=I-2A+A^2=I-2A+A=I-A$, $A(I-A)=A-A^2=O$입니다($AI=IA=A$라 전개가 가능)." + BR
       + "(b) $(I+A)(I-\\tfrac12A)=I-\\tfrac12A+A-\\tfrac12A^2=I+\\tfrac12A-\\tfrac12A=I$이고, 반대 순서 $(I-\\tfrac12A)(I+A)$도 같은 계산으로 $I$입니다. 따라서 $(I+A)^{-1}=I-\\tfrac12A$입니다." + BR
       + "(c) $A^2=A$의 양변 왼쪽에 $A^{-1}$을 곱하면 $A=I$입니다. 대우로 $A\\neq I$이면 $A$는 singular이고 $|A|=0$입니다." + BR
       + "<b>채점 요소:</b> (a) $A^2=A$ 대입 (b) 후보를 찾고 양쪽 곱이 $I$임을 확인 (c) $A^{-1}$을 곱함, singular ⇔ $|A|=0$",
       ["(b)는 $(I+A)(I+cA)=I$가 되는 $c$를 찾아 보세요.", "(c)는 $A^{-1}$이 있다고 가정하고 $A^2=A$에 곱해 보세요."]),
    OH("1-tr-4", "1.trans",
       "다음을 보이시오." + BR
       + "(a) $A$가 nonsingular이면 $(A^T)^{-1}=(A^{-1})^T$이다. 이로부터 nonsingular symmetric 행렬의 역행렬도 symmetric이다." + BR
       + "(b) 정사각행렬 $A$에 대해 $S=\\tfrac12(A+A^T)$는 $S^T=S$를, $K=\\tfrac12(A-A^T)$는 $K^T=-K$를 만족한다. 따라서 모든 정사각행렬은 symmetric 행렬과 $K^T=-K$인 행렬의 합이다." + BR
       + "(c) $K^T=-K$인 행렬의 대각성분은 모두 0이다.",
       "(a) $A^T(A^{-1})^T=(A^{-1}A)^T=I^T=I$이고 $(A^{-1})^TA^T=(AA^{-1})^T=I$이므로 $(A^T)^{-1}=(A^{-1})^T$입니다($(AB)^T=B^TA^T$ 사용). $A^T=A$이면 $(A^{-1})^T=(A^T)^{-1}=A^{-1}$이라 symmetric입니다." + BR
       + "(b) $S^T=\\tfrac12(A^T+(A^T)^T)=\\tfrac12(A^T+A)=S$, $K^T=\\tfrac12(A^T-A)=-K$이고, $S+K=A$입니다." + BR
       + "(c) $K^T=-K$의 $(i,i)$ 성분을 비교하면 $k_{ii}=-k_{ii}$이므로 $k_{ii}=0$입니다." + BR
       + "<b>채점 요소:</b> (a) 두 순서의 곱을 모두 확인 (b) 전치 성질 $(A+B)^T$, $(\\alpha A)^T$, $(A^T)^T$ (c) 성분 비교",
       ["(a)는 $(A^{-1})^T$를 $A^T$에 양쪽 순서로 곱해 보세요.", "(c)는 전치해도 대각성분은 그대로라는 점을 쓰세요."]),
    OH("1-inv-5", "1.inv",
       "$n\\times n$ 행렬 $A$가 $A^3=O$를 만족한다." + BR
       + "(a) $I-A$가 nonsingular임을 보이고 $(I-A)^{-1}$을 $A$와 $I$로 나타내시오." + BR
       + r"(b) $A=\begin{bmatrix}0&1&2\\0&0&3\\0&0&0\end{bmatrix}$이 $A^3=O$를 만족함을 확인하고, (a)의 결과로 $\begin{bmatrix}1&-1&-2\\0&1&-3\\0&0&1\end{bmatrix}^{-1}$을 구하시오.",
       "(a) $(I-A)(I+A+A^2)=I+A+A^2-A-A^2-A^3=I-A^3=I$이고, $(I+A+A^2)(I-A)$도 같은 계산으로 $I$입니다. 따라서 $I-A$는 nonsingular이고 $(I-A)^{-1}=I+A+A^2$입니다." + BR
       + r"(b) $A^2=\begin{bmatrix}0&0&3\\0&0&0\\0&0&0\end{bmatrix}$, $A^3=A^2A=O$입니다. 주어진 행렬은 $I-A$이므로 역행렬은 $I+A+A^2=\begin{bmatrix}1&1&5\\0&1&3\\0&0&1\end{bmatrix}$입니다. 소거 없이 곱셈 두 번으로 끝납니다."
       + BR + "<b>채점 요소:</b> (a) 두 순서의 곱이 $I$ (b) $A^2$, $A^3$ 계산과 '주어진 행렬 $=I-A$'라는 인식, 결과 행렬",
       ["수의 공식 $1-x^3=(1-x)(1+x+x^2)$을 행렬로 옮겨 보세요.", "(b)의 행렬이 $A$와 어떤 관계인지 먼저 보세요."]),
    OH("1-el-7", "1.elem",
       r"$A=\begin{bmatrix}2&4&0\\0&1&0\\0&3&1\end{bmatrix}$에 다음 행연산을 차례로 하면 $I$가 된다: ① 1행에 $\frac12$을 곱한다 ② 1행에서 2행의 2배를 뺀다 ③ 3행에서 2행의 3배를 뺀다. 각 연산의 기본행렬을 차례로 $G_1$, $G_2$, $G_3$라 하자."
       + BR + "(a) $G_1$, $G_2$, $G_3$를 쓰고 각각의 type을 밝히시오."
       + BR + "(b) $A^{-1}$과 $A$를 각각 기본행렬의 곱으로 나타내고 $A^{-1}$을 계산하시오."
       + BR + "(c) 기본행렬의 행렬식만 써서 $|A|$를 구하시오.",
       r"(a) $G_1=\begin{bmatrix}\frac12&0&0\\0&1&0\\0&0&1\end{bmatrix}$(type II), $G_2=\begin{bmatrix}1&-2&0\\0&1&0\\0&0&1\end{bmatrix}$(type III), $G_3=\begin{bmatrix}1&0&0\\0&1&0\\0&-3&1\end{bmatrix}$(type III)."
       + BR + r"(b) $G_3G_2G_1A=I$이므로 $A^{-1}=G_3G_2G_1=\begin{bmatrix}\frac12&-2&0\\0&1&0\\0&-3&1\end{bmatrix}$, $A=(G_3G_2G_1)^{-1}=G_1^{-1}G_2^{-1}G_3^{-1}$이고 $G_1^{-1}$은 $\frac12\to2$, $G_2^{-1}$, $G_3^{-1}$은 $c\to-c$입니다."
       + BR + r"(c) $|G_3||G_2||G_1||A|=|I|=1$이고 $|G_1|=\frac12$, $|G_2|=|G_3|=1$이므로 $|A|=2$입니다."
       + BR + "<b>채점 요소:</b> (a) 세 행렬과 type (b) 곱의 순서($A^{-1}=G_3G_2G_1$, $A=G_1^{-1}G_2^{-1}G_3^{-1}$)와 역행렬 규칙 (c) $|E_2|=\\alpha$, $|E_3|=1$",
       ["기본행렬은 $I$에 그 행연산을 한 번 한 행렬입니다.", "$A$는 $(G_3G_2G_1)^{-1}$이고, 곱의 역행렬은 순서가 뒤집힙니다."], "photo"),
    OH("1-pt-3", "1.part",
       r"$A$, $C$는 nonsingular $2\times2$ 행렬, $B$는 $2\times2$ 행렬이고 $M=\begin{bmatrix}A&B\\O&C\end{bmatrix}$이다."
       + BR + r"(a) $M^{-1}=\begin{bmatrix}X&Y\\Z&W\end{bmatrix}$로 놓고 블록 곱 $MM^{-1}=I$에서 $X$, $Y$, $Z$, $W$를 $A$, $B$, $C$로 나타내시오."
       + BR + "(b) 구한 행렬을 $M$의 왼쪽에 곱해도 $I$임을 확인하시오."
       + BR + r"(c) $A=\begin{bmatrix}1&1\\0&1\end{bmatrix}$, $B=I$, $C=\begin{bmatrix}2&1\\1&1\end{bmatrix}$일 때 $Y$를 구하시오.",
       r"(a) $MM^{-1}=\begin{bmatrix}AX+BZ&AY+BW\\CZ&CW\end{bmatrix}=\begin{bmatrix}I&O\\O&I\end{bmatrix}$입니다. $CZ=O$에 $C^{-1}$을 곱해 $Z=O$, $CW=I$에서 $W=C^{-1}$, $AX=I$에서 $X=A^{-1}$, $AY+BC^{-1}=O$에서 $Y=-A^{-1}BC^{-1}$입니다."
       + BR + r"(b) $\begin{bmatrix}A^{-1}&-A^{-1}BC^{-1}\\O&C^{-1}\end{bmatrix}\begin{bmatrix}A&B\\O&C\end{bmatrix}=\begin{bmatrix}I&A^{-1}B-A^{-1}BC^{-1}C\\O&I\end{bmatrix}=I$입니다."
       + BR + r"(c) $A^{-1}=\begin{bmatrix}1&-1\\0&1\end{bmatrix}$, $C^{-1}=\begin{bmatrix}1&-1\\-1&2\end{bmatrix}$($|C|=1$)이므로 $Y=-A^{-1}C^{-1}=\begin{bmatrix}-2&3\\1&-2\end{bmatrix}$입니다."
       + BR + "<b>채점 요소:</b> (a) 블록 곱 전개와 네 블록 (특히 곱의 순서 $A^{-1}BC^{-1}$) (b) 반대 순서 확인 (c) 2×2 역행렬과 결과",
       ["블록 크기가 같으니 블록을 성분처럼 곱해 네 식을 세우세요.", "행렬은 나눌 수 없으니 $A^{-1}$이나 $C^{-1}$을 곱하는 쪽(왼쪽·오른쪽)에 주의하세요."], "photo"),
    OH("2-cof-5", "2.cof",
       r"$A=\begin{bmatrix}2&1&3\\1&0&2\\5&6&7\end{bmatrix}$이고 $A_{ij}$는 $a_{ij}$의 cofactor이다. 각 값을 $A_{31}$, $A_{32}$, $A_{33}$을 따로 계산해 더하지 말고 여인수 성질로 구하시오. (3행을 다른 수로 바꾼 행렬의 행렬식을 계산하는 것은 된다.)"
       + BR + r"(a) $2A_{31}+A_{32}+3A_{33}$"
       + BR + r"(b) $A_{32}+A_{33}$"
       + BR + r"(c) $5A_{31}+6A_{32}+7A_{33}$. 그리고 3행 성분을 다른 수로 바꿔도 $A_{31}$, $A_{32}$, $A_{33}$이 변하지 않는 이유를 쓰시오.",
       r"(a) 1행 성분에 3행의 cofactor를 곱한 합이므로 여인수 성질($i\neq j$이면 0)에 따라 0입니다."
       + BR + r"(b) $0\cdot A_{31}+1\cdot A_{32}+1\cdot A_{33}$은 3행을 $(0,1,1)$로 바꾼 행렬을 3행으로 전개한 값입니다: $\begin{vmatrix}2&1&3\\1&0&2\\0&1&1\end{vmatrix}=2(0-2)-1(1-0)+3(1-0)=-2$."
       + BR + r"(c) 3행으로 전개한 값이므로 $|A|$입니다. 1행으로 전개하면 $|A|=2(0-12)-1(7-10)+3(6-0)=-3$입니다. $A_{3j}=(-1)^{3+j}|M_{3j}|$이고 $M_{3j}$는 3행을 지운 행렬이라 3행 성분과 무관합니다. 그래서 (a)(b)처럼 3행만 바꾼 행렬도 같은 cofactor로 전개됩니다."
       + BR + "<b>채점 요소:</b> (a) 1행 성분과 3행 cofactor라는 인식과 결과 0 (여인수 성질 인용 또는 같은 행이 두 개인 행렬로 설명, 어느 쪽이든 만점) (b) 3행을 바꾼 행렬의 행렬식으로 해석, 값 (c) $|A|$ 값과 '$M_{3j}$에 3행이 없음'",
       ["$\\sum_k c_kA_{3k}$는 3행을 $(c_1,c_2,c_3)$로 바꾼 행렬의 행렬식입니다.", "(c)의 이유는 minor $M_{3j}$를 만들 때 무엇을 지우는지에 있습니다."],
       alts=[r"(a)를 이렇게 써도 됩니다: $A$의 3행을 1행 $(2,1,3)$으로 바꾼 행렬을 3행으로 전개한 값이 $2A_{31}+A_{32}+3A_{33}$인데, 그 행렬은 같은 행이 두 개라 행렬식이 0입니다."]),
    OH("2-row-9", "2.row",
       "$n\\times n$ 행렬 $A$와 cofactor $A_{jk}$에 대해 $i\\neq j$이면 $a_{i1}A_{j1}+a_{i2}A_{j2}+\\cdots+a_{in}A_{jn}=0$이다. 이 성질을 인용하지 말고, 행 하나를 바꾼 행렬의 행렬식으로 이 식이 0인 이유를 설명하시오.",
       "$A$의 $j$행을 $i$행으로 바꾼 행렬을 $A^*$라 하자. $A^*$의 $j$행 성분은 $a_{i1},\\dots,a_{in}$이고, $A^*_{jk}=(-1)^{j+k}|M^*_{jk}|$에서 $M^*_{jk}$는 $j$행을 지운 행렬이라 $A$의 것과 같으므로 $A^*_{jk}=A_{jk}$입니다. 따라서 $A^*$를 $j$행으로 전개하면 $|A^*|=a_{i1}A_{j1}+\\cdots+a_{in}A_{jn}$입니다. 그런데 $A^*$는 $i$행과 $j$행이 같아 $|A^*|=0$입니다." + BR
       + "<b>채점 요소:</b> $j$행을 $i$행으로 바꾼 행렬, $j$행 cofactor가 그대로라는 근거($M_{jk}$에 $j$행이 없음), 같은 두 행이면 행렬식이 0",
       ["식의 성분은 $i$행, cofactor는 $j$행입니다. $j$행 자리에 무엇을 넣은 행렬일까요?", "$j$행으로 전개할 때 쓰는 cofactor는 $j$행 성분과 무관합니다."]),
    OH("2-row-7", "2.row",
       r"$A=\begin{bmatrix}x&1&1\\1&x&1\\1&1&x\end{bmatrix}$이다."
       + BR + "(a) 행연산을 써서 $|A|$를 인수분해된 꼴로 구하시오. 각 연산이 행렬식을 어떻게 바꾸는지 밝히시오."
       + BR + "(b) $A$가 singular가 되는 $x$를 모두 구하시오."
       + BR + r"(c) $x=3$일 때 $|\operatorname{adj}A|$를 구하시오.",
       r"(a) 1행에 2행과 3행을 더하면(type III, 값 그대로) 1행이 $(x+2)(1,1,1)$이 됩니다. 1행에서 $x+2$를 밖으로 꺼내고(type II의 역), 2행·3행에서 1행을 빼면(type III) $(x+2)\begin{vmatrix}1&1&1\\0&x-1&0\\0&0&x-1\end{vmatrix}=(x+2)(x-1)^2$입니다."
       + BR + r"(b) singular ⇔ $|A|=0$이므로 $x=-2$ 또는 $x=1$입니다."
       + BR + r"(c) $A(\operatorname{adj}A)=|A|I$의 행렬식을 취하면 $|A||\operatorname{adj}A|=|A|^3$이고 $|A|=5\cdot4=20\neq0$이므로 $|\operatorname{adj}A|=|A|^2=400$입니다."
       + BR + "<b>채점 요소:</b> (a) 행 합으로 공통인수를 만드는 연산과 type별 행렬식 변화 (b) singular ⇔ $|A|=0$ (c) $|\\operatorname{adj}A|=|A|^{n-1}$을 끌어낸 과정",
       ["세 행을 모두 더하면 어떤 행이 나오는지 보세요.", "(c)는 $A(\\operatorname{adj}A)=|A|I$의 양변에 행렬식을 취합니다. $||A|I|$는 3×3에서 $|A|^3$입니다."]),
    OH("2-row-8", "2.row",
       r"3×3 행렬 $A$의 행이 차례로 $\mathbf r_1,\mathbf r_2,\mathbf r_3$이고 $|A|=3$이다. 다음 행렬의 행렬식을 구하고, 쓴 성질을 밝히시오. (행은 위에서부터 차례로 쓴다)"
       + BR + r"(a) 행이 $\mathbf r_2,\ \mathbf r_1,\ \mathbf r_3+4\mathbf r_1$인 행렬"
       + BR + r"(b) 행이 $\mathbf r_3,\ 2\mathbf r_2,\ \mathbf r_1-\mathbf r_3$인 행렬"
       + BR + r"(c) 행이 $\mathbf r_1+\mathbf r_2,\ \mathbf r_2+\mathbf r_3,\ \mathbf r_3+\mathbf r_1$인 행렬",
       r"(a) 3행에서 2행의 4배를 빼면(type III) 행이 $\mathbf r_2,\mathbf r_1,\mathbf r_3$이고, 행 교환 한 번($|E_1|=-1$)이면 $A$이므로 $-3$입니다."
       + BR + r"(b) 3행에 1행을 더하면(type III) $\mathbf r_3,2\mathbf r_2,\mathbf r_1$, 2행의 2를 꺼내고($|E_2|=2$) 1행과 3행을 바꾸면($-1$) $A$이므로 $2\cdot(-1)\cdot3=-6$입니다."
       + BR + r"(c) 3행 −= 1행: $\mathbf r_3-\mathbf r_2$, 3행 += 2행: $2\mathbf r_3$(type III 두 번). 3행의 2를 꺼내면 $\mathbf r_3$이 되고, 2행 −= 3행, 1행 −= 2행(type III)으로 $\mathbf r_1,\mathbf r_2,\mathbf r_3$이 됩니다. 따라서 $2\cdot3=6$입니다."
       + BR + "<b>채점 요소:</b> 소문항마다 행연산의 순서와 각 type의 행렬식 변화($-1$, $\\alpha$, $1$), 결과",
       ["행렬을 $A$로 되돌리는 행연산을 찾고, 그 연산들이 행렬식에 곱하는 수를 모으세요.", "(c)는 한 행에서 다른 행을 빼서 $\\mathbf r$ 하나만 남는 행을 먼저 만드세요."]),
    OH("2-mul-6", "2.mult",
       "다음을 보이시오." + BR
       + "(a) $n\\times n$ 행렬 $A$, $B$가 $AB=I$를 만족하면 $BA=I$이다." + BR
       + "(b) 3×3 행렬 $A$가 $A^T=-A$를 만족하면 $|A|=0$이다." + BR
       + "(c) $n\\times n$ 행렬 $A$가 $A^TA=I$를 만족하면 $|A|=1$ 또는 $-1$이다.",
       "(a) $|A||B|=|AB|=|I|=1$이므로 $|A|\\neq0$이고 $A^{-1}$이 있습니다. $AB=I$의 왼쪽에 $A^{-1}$을 곱하면 $B=A^{-1}$이므로 $BA=A^{-1}A=I$입니다." + BR
       + "(b) $|A|=|A^T|=|-A|=(-1)^3|A|=-|A|$이므로 $2|A|=0$, $|A|=0$입니다($|\\alpha A|=\\alpha^n|A|$)." + BR
       + "(c) $|A^T||A|=|I|=1$이고 $|A^T|=|A|$이므로 $|A|^2=1$, $|A|=\\pm1$입니다." + BR
       + "<b>채점 요소:</b> (a) $|AB|=|A||B|$로 nonsingular를 보인 뒤 역행렬을 곱함 (b) $|A^T|=|A|$와 $(-1)^n$, $n$이 홀수라는 점 (c) $|A^T|=|A|$, $|AB|=|A||B|$",
       ["세 문제 모두 양변에 행렬식을 취하는 데서 시작합니다.", "(b)에서 $n=3$이 홀수라는 점이 어디에 쓰이는지 보세요."]),
    OH("2-adj-6", "2.adj",
       "$|A|=2$인 3×3 행렬 $A$에 대해 답하시오." + BR
       + "(a) $\\operatorname{adj}A$를 $A^{-1}$로 나타내고 $|\\operatorname{adj}A|$를 구하시오." + BR
       + "(b) $|A^T\\operatorname{adj}A|$를 구하시오." + BR
       + "(c) $|3A^{-1}-\\operatorname{adj}A|$를 구하시오.",
       "(a) $A(\\operatorname{adj}A)=|A|I$의 왼쪽에 $A^{-1}$을 곱하면 $\\operatorname{adj}A=|A|A^{-1}=2A^{-1}$입니다. $|\\operatorname{adj}A|=2^3|A^{-1}|=8\\cdot\\tfrac12=4$입니다." + BR
       + "(b) $|A^T||\\operatorname{adj}A|=2\\cdot4=8$입니다." + BR
       + "(c) $3A^{-1}-2A^{-1}=A^{-1}$이므로 $|A^{-1}|=\\tfrac12$입니다. 행렬식끼리 빼서 $|3A^{-1}|-|\\operatorname{adj}A|$로 계산하면 틀립니다(행렬식은 덧셈·뺄셈과 바꿀 수 없음)." + BR
       + "<b>채점 요소:</b> (a) $\\operatorname{adj}A=|A|A^{-1}$와 $|\\alpha A|=\\alpha^n|A|$ (b) $|A^T|=|A|$ (c) 행렬끼리 먼저 정리",
       ["$A(\\operatorname{adj}A)=|A|I$에서 출발하세요.", "(c)는 $\\operatorname{adj}A$를 $A^{-1}$로 바꾸면 행렬 하나로 합쳐집니다."]),
    OH("2-adj-7", "2.adj",
       r"$A=\begin{bmatrix}1&2&1\\0&1&2\\1&0&3\end{bmatrix}$, $b=\begin{bmatrix}1\\1\\5\end{bmatrix}$이다."
       + BR + "(a) $|A|$를 구하시오."
       + BR + r"(b) $A^{-1}$ 전체를 구하지 말고 $A^{-1}$의 $(2,3)$ 성분만 $\operatorname{adj}A$로 구하시오."
       + BR + "(c) $Ax=b$의 $x_3$만 크라메르 공식으로 구하시오.",
       r"(a) 1열로 전개하면 $1\cdot\begin{vmatrix}1&2\\0&3\end{vmatrix}+1\cdot\begin{vmatrix}2&1\\1&2\end{vmatrix}=3+3=6$입니다."
       + BR + r"(b) $\operatorname{adj}A$의 $(2,3)$ 성분은 전치 때문에 $A_{32}=(-1)^{3+2}\begin{vmatrix}1&1\\0&2\end{vmatrix}=-2$이므로 $(A^{-1})_{23}=-2/6=-\frac13$입니다. $A_{23}$을 쓰면 틀립니다."
       + BR + r"(c) $|A_3|=\begin{vmatrix}1&2&1\\0&1&1\\1&0&5\end{vmatrix}=6$이므로 $x_3=6/6=1$입니다. (해 전체는 $x=(2,-1,1)$)"
       + BR + "<b>채점 요소:</b> (a) $|A|=6$ (어느 행·열로 전개하거나 행연산을 써도 됨) (b) $(A^{-1})_{ij}=A_{ji}/|A|$ (c) 3열을 $b$로 바꾼 $A_3$와 결과",
       ["$\\operatorname{adj}A$는 cofactor 행렬의 전치입니다. $(2,3)$ 성분은 어느 cofactor일까요?", "$x_3$에는 $|A|$와 $|A_3|$ 두 개만 필요합니다."], "photo"),
    OH("2-cr-6", "2.cramer",
       "성분이 모두 정수인 $n\\times n$ 행렬 $A$에 대해 다음을 보이시오." + BR
       + "(a) $|A|=\\pm1$이고 $b$의 성분이 모두 정수이면, $Ax=b$의 해 $x$의 성분도 모두 정수이다." + BR
       + "(b) $|A|=\\pm1$이면 $A^{-1}$의 성분도 모두 정수이다." + BR
       + "(c) 반대로 $A$와 $A^{-1}$의 성분이 모두 정수이면 $|A|=\\pm1$이다.",
       "(a) $|A|\\neq0$이라 크라메르 공식 $x_i=|A_i|/|A|$를 쓸 수 있습니다. $A_i$의 성분은 정수이고, 정수 행렬의 행렬식은 cofactor 전개(곱과 합)로 구하므로 정수입니다. 정수를 $\\pm1$로 나누면 정수입니다." + BR
       + "(b) $A^{-1}=\\frac{1}{|A|}\\operatorname{adj}A$이고 cofactor $A_{ij}=(-1)^{i+j}|M_{ij}|$는 정수 행렬의 행렬식이라 정수입니다. $\\pm1$로 나누어도 정수입니다." + BR
       + "(c) $|A||A^{-1}|=|AA^{-1}|=|I|=1$이고 두 값이 모두 정수이므로 $|A|=\\pm1$입니다." + BR
       + "<b>채점 요소:</b> (a) 크라메르 공식(또는 $x=A^{-1}b$와 adj)과 '정수 행렬의 행렬식은 정수'인 근거 (b) $A^{-1}=\\operatorname{adj}A/|A|$ (c) $|A||A^{-1}|=1$과 정수끼리의 곱",
       ["행렬식을 전개식으로 구하면 성분의 곱과 합만 나온다는 점을 쓰세요.", "(c)는 $AA^{-1}=I$의 행렬식에서 시작합니다."],
       alts=["(a)를 이렇게 써도 됩니다: $x=A^{-1}b=\\frac{1}{|A|}(\\operatorname{adj}A)b$이고 cofactor는 정수 행렬의 행렬식이라 정수이므로, $\\pm1$로 나눈 $\\operatorname{adj}A$와 정수 벡터 $b$의 곱인 $x$도 정수입니다."]),
    OH("2-vol-4", "2.vol",
       "부피(넓이)로서의 행렬식으로 답하시오." + BR
       + "(a) 세 점 $(1,1)$, $(4,2)$, $(2,5)$를 꼭짓점으로 하는 삼각형의 넓이를 구하시오." + BR
       + r"(b) 평면의 모든 점 $\mathbf p$를 $T\mathbf p$로 옮긴다. $T=\begin{bmatrix}3&1\\1&1\end{bmatrix}$일 때 (a)의 세 점을 옮긴 세 점이 만드는 삼각형의 넓이를 구하시오."
       + BR + r"(c) $|\mathbf a_1\ \mathbf a_2\ \mathbf a_3|=5$일 때 $\mathbf a_1$, $\mathbf a_2+2\mathbf a_1$, $\mathbf a_3-\mathbf a_1+3\mathbf a_2$가 만드는 평행육면체의 부피를 구하시오.",
       r"(a) $(1,1)$에서 나머지 두 점으로 가는 벡터는 $(3,1)$, $(1,4)$입니다. 평행사변형 넓이 $\begin{vmatrix}3&1\\1&4\end{vmatrix}=11$의 절반이라 $\frac{11}{2}$입니다."
       + BR + r"(b) 옮긴 점들 사이의 벡터는 $T\mathbf p_2-T\mathbf p_1=T(\mathbf p_2-\mathbf p_1)$이므로 새 평행사변형은 $T[\mathbf u\ \mathbf v]$의 열이 만듭니다. $|T[\mathbf u\ \mathbf v]|=|T|\cdot|\mathbf u\ \mathbf v|=2\cdot11=22$이므로 삼각형 넓이는 $11$입니다."
       + BR + r"(c) 각 열에 다른 열의 상수배를 더한 것(type III 열 연산)이라 행렬식이 그대로 5이고, 부피는 5입니다. 둘째 열이 먼저 바뀌었어도 셋째 열은 $\mathbf a_3-7\mathbf a_1+3(\mathbf a_2+2\mathbf a_1)$이라 여전히 다른 열의 일차결합을 더한 것입니다."
       + BR + "<b>채점 요소:</b> (a) 꼭짓점 차이 벡터와 ½ (b) $|AB|=|A||B|$로 넓이가 $|T|$배 (c) shear(type III)는 부피 불변",
       ["(a)는 한 꼭짓점에서 나머지 두 꼭짓점으로 가는 벡터 두 개를 쓰세요.", "(b)는 $|T[\\mathbf u\\ \\mathbf v]|=|T||[\\mathbf u\\ \\mathbf v]|$를 쓰면 점을 직접 옮길 필요가 없습니다."],
       alts=[r"(b)는 세 점을 $T$로 직접 옮겨 $(4,2)$, $(14,6)$, $(11,7)$을 구하고, 차이 벡터 $(10,4)$, $(7,5)$의 행렬식 $22$의 절반으로 $11$을 얻어도 됩니다."]),
]
Q += EXAM


def check_exam():
    """시험형 서술형 모범 답안의 수치를 확인한다."""
    a, b, t, x = symbols("a b t x")
    # 1-ref-6
    A = Matrix([[1, 1, 1], [1, 2, 3], [1, 3, a]])
    assert A.det() == a - 5
    U = Matrix([[1, 1, 1, 1], [1, 2, 3, 2], [1, 3, a, b]])
    U[1, :] -= U[0, :]; U[2, :] -= U[0, :]; U[2, :] -= 2 * U[1, :]
    assert U[2, :] == Matrix([[0, 0, a - 5, b - 3]])
    A5 = A.subs(a, 5)
    assert A5 * Matrix([t, 1 - 2 * t, t]) == Matrix([1, 2, 3])
    # 1-alg-6
    P = Matrix([[1, 1], [0, 0]]); I2 = eye(2)
    assert P * P == P and (I2 + P) * (I2 - P / 2) == I2 and (I2 - P / 2) * (I2 + P) == I2
    # 1-inv-5
    N = Matrix([[0, 1, 2], [0, 0, 3], [0, 0, 0]])
    assert N ** 3 == Matrix.zeros(3) and N ** 2 == Matrix([[0, 0, 3], [0, 0, 0], [0, 0, 0]])
    assert eye(3) - N == Matrix([[1, -1, -2], [0, 1, -3], [0, 0, 1]])
    assert (eye(3) - N).inv() == eye(3) + N + N ** 2 == Matrix([[1, 1, 5], [0, 1, 3], [0, 0, 1]])
    # 1-el-7
    A = Matrix([[2, 4, 0], [0, 1, 0], [0, 3, 1]])
    G1 = Matrix.diag(Rational(1, 2), 1, 1)
    G2 = Matrix([[1, -2, 0], [0, 1, 0], [0, 0, 1]])
    G3 = Matrix([[1, 0, 0], [0, 1, 0], [0, -3, 1]])
    assert G3 * G2 * G1 * A == eye(3)
    assert G3 * G2 * G1 == Matrix([[Rational(1, 2), -2, 0], [0, 1, 0], [0, -3, 1]])
    assert G1.inv() * G2.inv() * G3.inv() == A and A.det() == 2
    # 1-pt-3
    Ab, Cb = Matrix([[1, 1], [0, 1]]), Matrix([[2, 1], [1, 1]])
    Mb = Matrix.vstack(Matrix.hstack(Ab, eye(2)), Matrix.hstack(Matrix.zeros(2), Cb))
    assert Cb.inv() == Matrix([[1, -1], [-1, 2]]) and Ab.inv() == Matrix([[1, -1], [0, 1]])
    assert Mb.inv()[0:2, 2:4] == -Ab.inv() * Cb.inv() == Matrix([[-2, 3], [1, -2]])
    # 2-cof-5
    A = Matrix([[2, 1, 3], [1, 0, 2], [5, 6, 7]])
    c3 = [A.cofactor(2, j) for j in range(3)]
    assert 2 * c3[0] + c3[1] + 3 * c3[2] == 0
    assert c3[1] + c3[2] == Matrix([[2, 1, 3], [1, 0, 2], [0, 1, 1]]).det() == -2
    assert 5 * c3[0] + 6 * c3[1] + 7 * c3[2] == A.det() == -3
    # 2-row-7
    X = Matrix([[x, 1, 1], [1, x, 1], [1, 1, x]])
    assert (X.det() - (x + 2) * (x - 1) ** 2).expand() == 0
    X3 = X.subs(x, 3)
    assert X3.det() == 20 and X3.adjugate().det() == 400
    # 2-row-8: 일반 3×3에서 행렬식 비율 확인
    G = Matrix(3, 3, symbols("g0:9"))
    r1, r2, r3 = G[0, :], G[1, :], G[2, :]
    d = G.det()
    for rows, k in (((r2, r1, r3 + 4 * r1), -1), ((r3, 2 * r2, r1 - r3), -2), ((r1 + r2, r2 + r3, r3 + r1), 2)):
        assert (Matrix.vstack(*rows).det() - k * d).expand() == 0
    # 2-adj-6
    for A in (Matrix.diag(2, 1, 1), Matrix([[1, 1, 0], [0, 2, 1], [0, 0, 1]])):
        assert A.det() == 2 and A.adjugate() == 2 * A.inv() and A.adjugate().det() == 4
        assert (A.T * A.adjugate()).det() == 8 and (3 * A.inv() - A.adjugate()).det() == Rational(1, 2)
    # 2-adj-7
    A, bv = Matrix([[1, 2, 1], [0, 1, 2], [1, 0, 3]]), Matrix([1, 1, 5])
    assert A.det() == 6 and A.inv()[1, 2] == Rational(-1, 3) and A.cofactor(2, 1) == -2
    A3 = A.copy(); A3[:, 2] = bv
    assert A3.det() == 6 and A.solve(bv) == Matrix([2, -1, 1])
    # 2-vol-4
    u, v = Matrix([4, 2]) - Matrix([1, 1]), Matrix([2, 5]) - Matrix([1, 1])
    assert Matrix.hstack(u, v).det() == 11
    T = Matrix([[3, 1], [1, 1]])
    assert T.det() == 2 and Matrix.hstack(T * u, T * v).det() == 22
    p1, p2, p3 = (T * Matrix(p) for p in ([1, 1], [4, 2], [2, 5]))  # alts: 점을 직접 옮기기
    assert [list(p) for p in (p1, p2, p3)] == [[4, 2], [14, 6], [11, 7]] and Matrix.hstack(p2 - p1, p3 - p1).det() == 22
    H = Matrix(3, 3, symbols("h0:9"))
    a1, a2, a3 = H[:, 0], H[:, 1], H[:, 2]
    assert (Matrix.hstack(a1, a2 + 2 * a1, a3 - a1 + 3 * a2).det() - H.det()).expand() == 0
    print(f"시험형 서술형 검증 통과 ({len(EXAM)}문항)")


def check():
    """계산이 들어간 정답을 sympy로 확인한다. 단답형은 정답 문자열을 직접 파싱해 비교한다."""
    k = symbols("k")
    got = {}
    assert solve(2 * 3 - k, k) == [6]
    got["1-sys-1"] = 6
    got["1-ge-5"] = Matrix([[1, 1, 1], [2, 3, 1], [1, 2, 3]]).solve(Matrix([6, 11, 14])).T
    got["1-ref-5"] = solve(Matrix([[1, 1, 1, 1], [1, 2, 3, 2], [2, 3, 4, k]]).echelon_form()[2, 3], k)[0]
    got["1-alg-2"] = (Matrix([[1, 2], [3, 4]]) * Matrix([[2, 0], [1, 5]]))[1, 0]
    got["1-alg-5"] = Matrix([[1, 1], [0, 1]]) ** 3
    P, Qm = Matrix([[1, 1], [0, 0]]), Matrix([[1, 0], [1, 0]])
    assert P * Qm == Matrix([[2, 0], [0, 0]]) and Qm * P == Matrix([[1, 1], [1, 1]])  # 1-alg-4
    got["1-el-2"] = Matrix([[1, 0, 0], [4, 1, 0], [0, 0, 1]]).inv()
    E1, E2 = Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]]), Matrix([[5, 0, 0], [0, 1, 0], [0, 0, 1]])
    got["1-el-3"] = (E1 * E2).inv()
    assert E2.inv() * E1 != E1 * E2.inv()
    got["1-el-6"] = Matrix([[1, 1, 0], [0, 1, 1], [0, 0, 1]]).inv()
    got["1-pt-1"] = Matrix([[1, 2], [3, 4]]) * Matrix([[2], [1]])
    got["1-pt-2"] = Matrix([[2, 0, 0], [0, 1, 2], [0, 1, 3]]).inv()
    got["2-cof-1"] = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]]).cofactor(0, 1)
    got["2-cof-2"] = Matrix([[1, 0, 0, 2], [3, 0, 4, 1], [0, 0, 0, 5], [2, 1, 3, 0]]).det()
    got["2-cof-4"] = Matrix([[2, 1, 3], [1, 0, 2], [4, 1, 1]]).det()
    assert [Matrix(m).det() for m in ([[1, 2, 3], [2, 4, 6], [0, 1, 5]], [[1, 2], [3, 4]], [[2, 1, 7], [0, 3, 1], [0, 0, 5]], [[0, 1], [1, 0]])] == [0, -2, 30, -1]  # 2-pr-1
    A3 = Matrix([[1, 2, 0], [0, 3, 1], [2, 1, 1]]); s = A3.det()
    B = A3.copy(); B.row_swap(0, 2); B[1, :] = 3 * B[1, :]
    got["2-row-1"] = B.det() / s * 5
    got["2-row-2"] = 3 ** 4 * 2
    R = A3.copy(); R[1, :] = R[1, :] + 4 * R[0, :]
    got["2-row-3"] = R.det() / s * 7
    got["2-row-4"] = sum(A3[0, j] * A3.cofactor(1, j) for j in range(3))
    got["2-row-6"] = Matrix([[1, 2, 3], [2, 5, 7], [3, 7, 11]]).det()
    got["2-mul-1"] = Rational(1, 2) * (-3)
    got["2-mul-3"] = 1
    got["2-adj-1"] = Matrix([[3, 5], [1, 2]]).inv()
    got["2-adj-2"] = Matrix.diag(2, 1, 1).adjugate().det()
    G = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    assert G.det() == 1
    got["2-adj-3"] = G.adjugate()[0, 1]
    got["2-adj-5"] = G.inv()
    Ac, b = Matrix([[2, 1], [1, 3]]), Matrix([5, 5])
    A2 = Ac.copy(); A2[:, 1] = b
    got["2-cr-1"] = A2.det() / Ac.det()
    C3 = Matrix([[1, 1, 1], [1, 2, 1], [1, 1, 2]]); b3 = Matrix([6, 8, 9])
    C33 = C3.copy(); C33[:, 2] = b3
    assert C3.det() == 1 and C33.det() == 3 and C3.solve(b3) == Matrix([1, 2, 3])
    got["2-cr-4"] = C33.det() / C3.det()
    got["2-vol-2"] = Matrix([[2, 11], [0, 3]]).det()
    assert Matrix([[2, 1], [0, 3]]).det() == 6
    got["2-vol-3"] = abs((2 * Matrix.diag(-4, 1, 1)).det())

    def parse(t):
        t = t.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
        rows = [r.replace(",", " ").split() for r in t.split(";")]
        return Matrix([[Rational(x) for x in r] for r in rows])

    byid = {q["id"]: q for q in Q}
    for qid, v in got.items():
        q = byid[qid]
        key = q["ans"] if isinstance(q["ans"], str) else q["ans"][0]
        exp = parse(key)
        val = v if isinstance(v, Matrix) else Matrix([[v]])
        if exp.shape != val.shape and 1 in exp.shape and 1 in val.shape:
            exp, val = exp.reshape(1, len(exp)), val.reshape(1, len(val))
        assert exp == val, f"{qid}: 정답 {key} ≠ 계산 {val.tolist()}"
    unchecked = [q["id"] for q in Q if q["t"] == "short" and q["id"] not in got and parse_ok(q)]
    assert not unchecked, f"검증하지 않은 단답형: {unchecked}"
    print(f"sympy 검증 통과 (단답형 {len(got)}개)")


def parse_ok(q):
    import re
    k = q["ans"] if isinstance(q["ans"], str) else q["ans"][0]
    return bool(re.fullmatch(r"[\[\(]?[-\d/ ,;]+[\]\)]?", k))


PROFILE = {
    "genTypes": ["open", "short", "mc"],
    "genPrefer": "시험이 서술형뿐이므로 서술형을 기본으로 낸다. 오답 원인이 계산 한 단계뿐이면 단답형, 두 성질을 구분하는지만 볼 때는 객관식",
    "genRules": [
        "시험 형식: 1시간에 서술형 7문제(문제당 8분 안팎). 서술형 후속 문제는 소문항 (a)(b)(c) 2~3개로 만들고, 앞 소문항에서 법칙을 보이거나 끌어낸 뒤 뒤 소문항에서 그 법칙으로 계산이 짧게 끝나게 한다.",
        "ch1과 ch2를 잇는 문제를 우선한다: 해의 판정과 행렬식, 기본행렬과 행렬식, adj와 크라메르 공식, 행렬 등식에서 역행렬 찾기와 singular 판정.",
        "서술형 모범 답안 끝에는 '<b>채점 요소:</b>'로 소문항마다 꼭 써야 할 성질, 핵심 식, 결과를 적는다.",
        "교수님 출제 스타일: 법칙이나 개념을 알면 계산이 금방 끝나는 문제를 낸다. 성질을 모르면 오래 걸리고, 알면 한두 줄로 끝나야 좋은 문제다.",
        "아직 배우지 않은 개념(벡터공간, 부분공간, 일차독립, 랭크, 기저, 고유값, 직교성 등)은 문제와 보기에 쓰지 않는다.",
        "행렬은 3×3 이하, 성분은 한 자리 정수로 한다. 4×4는 0이 많아 한두 번 전개로 끝나는 경우만 쓴다.",
        "단답형 정답은 수 하나, 벡터, 행렬 중 하나로 정해지게 한다. 힌트는 첫째는 방향, 둘째는 핵심 단계로 쓰고 정답을 직접 말하지 않는다.",
        "용어는 노트처럼 영어 용어(singular, lead variable, cofactor, row echelon form 등)를 그대로 써도 된다.",
        "크라메르 공식의 연도 같은 역사적 사실은 묻지 않는다.",
    ],
    "gradeRules": [
        "시험 서술형처럼 채점한다. 소문항이 있으면 소문항마다 근거(쓴 성질이나 식)와 결과를 따로 보고, score는 소문항을 고르게 나눈 100점 만점으로 매긴다. feedback에서 어느 소문항에서 왜 점수를 잃었는지 말한다.",
        "모범 답안의 '채점 요소'를 기준으로 하되, 다른 행연산 순서, 다른 전개 행·열 등 다른 방법이라도 맞으면 인정한다.",
        "증명·설명형은 어떤 성질을 어떤 순서로 썼는지를 본다. 결론만 맞고 근거가 빠졌으면 partial로 한다.",
        "풀이는 노트의 행연산 표기(예: R2-3R1, 2행 −= 3×1행)나 [1 2; 3 4] 같은 간단 표기로 써도 인정한다.",
        "표기가 노트와 조금 달라도 뜻이 같으면 인정한다.",
    ],
    "tools": ["matrix"],
    "cycle": 8,
    "sessionGoal": 7,
    "photoLimit": {"n": 2, "of": 5},
}


def shuffle(qs):
    """정답 위치가 한쪽으로 몰리지 않게 문제 id로 정한 순서로 보기를 섞는다(실행할 때마다 같은 결과)."""
    import random
    for q in qs:
        if q["t"] != "mc":
            continue
        rng = random.Random(q["id"])
        idx = list(range(len(q["o"])))
        rng.shuffle(idx)
        q["o"], q["a"] = [q["o"][i] for i in idx], idx.index(q["a"])
    return qs


DATA = {
    "title": "선형대수 약점 클리닉",
    "subject": "선형대수",
    "role": "너는 대학교 2학년 \"선형대수\" 과목(교재: S. Leon, Linear Algebra with Applications, 1~2장 범위)의 튜터다. 답은 한국어 존댓말로 쓴다. 아래 강의 노트 범위를 벗어난 내용을 요구하거나 가르치지 않는다. 표기는 강의 노트를 따른다: |A| 행렬식, M_ij 소행렬식(minor), A_ij=(−1)^(i+j)|M_ij| 여인수(cofactor), adj A 수반행렬, A^T 전치행렬, 기본행렬 E_1/E_2/E_3 = type I(두 행 교환)/II(한 행에 상수배)/III(한 행의 상수배를 다른 행에 더함).",
    "lede": "시험은 <b>1시간에 서술형 7문제</b>(문제당 8분 안팎)입니다. 소문항이 있는 서술형은 시험지에 쓰듯 근거(쓴 성질)와 결과를 모두 쓰고, 8분 안에 끝내는 연습을 하세요. 단답형도 풀이를 함께 내면 Claude가 어느 단계에서 틀렸는지 봐 줍니다.",
    "unitFormat": "Ch.{u}",
    "units": UNITS,
    "concepts": CONCEPTS,
    "profile": PROFILE,
    "questions": shuffle(Q),
}

if __name__ == "__main__":
    check()
    check_exam()
    out = os.path.join(HERE, "subject.json")
    json.dump(DATA, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("작성:", out, "문제", len(Q))
