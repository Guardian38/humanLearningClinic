# study-clinic (약점 클리닉 스킬)

[Claude Code](https://claude.com/claude-code) 스킬이다. 강의 자료(요약 노트, 슬라이드, 연습문제)로 과목별 공부 자료를 만든다. 무엇을 만들지는 과목마다 고른다.

| 산출물 | 내용 |
|---|---|
| 요약본 | 강의를 쪽수 근거와 함께 옮긴 `요약.md`(다른 산출물의 원본)와 훑어보기용 페이지 |
| 이해 가이드 | 개념마다 "왜 → 직관 → 식 → 직접 해보기 → 자주 하는 오해" 순서로 설명하는 단원별 페이지. 캔버스 실습과 자가 점검이 들어간다. 교수님이 예시 문제나 시험 정보를 주지 않은 과목에 특히 알맞다 |
| 약점 클리닉 | 아래의 적응형 문제 풀이 페이지 |

가이드와 클리닉은 같은 개념 id를 쓰므로, 클리닉에서 답을 확인하면 그 개념의 가이드 절로 가는 링크가 나온다.

약점 클리닉:

- 개념별 숙련도와 간격 복습으로 다음 문제를 고른다.
- 객관식, 단답형(수·벡터·행렬을 유리수로 정확히 비교), 서술형을 낸다. 종이 풀이 사진도 올릴 수 있다.
- 페이지 안의 Claude가 서술형 채점, 풀이에서 처음 틀린 단계 진단, 오답을 겨냥한 후속 문제, 정답·해설 이의 검토를 한다.
- 모르는 문제는 "모르겠음"을 누르면 틀림으로 기록하고, 정답과 함께 Claude가 개념부터 단계별로 설명한다.
- 코딩 과목은 코드 색칠(VS Code 색), 코드 편집기, 브라우저 안 실행(JavaScript, Python/Pyodide)과 출력 비교를 지원한다.
- 풀이 기록은 아티팩트 db에 쌓여 다시 게시해도 남는다.

## 설치

```
git clone https://github.com/Guardian38/humanLearningClinic.git ~/.claude/skills/study-clinic
```

Windows는 `C:\Users\<이름>\.claude\skills\study-clinic`에 받는다. Claude Code를 다시 열면 스킬 목록에 `study-clinic`이 나온다. 업데이트는 그 폴더에서 `git pull`.

## 필요한 것

- Claude Code와 claude.ai 아티팩트 게시(Artifact 도구). 클리닉 페이지는 아티팩트의 `db`(기록 저장)와 `sample`(페이지 안 Claude 호출) 기능을 쓰므로, 계정에서 이 기능을 쓸 수 있어야 한다.
- Python 3와 `sympy`(정답 검증): `python -m pip install sympy`
- (코딩 과목) 모범 코드 실행 검증에 Python, JavaScript 과목이면 Node.js
- (선택) 페이지 스크립트 문법 검사: `pip install --target <폴더> esprima` 후 빌드에 `--pylib <폴더>`

## 쓰는 법

과목 폴더에서 Claude Code를 열고 "이 과목 공부 자료 만들어 줘", "이 과목으로 약점 클리닉 만들어 줘", "이해 가이드 만들어 줘"처럼 말한다. 무엇을 만들지 정하지 않았으면 스킬이 자료를 보고 산출물을 추천해 묻는다. 스킬이 자료를 읽고 과목 프로필 초안을 만든 뒤, 자료로 정할 수 없는 출제·채점 기준(시험 형식, 부분 점수, 세션 길이 등)은 사용자에게 묻는다. 정한 기준은 과목 폴더의 `PROGRESS.md`에 남아 다른 기기·세션에서도 같게 동작한다.

클리닉에서 문제를 이의 제기하거나 고친 뒤 "수정 내역 반영해 줘"라고 하면 문제 은행 원본에 반영하고 다시 게시한다.

자세한 절차는 `SKILL.md`, 문제 작성 원칙은 `references/question-rules.md`를 본다.

## 파일

| 파일 | 내용 |
|---|---|
| `SKILL.md` | 스킬 본문(산출물 고르기 → 과목 평가·요약본·가이드 → 데이터 → 빌드 → 게시 → 유지보수) |
| `assets/clinic_template.html` | 클리닉 엔진. 과목 데이터만 끼워 넣는다 |
| `assets/guide_template.html` | 이해 가이드 틀(단원 전환, 목차, 자가 점검, 수식, 실습 도구 `G.Plot`) |
| `scripts/build_clinic.py` | `subject.json`을 검사하고 템플릿에 넣어 HTML을 만든다 |
| `scripts/build_summary.py` | `요약.md`를 훑어보기용 페이지로 만든다 |
| `scripts/build_guide.py` | 가이드 본문 조각을 검사하고 한 장짜리 HTML과 개념 절 지도(`guide_map.json`)를 만든다 |
| `references/question-rules.md` | 출제 원칙(공통 규칙, 과목마다 정할 것, 피할 것) |
| `references/guide-rules.md` | 이해 가이드 작성 원칙(원본, 절 구성, 상자, 자가 점검, 실습) |
| `examples/linear_algebra_make_subject.py` | 예시: 선형대수 ch1~2 문제 은행(68문항, sympy 검증 포함). 구조만 참고하고, 안의 `PROFILE`은 그 과목에서 정한 값이라 그대로 쓰지 않는다 |
| `examples/guide/` | 예시: 선형대수 이해 가이드 2단원(실습 1개). 형식 참고용으로 내용은 일부만 있다 |
| `CHANGELOG.md` | 변경 내역(받은 피드백, 판단, 바뀐 것) |

## 피드백

버그나 제안은 [Issues](https://github.com/Guardian38/humanLearningClinic/issues)에 남겨 주세요.

## 기여자

- [@blokey47](https://github.com/blokey47): "모르겠음" 버튼과 자세한 설명, Claude 호출 상태 안내, 출제 원칙의 일반화를 제안하고 처음 구현했다.

## 라이선스

MIT. `LICENSE`를 본다.
