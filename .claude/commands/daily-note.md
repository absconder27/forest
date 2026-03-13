---
description: 오늘 날짜의 Daily Note 생성 또는 열기 (Google Calendar 일정 포함)
allowed-tools: Read, Write, Edit, Bash
---

오늘 날짜의 Daily Note를 생성하거나 열어주세요. **Google Calendar 일정과 알림을 함께 가져옵니다.**

**수행할 작업:**

1. 오늘 날짜 확인 (YYYY-MM-DD 형식)
2. 경로:
   - 파일 경로: `./40-personal/41-daily/YYYY-MM-DD.md`
3. 파일이 없으면:
   - 템플릿 읽기:
     - `./00-system/01-templates/daily-note-template.md`
   - **Google Calendar에서 오늘 일정 가져오기 (gcalcli 사용):**
     ```bash
     # 일정 캘린더 조회 (gcalcli list로 확인된 캘린더 사용)
     gcalcli agenda --tsv

     # 알림 캘린더 조회 (별도 알림용 캘린더가 있으면)
     # gcalcli agenda --calendar "알림캘린더명" --tsv
     ```
   - 변수 치환:
     - `{{date}}`: 2025-10-20
     - `{{weekday}}`: 일요일
     - `{{yesterday}}`: 2025-10-19
     - `{{tomorrow}}`: 2025-10-21
     - `{{week}}`: 2025-W42
     - `{{calendar_events}}`: gcalcli로 가져온 일정을 Markdown 리스트로 변환
     - `{{money_alerts}}`: 알림 캘린더 일정을 Markdown 리스트로 변환 (설정된 경우)
   - 새 파일 생성
4. 파일이 있으면:
   - 현재 내용 표시
   - Google Calendar 일정을 확인하고 업데이트 여부 물어보기

**Google Calendar 통합 (gcalcli):**
- `gcalcli agenda --calendar "캘린더명" --tsv` 명령어 사용
- **일정 캘린더**: gcalcli list로 확인된 캘린더 → "Google Calendar (일정)" 섹션
  - TSV 출력을 Markdown 리스트로 변환: `- **HH:MM-HH:MM**: 일정 제목`
- **알림 캘린더**: 별도 알림용 캘린더 (설정된 경우) → "알림" 섹션
  - TSV 출력을 Markdown 리스트로 변환
- 일정이 없으면 "일정이 없습니다." 표시
- **gcalcli 설치 확인**: `which gcalcli`로 먼저 확인
