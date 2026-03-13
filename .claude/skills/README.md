# Skills

> Claude Code와 외부 서비스를 통합하는 기능 모음

## 사용 가능한 Skills

### Web Crawler + OCR (Firecrawl + Gemini)

**상태**: 설정 가이드 완료

웹페이지 크롤링 + 이미지 OCR을 자동으로 처리:
- "https://competitor-cafe.com 분석해줘"
- "이 페이지 크롤링해줘"
- "경쟁사 웹사이트 분석"
- "대용량 이미지 OCR 필요해"

**설정 방법**: [web-crawler-ocr/SETUP_GUIDE.md](./web-crawler-ocr/SETUP_GUIDE.md) (10분 소요)

**특징**:
- Firecrawl로 깨끗한 텍스트 추출 (광고/잡음 제거)
- Gemini OCR로 대용량 이미지 처리 (20MB, Claude 5MB 제한 우회)
- 완전한 마크다운 생성 (텍스트 + 이미지 분석)
- URL 자동 감지 및 실행

**시작하기**:
```bash
# 1. 수동 설정
cd skills/web-crawler-ocr/scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. API 키 설정 (.env 파일)
GEMINI_API_KEY=your_gemini_key
FIRECRAWL_API_KEY=your_firecrawl_key

# 4. Claude와 대화
"https://example.com 분석해줘"
```

자세한 내용: [web-crawler-ocr/README.md](./web-crawler-ocr/README.md)

### Transcript Organizer

녹음 텍스트 파일(강의, 미팅, 인터뷰)을 자동으로 분석 및 구조화:
- "강의 정리해줘", "미팅록 정리", "인터뷰 정리"
- 인코딩 자동 감지(UTF-16 -> UTF-8), STT 오인식 교정
- 유형별 템플릿 적용 (강의/미팅/인터뷰)

### Dashboard PRD Generator

대시보드 PRD를 대화형으로 생성:
- "대시보드 PRD", "대시보드 기획"
- 결정 우선(Decision-First) 원칙 기반 설계
- 4단계 대화형 프로세스 (의사결정 -> 데이터 -> 화면 -> 기술)

### Excel to CSV Converter

Excel 파일을 Claude Code에서 분석 가능한 CSV로 변환:
- "엑셀 변환", "xlsx 변환", .xlsx 파일 경로 제공 시 자동 실행
- 멀티 시트 지원, EUC-KR 인코딩 변환

---

## Skills란?

Skills는 Claude Code를 외부 서비스와 연결하여 확장하는 기능입니다.

### Skills vs Commands

| 구분 | Skills | Commands |
|------|--------|----------|
| **목적** | 외부 서비스 통합 | 내부 워크플로우 자동화 |
| **예시** | Web Crawler, Notion | `/daily-note`, `/setup-workspace` |
| **위치** | `skills/` | `.claude/commands/` |
| **설정** | OAuth, API 키 필요 | 설정 불필요 (즉시 사용) |

---

## 추가 가능한 Skills 예시

**생산성:**
- **Notion** - Notion 페이지 생성/조회
- **Todoist** - 할 일 관리
- **Google Calendar** - 일정 관리

**커뮤니케이션:**
- **Slack** - 메시지 전송/채널 조회
- **Discord** - 봇 통합

**개발:**
- **GitHub** - 이슈/PR 관리

**데이터:**
- **Airtable** - 데이터베이스 조회/수정
- **Google Sheets** - 스프레드시트 읽기/쓰기

---

## 커스텀 Skills 추가

자신만의 스킬을 추가하려면:

### 1. 폴더 생성
```bash
mkdir -p skills/skill-name/scripts
```

### 2. SKILL.md 작성
```markdown
---
name: skill-name
description: 스킬 설명 및 트리거 키워드
allowed-tools: Bash, Read
---

# Skill Name

## 사용 방법
...
```

### 3. 스크립트 작성 (선택)
```bash
# skills/skill-name/scripts/main.py
# 실제 기능 구현
```

### 4. README 작성
```markdown
# Skill Name

## 설정 가이드
...
```

### 참고 자료
- **예시**: [web-crawler-ocr/](./web-crawler-ocr/) 폴더 구조 참고
- **공식 문서**: [Claude Code Skills 가이드](https://docs.claude.com)

---

## Skills 사용 팁

### 자동 트리거

Skills는 대화 중 키워드를 감지하면 자동으로 실행됩니다:
```
사용자: "이 URL 분석해줘"
-> web-crawler-ocr skill 자동 실행
```

### 명시적 호출

특정 skill을 명시적으로 호출할 수도 있습니다:
```
사용자: "web-crawler-ocr skill로 이 페이지 크롤링해줘"
```

### PKM 통합

Skills를 `/daily-note`, `/weekly-review` 등의 commands와 결합하여 자동화할 수 있습니다.

---

## 선택적 기능

Skills는 **선택적**입니다. 필요한 기능만 설정하세요.

- **web-crawler-ocr**: 웹 리서치, 경쟁사 분석이 필요한 경우
- **transcript-organizer**: 녹음 파일 구조화가 필요한 경우
- **dashboard-prd**: 대시보드 기획이 필요한 경우
- **excel-to-csv**: Excel 데이터 분석이 필요한 경우
