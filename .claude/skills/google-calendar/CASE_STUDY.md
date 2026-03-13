# Google Calendar Skill 생성 케이스 스터디

> **프로젝트**: Claude Code Skills 시스템을 활용한 Google Calendar 통합
> **날짜**: 2025년 10월 22일
> **소요 시간**: 약 2시간
> **난이도**: 중급 (OAuth 인증, 파싱 로직, 하이브리드 아키텍처)

---

**이 문서는 PKM에도 저장할 수 있습니다:**
- **위치**: `30-knowledge/36-ai-tools/36.01-claude-code/skills-case-studies/google-calendar-skill.md`
- **폴더**: `skills-case-studies/` (Claude Code Skills 케이스 스터디 모음)

---

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [기술 의사결정](#기술-의사결정)
3. [구현 과정](#구현-과정)
4. [문제 해결](#문제-해결)
5. [최종 결과](#최종-결과)
6. [교훈](#교훈)

---

## 프로젝트 개요

### 목표

Claude Code의 Skills 시스템을 사용하여 Google Calendar와 통합하고, Daily Note와 Weekly Review에 자동으로 일정을 삽입하는 기능을 구현한다.

### 요구사항

**핵심 기능:**
- ✅ 오늘 일정 조회 (Markdown 형식)
- ✅ 이번 주 일정 조회 (날짜별 그룹화)
- ✅ 키워드로 일정 검색
- ✅ 자연어로 일정 등록

**제약사항:**
- 특정 캘린더만 조회 (업무용, 개인용, 재무용)
- 공유 캘린더 제외
- 종일 일정 지원 필수
- Daily Note 템플릿 자동 통합

### 초기 상황

**기존 리소스:**
- ✅ PKM 시스템 (Johnny Decimal 구조)
- ✅ Daily Note 템플릿 (`{{calendar_events}}` placeholder)
- ✅ `/daily-note` slash command
- ✅ Google OAuth credentials (credentials.json)

**미완성 부분:**
- ❌ Google Calendar API 인증
- ❌ 실행 가능한 스크립트
- ❌ Skills 통합

---

## 기술 의사결정

### 1. gcalcli vs 직접 Python API

**선택지:**

| 항목 | gcalcli (채택) | Python API (기존) |
|-----|---------------|------------------|
| **기능** | 조회/검색/수정/삭제/뷰 | 조회/등록만 |
| **설치** | `pipx install gcalcli` | 복잡한 pip 설정 |
| **인증** | `gcalcli init` | credentials.json + 코드 |
| **날짜 범위** | 자유롭게 지정 가능 | 오늘만 가능 |
| **캘린더 뷰** | calw/calm (ASCII) | 없음 |
| **Markdown 출력** | 래퍼로 변환 | 기본 지원 |

**최종 결정: gcalcli + Python 래퍼 (하이브리드)**

**이유:**
1. **기능 풍부**: gcalcli는 성숙한 오픈소스로 검색/수정/삭제 등 고급 기능 제공
2. **유지보수**: 커뮤니티가 관리하므로 버그 수정 및 업데이트 보장
3. **확장성**: 필요한 기능만 Python 래퍼로 감싸서 Markdown 출력 최적화
4. **안정성**: gcalcli가 Google API 변경사항을 자동 반영

### 2. 아키텍처 설계

```
┌─────────────────────────────────────┐
│   Claude Code (Skills 시스템)        │
│   "오늘 일정 뭐 있어?"                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   google-calendar Skill              │
│   (SKILL.md - 실행 가이드)           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Python 래퍼 스크립트                │
│   - get_events.py                   │
│   - get_week_events.py              │
│   - search_events.py                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   gcalcli (CLI 도구)                 │
│   Google Calendar API 호출           │
└─────────────────────────────────────┘
```

**계층별 역할:**

1. **Skills 계층**: Claude가 사용자 의도 파악 및 적절한 스크립트 선택
2. **래퍼 계층**: gcalcli 출력을 Markdown으로 변환, 캘린더 필터링
3. **gcalcli 계층**: Google Calendar API 통신, OAuth 인증 관리

---

## 구현 과정

### Phase 1: gcalcli 설치 및 인증 (30분)

#### 1.1 gcalcli 설치

**문제:** Mac 환경에서 `pip3 install`이 externally-managed-environment 오류 발생

**해결:**
```bash
# pipx 사용 (가상환경 자동 관리)
brew install pipx
pipx install gcalcli
pipx ensurepath
export PATH="$HOME/.local/bin:$PATH"
```

**검증:**
```bash
gcalcli --version
# 출력: gcalcli 4.5.1
```

#### 1.2 OAuth 인증 설정

**준비물:**
- Google Cloud Console에서 발급받은 `credentials.json`
- Client ID: `YOUR_CLIENT_ID.apps.googleusercontent.com`
- Client Secret: `YOUR_CLIENT_SECRET`

**인증 과정:**
```bash
gcalcli init
```

**발생한 문제:**
1. **잘못된 입력**: 사용자가 Client ID에 이메일 주소 입력
   - ❌ 입력: `user@gmail.com`
   - ✅ 정답: `YOUR_CLIENT_ID.apps.googleusercontent.com`

2. **Google OAuth 테스트 모드 제한**:
   - 오류: `403 error: access_denied`
   - 원인: OAuth 앱이 테스트 모드이고 테스터 미등록

**해결:**
- Google Cloud Console → OAuth 동의 화면 → 테스트 사용자에 `user@gmail.com` 추가

**성공 확인:**
```bash
gcalcli list
# 출력:
# Access  Title
# ------  -----
# owner   공유캘린더
# owner   재무
# owner   업무
# owner   개인
# reader  대한민국의 휴일
```

### Phase 2: Python 래퍼 스크립트 작성 (45분)

#### 2.1 get_events.py (오늘 일정)

**초기 구현:**
```python
def get_today_events():
    """오늘 일정 가져오기"""
    output = run_gcalcli(['agenda', '--nocolor', '--nodeclined'])
    markdown = parse_gcalcli_output_to_markdown(output)
    return markdown
```

**문제 1: 모든 캘린더 일정 표시**
- 공유 캘린더까지 포함되어 불필요한 일정 표시

**해결:**
```python
# 조회할 캘린더 지정
calendars = ['업무', '개인', '재무']

cmd = ['agenda', today, today, '--nocolor', '--nodeclined']
for cal in calendars:
    cmd.extend(['--calendar', cal])

output = run_gcalcli(cmd)
```

**문제 2: 종일 일정 미표시**
- gcalcli가 날짜 범위 조회 시 종일 일정을 제대로 반환하지 않음

**해결:**
```python
# 종일 일정 포함을 위해 다음날까지 조회 후 필터링
tomorrow = (today_date + timedelta(days=1)).strftime('%Y-%m-%d')
cmd = ['agenda', today, tomorrow, '--nocolor', '--nodeclined']

# 오늘 날짜만 필터링
filtered_output = filter_today_only(output, today)
```

**문제 3: ANSI 색상 코드**
- gcalcli 출력에 `\x1b[0;33m`, `[0m` 같은 ANSI 코드 포함
- Markdown 파싱 실패

**해결:**
```python
# ANSI 색상 코드 제거 (모든 형태)
output_clean = re.sub(r'\x1b\[[0-9;]*m|\[[0-9;]*m', '', output)
```

**문제 4: 날짜 헤더와 일정이 한 줄에**
- 예: `"Thu Oct 23         월 구독료 결제"`
- 날짜 부분을 제거하고 일정만 추출 필요

**해결:**
```python
if today_formatted in line:
    include_line = True
    # 날짜 행에 일정이 같이 있는 경우
    event_part = line.replace(today_formatted, '').strip()
    if event_part:
        today_lines.append('         ' + event_part)
    continue
```

**최종 parse 로직:**
```python
def parse_gcalcli_output_to_markdown(output):
    # ANSI 제거
    output_clean = re.sub(r'\x1b\[[0-9;]*m|\[[0-9;]*m', '', output)

    for line in lines:
        # 날짜 헤더 건너뛰기
        if re.match(r'^[A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d{1,2}', line.strip()):
            continue

        # 시간 있는 일정: "  9:00am  Team Meeting"
        time_match = re.search(r'(\d{1,2}:\d{2}[ap]m|All Day)', line, re.IGNORECASE)
        if time_match:
            # 시간 변환 및 Markdown 생성
        else:
            # 종일 일정
            event_text = line.strip()
            if event_text:
                markdown_lines.append(f"- **종일** {event_text}")
```

#### 2.2 get_week_events.py (주간 일정)

**핵심 차이점:**
- 날짜별 그룹화 필요
- 여러 날짜의 일정을 처리

**구현:**
```python
def parse_week_events_to_markdown(output):
    output_clean = re.sub(r'\x1b\[[0-9;]*m|\[[0-9;]*m', '', output)

    events_by_date = {}
    current_date = None

    for line in lines:
        # 날짜 헤더 체크
        date_match = re.match(r'^([A-Z][a-z]{2} [A-Z][a-z]{2} \d{1,2})', line.strip())
        if date_match:
            current_date = date_match.group(1)
            # ... 날짜별로 일정 그룹화
```

**시간 파싱 개선:**
```python
# 24시간 형식 지원 (HH:MM)
time_match = re.match(r'^\s*(\d{1,2}:\d{2})([ap]m)?', line, re.IGNORECASE)
if time_match:
    time_str = time_match.group(1)
    ampm = time_match.group(2)

    # 12시간 형식이면 24시간으로 변환
    if ampm:
        time_display = convert_to_24h(time_str + ampm)
    else:
        time_display = time_str  # 이미 24시간 형식
```

#### 2.3 search_events.py (검색)

**구현:**
```python
def search_events(keyword):
    calendars = ['업무', '개인', '재무']

    cmd = ['search', keyword, '--nocolor', '--nodeclined']
    for cal in calendars:
        cmd.extend(['--calendar', cal])

    output = run_gcalcli(cmd)
    markdown = parse_search_results_to_markdown(output)
    return markdown
```

### Phase 3: Skill 생성 (20분)

#### 3.1 SKILL.md 작성

**핵심 구성:**
```yaml
---
name: google-calendar
description: Google Calendar 일정 조회, 검색, 등록. "오늘 일정", "이번 주 일정", "일정 검색", "미팅 잡아줘" 등을 언급하면 자동 실행.
allowed-tools: Bash, Read
---

# Google Calendar Integration Skill

## 사용 시나리오

### 1. 오늘 일정 조회
Trigger: "오늘 일정 뭐 있어?"
실행: cd skills/google-calendar/scripts && python3 get_events.py

### 2. 이번 주 일정 조회
Trigger: "이번 주 스케줄 알려줘"
실행: python3 get_week_events.py
```

**중요 포인트:**
1. **description**: Claude가 언제 skill을 실행할지 판단하는 핵심
   - Trigger 키워드 명시 ("오늘 일정", "이번 주 일정")
   - 사용 사례 구체적으로 나열

2. **allowed-tools**: Bash, Read만 허용 (보안)

3. **스크립트 경로**: 절대 경로 사용

#### 3.2 문서 업데이트

**업데이트한 파일:**
1. `~/.claude/skills/README.md` - google-calendar skill 추가
2. `/calendar/README.md` - gcalcli 기반 사용법
3. `SETUP_GUIDE.md` - 설정 안내서
4. `CASE_STUDY.md` - 이 문서

---

## 문제 해결

### 문제 1: OAuth 인증 실패

**증상:**
```
액세스 차단됨: claude-code-gg은(는) Google 인증 절차를 완료하지 않았습니다
403 오류: access_denied
```

**원인:** OAuth 앱이 테스트 모드이고 사용자가 테스터 목록에 없음

**해결 단계:**
1. Google Cloud Console → APIs 및 서비스 → OAuth 동의 화면
2. "테스트 사용자" 섹션 → "+ 사용자 추가"
3. `user@gmail.com` 추가
4. 저장 후 `gcalcli init` 재실행

### 문제 2: 종일 일정 미표시

**증상:**
- gcalcli로 직접 조회하면 나오는데, 날짜 범위로 조회하면 종일 일정이 빠짐

**원인:** gcalcli의 날짜 범위 처리 버그

**해결:**
```python
# Before: 오늘만 조회 (종일 일정 누락)
output = run_gcalcli(['agenda', '2025-10-22', '2025-10-22'])

# After: 내일까지 조회 후 필터링
output = run_gcalcli(['agenda', '2025-10-22', '2025-10-23'])
filtered = filter_today_only(output, '2025-10-22')
```

### 문제 3: ANSI 색상 코드 파싱 오류

**증상:**
```python
# Raw output:
"[0;33m\nThu Oct 23[0m[0m         월 구독료 결제\n[0m"
```

**원인:** `--nocolor` 옵션을 사용해도 일부 ANSI 코드가 남음

**해결:**
```python
# 두 가지 ANSI 패턴 모두 제거
output_clean = re.sub(r'\x1b\[[0-9;]*m|\[[0-9;]*m', '', output)

# 결과:
# "\nThu Oct 23         월 구독료 결제\n"
```

### 문제 4: 시간 파싱 실패

**증상:**
```
- **종일** 16:00          록담 미팅  # 시간이 있는데 종일로 표시
```

**원인:** 기존 정규식이 12시간 형식(`9:00am`)만 찾고 24시간 형식(`16:00`) 못 찾음

**해결:**
```python
# Before: 12시간 형식만
time_match = re.search(r'(\d{1,2}:\d{2}[ap]m)', line, re.IGNORECASE)

# After: 24시간/12시간 모두 지원
time_match = re.match(r'^\s*(\d{1,2}:\d{2})([ap]m)?', line, re.IGNORECASE)
if time_match:
    time_str = time_match.group(1)
    ampm = time_match.group(2)
    if ampm:
        time_display = convert_to_24h(time_str + ampm)
    else:
        time_display = time_str  # 이미 24시간 형식
```

### 문제 5: 날짜 헤더와 일정 분리

**증상:**
```
"Thu Oct 23         월 구독료 결제"  # 한 줄에 날짜와 일정
```

**원인:** gcalcli가 첫 일정을 날짜 헤더와 같은 줄에 출력

**해결:**
```python
if today_formatted in line:
    include_line = True
    # 날짜 부분 제거하고 일정만 추출
    event_part = line.replace(today_formatted, '').strip()
    if event_part:
        today_lines.append('         ' + event_part)  # 공백 추가
    continue
```

---

## 최종 결과

### 완성된 파일 구조

```
~/.claude/skills/google-calendar/
├── SKILL.md                    # Skill 정의 (6KB)
├── SETUP_GUIDE.md              # 설정 안내 (4KB)
└── CASE_STUDY.md               # 이 문서

skills/google-calendar/scripts/
├── README.md                   # 사용 가이드 (gcalcli 기반)
├── get_events.py               # 오늘 일정 (180줄)
├── get_week_events.py          # 주간 일정 (150줄)
├── search_events.py            # 검색 (110줄)
├── add_event.py                # 일정 등록
└── credentials.json            # OAuth 인증 정보
```

### 기능 검증

**1. 오늘 일정 조회:**
```bash
$ python3 get_events.py
일정이 없습니다.  # 2025-10-22
```

**2. 이번 주 일정 조회:**
```bash
$ python3 get_week_events.py

## 이번 주 일정

### Mon Oct 20
- **16:00** 파트너 미팅

### Tue Oct 21
- **종일** 기념일
- **10:00** 팀 회의
- **14:00** 은행 방문

### Fri Oct 24
- **19:30** AI 워크숍

### Sat Oct 25
- **10:00** AI 스터디
- **14:00** 프로젝트 미팅
```

**3. Claude와 대화:**
```
사용자: "오늘 일정 뭐 있어?"
Claude: (google-calendar skill 자동 실행)
        일정이 없습니다.

사용자: "이번 주 스케줄 알려줘"
Claude: (google-calendar skill 자동 실행)
        ## 이번 주 일정
        ### Mon Oct 20
        - **16:00** 파트너 미팅
        ...
```

### 성능 지표

| 항목 | 결과 |
|-----|------|
| **총 소요 시간** | 2시간 |
| **코드 라인** | ~440줄 (3개 스크립트) |
| **파일 개수** | 10개 (스크립트 + 문서) |
| **캘린더 필터링** | 3개 (업무, 개인, 재무) |
| **지원 형식** | 시간 일정, 종일 일정 |
| **출력 형식** | Markdown (PKM 최적화) |

---

## 교훈

### 1. 기술 선택의 중요성

**gcalcli를 선택한 것이 핵심 성공 요인:**
- ✅ 기능 풍부 (검색/수정/삭제/뷰)
- ✅ 커뮤니티 지원 (버그 수정, 업데이트)
- ✅ 설치 간편 (pipx)
- ✅ OAuth 인증 자동화

만약 Python API를 직접 사용했다면:
- ❌ 모든 기능을 직접 구현 (2배 이상 시간 소요)
- ❌ OAuth 토큰 관리 직접
- ❌ API 변경사항 직접 대응

**결론:** 성숙한 도구를 활용하고, 필요한 부분만 래퍼로 감싸는 하이브리드 접근이 효율적

### 2. 파싱 로직의 복잡성

**간과했던 부분:**
- ANSI 색상 코드 (2가지 패턴: `\x1b[...]m`, `[...]m`)
- 날짜 헤더와 일정이 한 줄에
- 24시간 vs 12시간 형식
- 종일 일정의 gcalcli 버그

**교훈:**
1. **실제 데이터로 테스트**: 예상치 못한 엣지 케이스 발견
2. **점진적 개선**: 한 번에 완벽하게 만들려 하지 말고 반복 개선
3. **디버깅 스크립트**: 중간 출력을 확인하는 테스트 스크립트 작성

### 3. Skills 시스템의 강력함

**Claude Code Skills의 장점:**
1. **Model-invoked**: 사용자가 자연어로만 요청해도 자동 실행
2. **문서화 = 코드**: SKILL.md에 모든 것이 정의됨
3. **유연성**: Bash, Python, 모든 도구 활용 가능

**효과적인 Skill 작성:**
- ✅ `description`에 구체적인 Trigger 키워드 명시
- ✅ 사용 시나리오를 상세하게 나열
- ✅ 스크립트 경로는 절대 경로 사용
- ✅ 에러 메시지에 해결 방법 포함

### 4. 문서화의 가치

**작성한 문서:**
1. `SKILL.md` - Claude가 참조할 실행 가이드
2. `SETUP_GUIDE.md` - 사용자용 설정 안내
3. `README.md` - 스크립트 사용법
4. `CASE_STUDY.md` - 전체 과정 기록 (이 문서)

**효과:**
- 미래의 나 또는 다른 사람이 쉽게 이해 가능
- 유사한 프로젝트 진행 시 참고 자료
- 문제 발생 시 빠른 디버깅

### 5. 반복적 문제 해결

**문제 해결 패턴:**
1. **증상 확인** → 실제 출력 확인
2. **원인 분석** → 디버깅 스크립트 작성
3. **해결책 구현** → 코드 수정
4. **검증** → 다양한 케이스 테스트
5. **문서화** → 해결 과정 기록

**예시 - ANSI 코드 문제:**
1. 증상: 파싱 실패
2. 원인: `[0m`, `\x1b[0;33m` 혼재
3. 해결: 두 패턴 모두 제거하는 정규식
4. 검증: 여러 날짜 일정 테스트
5. 문서화: CASE_STUDY에 기록

---

## 다음 단계

### 추가 가능한 기능

1. **일정 수정/삭제**:
   ```python
   # edit_event.py
   # delete_event.py
   ```

2. **월간 일정 조회**:
   ```python
   # get_month_events.py
   gcalcli agenda "1 month"
   ```

3. **미팅록 자동 생성**:
   ```python
   # Calendar 이벤트 → 프로젝트 미팅록 자동 링크
   ```

4. **시간 통계**:
   ```python
   # 이번 달 프로젝트별 미팅 시간 집계
   ```

### 개선 아이디어

1. **캘린더 설정 외부화**:
   ```yaml
   # calendar_config.yaml
   calendars:
     - Work
     - 개인
     - 재무
   ```

2. **캐싱**:
   ```python
   # 당일 조회 결과 캐싱 (성능 개선)
   ```

3. **에러 알림**:
   ```python
   # OAuth 만료 시 자동 알림
   ```

---

## 참고 자료

### 공식 문서
- **Claude Code Skills**: https://docs.claude.com/en/docs/claude-code/skills
- **gcalcli GitHub**: https://github.com/insanum/gcalcli
- **Google Calendar API**: https://developers.google.com/calendar

### 내부 문서
- **Skills README**: `.claude/skills/README.md`
- **CLAUDE.md**: `.claude/CLAUDE.md`
- **PKM 구조**: `pkm/README.md`

---

## 결론

Google Calendar Skill 생성 프로젝트는 **Claude Code Skills 시스템의 강력함과 유연성**을 보여주는 좋은 사례입니다.

**핵심 성공 요인:**
1. ✅ 기존 도구 활용 (gcalcli)
2. ✅ 하이브리드 아키텍처 (gcalcli + Python 래퍼)
3. ✅ 점진적 개선 (반복적 문제 해결)
4. ✅ 철저한 문서화

**최종 결과:**
- 자연어로 "오늘 일정 뭐 있어?"만 입력하면 자동으로 Google Calendar 조회
- Daily Note, Weekly Review에 일정 자동 통합
- 확장 가능한 구조로 향후 기능 추가 용이

**소요 시간:** 2시간
**가치:** PKM 시스템과 Google Calendar의 완벽한 통합 🎉

---

**작성:** 2025년 10월 22일
**작성자:** Claude Code
**버전:** 1.0
