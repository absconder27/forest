---
description: 텔레그램으로 Daily Briefing 전송
allowed-tools: Read, Bash, Edit
---

오늘의 Daily Briefing을 텔레그램으로 전송해주세요.

**수행할 작업:**

1. 오늘 날짜 확인 (YYYY-MM-DD, 요일)

2. GWS 데이터 가져오기:
   - `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/gws/gws_daily_fetch.py --date YYYY-MM-DD --workspace-root .` 실행
   - stdout에서 `===SECTION===` 구분자로 각 섹션 파싱:
     - `===SCHEDULE_TABLE===` → 오늘 일정
     - `===UPCOMING_EVENTS===` → 향후 일정
     - `===GMAIL_SUMMARY===` → 메일 요약
     - `===TOP3_TASKS===` → 우선순위
   - 실패 시 각 섹션을 "(데이터 없음)"으로 대체

3. 미완료 할일 읽기:
   - `pkm/40-personal/43-todos/active-todos.md`에서 Inbox 섹션의 `- [ ]` 항목 수집

4. 텔레그램 메시지 포맷 조합:
   ```
   *YYYY-MM-DD (요일) Daily Briefing*

   *오늘의 우선순위*
   (top3_tasks - 체크박스를 불릿으로 변환)

   *일정*
   (schedule_table - 테이블 형식을 불릿 리스트로 변환)

   *확인할 메일*
   (gmail_summary)

   *향후 일정*
   (upcoming_events)

   *미완료 할일 (N건)*
   (active-todos.md Inbox 항목)
   ```
   - Telegram Markdown 규칙: `*bold*`, `_italic_`
   - 특수문자(`*`, `_`, `` ` ``) 이스케이프 불필요 (레거시 Markdown 모드)
   - 빈 섹션은 "- (없음)" 표시

5. 전송:
   - `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/telegram/telegram_api.py send "조합된 메시지"`
   - 전송 결과 확인 후 사용자에게 보고

**주의사항:**
- GWS venv의 python을 사용 (requests 포함)
- 메시지가 4096자 초과 시 telegram_api.py가 자동 분할 처리
- Markdown 파싱 실패 시 plain text로 자동 재시도
