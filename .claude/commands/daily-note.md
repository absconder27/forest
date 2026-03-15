---
description: 오늘 날짜의 Daily Note 생성 또는 열기 (GWS 연동)
allowed-tools: Read, Write, Edit, Bash
---

오늘 날짜의 Daily Note를 생성하거나 열어주세요.

**수행할 작업:**

1. 오늘 날짜 확인 (YYYY-MM-DD 형식)
2. 경로:
   - 파일 경로: `./40-personal/41-daily/YYYY/MM/YYYY-MM-DD.md`
   - 폴더가 없으면 자동 생성 (`mkdir -p`)
3. 파일이 없으면:
   - **GWS 데이터 가져오기**:
     - `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/gws/gws_daily_fetch.py --date YYYY-MM-DD --workspace-root .` 실행
     - stdout에서 `===SECTION===` 구분자로 각 섹션 파싱:
       - `===SCHEDULE_TABLE===` → `{{schedule_table}}`
       - `===UPCOMING_EVENTS===` → `{{upcoming_events}}`
       - `===GMAIL_SUMMARY===` → `{{gmail_summary}}`
       - `===TOP3_TASKS===` → `{{top3_tasks}}`
     - **Fallback** (스크립트 실행 실패 또는 exit code != 0):
       - `{{schedule_table}}` → `| | | |`
       - `{{upcoming_events}}` → `- (일정 없음)`
       - `{{gmail_summary}}` → `- (메일 확인 필요)`
       - `{{top3_tasks}}` → `- [ ]\n- [ ]\n- [ ]`
   - **텔레그램 Inbox 가져오기**:
     - `python3 ./00-system/02-scripts/telegram/telegram_api.py fetch` 실행
     - stdout JSON 파싱 → 각 메시지의 `category` 필드 기준 마크다운 변환:
       - `("todo", text)` → `- [ ] {text}`
       - `("link", text)` → `- [ ] [링크] {text}`
       - `("note", text)` → `- 메모: {text}`
     - `{{telegram_inbox}}` 변수에 할당 (메시지 없으면 `- (새 메시지 없음)`)
     - **동시 작업**: 가져온 todo/link 항목을 `./40-personal/46-todos/active-todos.md`의 `## 📥 Inbox` 섹션에도 추가 (중복 방지)
     - **Fallback** (환경변수 미설정 또는 실행 실패): `{{telegram_inbox}}` → `- (텔레그램 미연결)`
   - 템플릿 읽기:
     - `./00-system/01-templates/daily-note-template.md`
   - 변수 치환:
     - `{{date}}`: 2025-10-20
     - `{{weekday}}`: 일요일
     - `{{yesterday}}`: 2025-10-19
     - `{{tomorrow}}`: 2025-10-21
     - `{{yesterday_path}}`: 40-personal/41-daily/2025/10/2025-10-19
     - `{{tomorrow_path}}`: 40-personal/41-daily/2025/10/2025-10-21
     - `{{week}}`: 2025-W42
     - `{{schedule_table}}`: GWS에서 가져온 일정 테이블
     - `{{upcoming_events}}`: 향후 2-3일 일정
     - `{{gmail_summary}}`: 메일 요약
     - `{{top3_tasks}}`: 어제 설정한 우선순위
     - `{{telegram_inbox}}`: 텔레그램 새 메시지 (todo/link/note)
   - 새 파일 생성
4. 파일이 있으면:
   - 현재 내용 표시
