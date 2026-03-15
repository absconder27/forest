---
description: 텔레그램에서 새 메시지를 가져와 Inbox에 추가
allowed-tools: Read, Write, Edit, Bash
---

텔레그램에서 새 메시지를 가져와서 Todo Inbox에 추가해주세요.

**수행할 작업:**

1. 새 메시지 가져오기:
   - `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/telegram/telegram_api.py fetch` 실행
   - JSON 배열 파싱 (각 메시지에 text, date, category 포함)

2. 메시지가 없으면:
   - "새 메시지가 없습니다." 출력 후 종료

3. 각 메시지 분류 (category 필드 활용):
   | category | 저장 형식 |
   |----------|----------|
   | `["todo", "내용"]` | `- [ ] 내용` |
   | `["link", "URL 포함 텍스트"]` | `- [ ] [링크] 텍스트` |
   | `["note", "메모 내용"]` | `- [ ] 메모: 내용` |

4. `pkm/40-personal/43-todos/active-todos.md`의 `## Inbox` 섹션 하단에 추가:
   - 각 항목에 메타데이터 포함:
     ```
     - [ ] 내용
       - added: YYYY-MM-DD HH:MM
       - source: telegram
     ```
   - 기존 항목 아래, `## Done` 섹션 위에 삽입

5. 처리 결과 요약 출력:
   ```
   텔레그램 Inbox 처리 완료:
   - todo: N건
   - link: N건
   - note: N건
   총 N건이 active-todos.md에 추가되었습니다.
   ```

**주의사항:**
- GWS venv의 python을 사용
- 이미 처리된 메시지는 last_update_id.txt로 추적되므로 중복 없음
- 빈 메시지나 명령어(/start 등)는 무시
